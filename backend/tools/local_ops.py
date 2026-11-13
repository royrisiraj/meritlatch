"""Loopback demo operations. No environment-loaded provider, downloads or PID killing."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import sqlite3
import subprocess
import sys
from threading import Timer
import time
from uuid import uuid4

import httpx
import uvicorn
from fastapi import Request

from backend.app.api import create_app
from backend.app.hosting import mount_hosting, bundle_files
from backend.app.perception import MockPerceptionProvider
from backend.app.settings import Settings
from backend.tools.portal_demo import prepare, CannedDemoObserver

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / (".venv" if (ROOT / ".venv").is_dir() else ".runtime")
LAST = BASE / "phase06-last-run.local.json"
TTL = 3600


class OpsError(Exception):
    pass


def atomic_json(path, value):
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def private_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=False)
    if os.name == "nt":
        # Set only DACL on our new directory, not owner/SACL. PowerShell Set-Acl
        # can request SeSecurityPrivilege in restricted Windows environments.
        # OWNER RIGHTS + SYSTEM inherit; no global permission/admin requirement.
        import ctypes
        from ctypes import wintypes
        security = ctypes.WinDLL("advapi32", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        descriptor, dacl = ctypes.c_void_p(), ctypes.c_void_p()
        present, defaulted = wintypes.BOOL(), wintypes.BOOL()
        security.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD)]
        security.GetSecurityDescriptorDacl.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.BOOL), ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.BOOL)]
        security.SetNamedSecurityInfoW.argtypes = [wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        security.SetNamedSecurityInfoW.restype = wintypes.DWORD
        try:
            if not security.ConvertStringSecurityDescriptorToSecurityDescriptorW("D:P(A;OICI;FA;;;OW)(A;OICI;FA;;;SY)", 1, ctypes.byref(descriptor), None):
                raise OpsError("PRIVATE_DIRECTORY_FAILED")
            if not security.GetSecurityDescriptorDacl(descriptor, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)) or not present:
                raise OpsError("PRIVATE_DIRECTORY_FAILED")
            if security.SetNamedSecurityInfoW(str(path), 1, 0x80000004, None, None, dacl, None):
                raise OpsError("PRIVATE_DIRECTORY_FAILED")
        finally:
            kernel.LocalFree.argtypes = [ctypes.c_void_p]
            kernel.LocalFree(descriptor)


def child_environment():
    env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR", "PATH", "PATHEXT", "COMSPEC") if k in os.environ}
    env.update(PYTHONUTF8="1", PYTHONUNBUFFERED="1", SENTINEL_PROVIDER_MODE="DISABLED", SENTINEL_ALLOW_BILLABLE="false",
               TEMP=str(BASE), TMP=str(BASE), TMPDIR=str(BASE))
    return env


def owned_root(value):
    path = Path(value).absolute()
    resolved = path.resolve()
    if path != resolved or not resolved.is_relative_to(BASE.resolve()) or not resolved.name.startswith("phase06-demo-"):
        raise OpsError("ISOLATED_ROOT_REQUIRED")
    return resolved


@contextmanager
def lease(root):
    file = (root / "operator.lock").open("a+b")
    try:
        file.seek(0)
        if os.name == "nt":
            import msvcrt
            if not file.read(1):
                file.write(b"0")
                file.flush()
            file.seek(0)
            msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        file.close()
        raise OpsError("DEMO_ALREADY_RUNNING") from None
    try:
        yield
    finally:
        file.close()  # OS releases lease even after a crash; no stale PID kill.


def record(root):
    path = owned_root(root)
    if (path / "runtime.local.json").is_symlink():
        raise OpsError("INVALID_DEMO_RECORD")
    data = json.loads((path / "runtime.local.json").read_text(encoding="utf-8"))
    if data.get("owner") != "SENTINEL_PHASE06" or data.get("root") != str(path) or not isinstance(data.get("port"), int) or not 1024 <= data["port"] <= 65535:
        raise OpsError("INVALID_DEMO_RECORD")
    return data


def preflight(port=8018):
    bundle = bundle_files(ROOT / "frontend/dist")
    versions = {name: importlib.metadata.version(name) for name in ("fastapi", "uvicorn", "SQLAlchemy", "pillow")}
    if not isinstance(port, int) or port != 0 and not 1024 <= port <= 65535:
        raise OpsError("INVALID_LOOPBACK_PORT")
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            raise OpsError("PORT_IN_USE") from None
        selected = probe.getsockname()[1]
    return {"status": "preflight_passed", "port": selected, "assets": len(bundle), "dependencies": versions}


def control(root, stop=False):
    info = record(root)
    try:
        with httpx.Client(trust_env=False, timeout=2) as client:
            response = client.request("POST" if stop else "GET", f"http://127.0.0.1:{info['port']}/_local/control",
                                      headers={"X-Operator-Token": info["control_token"], "X-Operator-Instance": info["instance_id"]})
    except httpx.TransportError:
        return {"status": "STOPPED" if info.get("status") == "STOPPED" else "UNAVAILABLE", "instance_id": info["instance_id"]}
    if response.status_code != 200 or response.json().get("instance_id") != info["instance_id"]:
        raise OpsError("INSTANCE_IDENTITY_MISMATCH")
    return response.json()


def start(root=None, port=8018, fixture="normal-unknown", acknowledge=False, resume=False):
    if fixture not in {"normal-unknown", "unsafe-then-valid"} or fixture != "normal-unknown" and not acknowledge:
        raise OpsError("CANNED_ACKNOWLEDGEMENT_REQUIRED")
    checked = preflight(port)
    BASE.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = owned_root(root or BASE / ("phase06-demo-" + uuid4().hex))
    if resume:
        previous = record(path)
        if previous["expires_at"] <= time.time():
            raise OpsError("DEMO_EXPIRED_CREATE_FRESH_ROOT")
        if previous["fixture"] != fixture or not (path / "data/demo.sqlite").is_file():
            raise OpsError("DEMO_RESUME_MISMATCH")
    else:
        private_directory(path)  # Never overwrite an existing run directory.
        previous = {}
    with lease(path):
        if resume and previous.get("status") == "STARTING" and time.time()-previous.get("start_requested_at", 0) < 45:
            raise OpsError("DEMO_START_IN_PROGRESS")
        info = dict(owner="SENTINEL_PHASE06", root=str(path), port=checked["port"], fixture=fixture,
                    instance_id=uuid4().hex, control_token=secrets.token_urlsafe(32), status="STARTING",
                    created_at=previous.get("created_at", time.time()), expires_at=previous.get("expires_at", time.time()+TTL),
                    resume=resume, start_requested_at=time.time())
        atomic_json(path / "runtime.local.json", info)
        with (path / "service.log").open("ab") as log:
            child = subprocess.Popen([sys.executable, "-m", "backend.tools.local_ops", "serve", "--root", str(path)],
                cwd=ROOT, env=child_environment(), stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    began = time.monotonic()
    try:
        while time.monotonic()-began < 35:
            if child.poll() is not None:
                raise OpsError("LOCAL_START_FAILED")
            try:
                value = control(path)
                if value.get("status") == "READY":
                    atomic_json(LAST, {"root": str(path)})
                    return {"status": "READY", "url": f"http://127.0.0.1:{info['port']}", "run_root": str(path),
                            "fixture": fixture, "startup_seconds": time.monotonic()-began, "expires_at": info["expires_at"]}
            except (httpx.HTTPError, ValueError, OpsError):
                pass
            time.sleep(0.1)
        raise OpsError("LOCAL_READINESS_TIMEOUT")
    except BaseException:
        if child.poll() is None:
            child.terminate()  # Only the child handle created by this exact call.
            child.wait(timeout=10)
        raise


def serve(root):
    path = owned_root(root)
    with lease(path):
        info = record(path)
        data = path / "data"
        if info["expires_at"] <= time.time():
            raise OpsError("DEMO_EXPIRED_CREATE_FRESH_ROOT")
        if info["resume"]:
            provider = CannedDemoObserver() if info["fixture"] == "unsafe-then-valid" else MockPerceptionProvider()
            app = create_app(Settings(database_path=data / "demo.sqlite", environment="test", provider_mode="MOCK_AI",
                media_root=data / "media", challenge_seconds=600), perception_provider=provider)
            if isinstance(provider, CannedDemoObserver):
                provider.repository = app.state.service.repository
        else:
            app = prepare(data, info["fixture"])  # Reuse the accepted Phase 05 harness.
        # Add operator control before catch-all hosting route. No application
        # credentials, approval/permission action or fixture injection is exposed.
        server = None

        @app.api_route("/_local/control", methods=["GET", "POST"], include_in_schema=False)
        def operator(request: Request):
            supplied = request.headers.get("X-Operator-Token", "")
            if request.client.host != "127.0.0.1" or not secrets.compare_digest(supplied, info["control_token"]) or request.headers.get("X-Operator-Instance") != info["instance_id"]:
                from fastapi.responses import JSONResponse
                return JSONResponse({"status": "DENIED"}, status_code=403)
            if request.method == "POST":
                server.should_exit = True
                return {"status": "STOPPING", "instance_id": info["instance_id"]}
            return {"status": "READY" if app.state.local_ready() else "NOT_READY", "instance_id": info["instance_id"]}

        mount_hosting(app, ROOT / "frontend/dist")
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=info["port"], workers=1,
            proxy_headers=False, access_log=False, log_level="critical", timeout_graceful_shutdown=30))
        info.update(status="RUNNING", pid=os.getpid())
        atomic_json(path / "runtime.local.json", info)
        timer = Timer(max(0, info["expires_at"]-time.time()), lambda: setattr(server, "should_exit", True))
        timer.daemon = True
        timer.start()
        try:
            server.run()
        finally:
            timer.cancel()
            app.state.service.repository.close()
            info.update(status="STOPPED", stopped_at=time.time())
            atomic_json(path / "runtime.local.json", info)


def stop(root):
    result = control(root, stop=True)
    if result["status"] in {"UNAVAILABLE", "STOPPED"}:
        return result
    began = time.monotonic()
    while time.monotonic()-began < 35:
        if record(root).get("status") == "STOPPED":
            return {"status": "STOPPED", "shutdown_seconds": time.monotonic()-began}
        time.sleep(0.1)
    raise OpsError("GRACEFUL_STOP_PENDING_NO_FORCE_KILL")


def backup(root):
    path = owned_root(root)
    with lease(path):
        if record(path).get("status") != "STOPPED":
            raise OpsError("STOP_BEFORE_BACKUP")
        data = path / "data"
        database = data / "demo.sqlite"
        if not database.is_file() or database.is_symlink():
            raise OpsError("BACKUP_SOURCE_REQUIRED")
        files = [p for p in data.rglob("*") if p.is_file()]
        if any(p.is_symlink() or not p.resolve().is_relative_to(data) for p in data.rglob("*")):
            raise OpsError("UNSAFE_BACKUP_SOURCE")
        # Read-only source: missing/corrupt state cannot silently create an empty DB.
        with sqlite3.connect(database.as_uri()+"?mode=ro", uri=True) as source:
            if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise OpsError("BACKUP_INTEGRITY_FAILED")
            from backend.app.media_storage import LocalPrivateMediaStorage
            storage = LocalPrivateMediaStorage(data / "media")
            for key, expected in source.execute("SELECT storage_key,sha256 FROM media_uploads"):
                if hashlib.sha256(storage.read(key,10*1024*1024)).hexdigest() != expected:
                    raise OpsError("BACKUP_MEDIA_MISMATCH")
        target = BASE / ("phase06-backup-" + uuid4().hex)
        private_directory(target)
        with sqlite3.connect(database.as_uri()+"?mode=ro", uri=True) as source, sqlite3.connect(target / "demo.sqlite") as destination:
            source.backup(destination)
            if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise OpsError("BACKUP_INTEGRITY_FAILED")
        for file in files:
            if file.name.startswith("demo.sqlite"):
                continue
            out = target / file.relative_to(data)
            out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copyfile(file, out)
        atomic_json(target / "backup.local.json", {"source_root": str(path), "created_at":time.time(),
            "classification":"PRIVATE_DEMO_BACKUP", "sqlite_integrity":"ok"})
        return {"status": "BACKUP_COMPLETE", "backup_root": str(target)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["preflight", "start", "serve", "status", "stop", "backup"])
    parser.add_argument("--root", type=Path)
    parser.add_argument("--port", type=int, default=8018)
    parser.add_argument("--fixture", choices=["normal-unknown", "unsafe-then-valid"], default="normal-unknown")
    parser.add_argument("--acknowledge-canned", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        root = args.root
        if args.action in {"status", "stop", "backup"} and root is None:
            root = Path(json.loads(LAST.read_text(encoding="utf-8"))["root"])
        if args.action == "preflight":
            result = preflight(args.port)
        elif args.action == "start":
            result = start(root, args.port, args.fixture, args.acknowledge_canned, args.resume)
        elif args.action == "serve":
            serve(root)
            return
        elif args.action == "status":
            result = control(root)
        elif args.action == "stop":
            result = stop(root)
        else:
            result = backup(root)
        print(json.dumps(result), flush=True)
    except Exception as error:
        code = str(error) if isinstance(error, OpsError) else "LOCAL_OPERATION_FAILED"
        print(json.dumps({"status":"FAILED", "reason_codes":[code],
                          "guidance":"Check local dependencies, isolated path, ports and saved run state; no automatic reset or download."}), flush=True)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
