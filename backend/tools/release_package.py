"""Deterministic allowlisted native package, not a cloud/container deployment."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import zipfile

from backend.app.hosting import bundle_files

ROOT = Path(__file__).resolve().parents[2]
MODULES = "__init__ api api_models assurance_corpus assurance_executor assurance_models assurance_router assurance_schema assurance_scoring assurance_service assurance_worker auth case_service config errors gemini_provider hosting http_limits main media media_service media_state media_storage models perception policy portal_router provisioning repository settings workflow_models workflow_service".split()
STATIC = {"backend/__init__.py", "backend/tools/__init__.py", "backend/tools/portal_demo.py",
          "backend/tools/local_ops.py", "backend/tools/release_package.py", "backend/requirements.txt", "scripts/Demo.ps1",
          "policies/maintenance_v1.json", "fixtures/security/scenarios_v1.json", "fixtures/security/labels_v1.json",
          "fixtures/security/manifest_v1.json", "frontend/dist/index.html"} | {
          f"backend/app/{name}.py" for name in MODULES} | {
          f"docs/{name}_phase06.md" for name in ("deployment_decision", "demo_runbook", "pitch", "operations", "security_deployment_review")}


def permitted(name):
    return name in STATIC or name.startswith("frontend/dist/assets/") and __import__("re").fullmatch(
        r"frontend/dist/assets/[A-Za-z0-9_-]+\.(js|css)", name) is not None


def build(output: Path, source=ROOT):
    source = source.resolve()
    names = STATIC | {"frontend/dist/"+name for name in bundle_files(source / "frontend/dist")}
    payload = {}
    for name in sorted(names):
        file = source / name
        if not file.is_file() or any(p.is_symlink() for p in (file, *file.parents)) or not file.resolve().is_relative_to(source):
            raise ValueError("RELEASE_INPUT_MISSING_OR_UNSAFE")
        data = file.read_bytes()
        if len(data) > 2*1024*1024:
            raise ValueError("RELEASE_INPUT_TOO_LARGE")
        payload[name] = data
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        commit = "SOURCE_EXPORT"
    manifest = dict(schema=1, base_commit=commit, worktree_packaged=True,
        classification="NATIVE_OFFLINE_PACKAGE_NOT_DEPLOYED", dependencies="EXTERNAL_EXISTING_PYTHON_ENVIRONMENT_REQUIRED",
        files={name:hashlib.sha256(data).hexdigest() for name,data in payload.items()})
    payload["RELEASE_MANIFEST.json"] = (json.dumps(manifest, sort_keys=True, indent=2)+"\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream, zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            entry = zipfile.ZipInfo(name, date_time=(2020,1,1,0,0,0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return verify(output)


def verify(package: Path):
    if package.stat().st_size > 16*1024*1024:
        raise ValueError("PACKAGE_TOO_LARGE")
    with zipfile.ZipFile(package) as archive:
        entries = archive.infolist()
        names = [e.filename for e in entries]
        if len(names) > 128 or len(set(names)) != len(names) or sum(e.file_size for e in entries) > 32*1024*1024:
            raise ValueError("PACKAGE_LIMIT_EXCEEDED")
        for entry in entries:
            name = entry.filename
            if name != str(PurePosixPath(name)) or ".." in PurePosixPath(name).parts or "\\" in name or name.startswith("/") or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("UNSAFE_PACKAGE_PATH")
            if name != "RELEASE_MANIFEST.json" and not permitted(name):
                raise ValueError("UNAPPROVED_PACKAGE_FILE")
        manifest = json.loads(archive.read("RELEASE_MANIFEST.json"))
        hashes = manifest["files"]
        if manifest["schema"] != 1 or set(names) != set(hashes) | {"RELEASE_MANIFEST.json"} or not STATIC <= set(hashes):
            raise ValueError("PACKAGE_MANIFEST_MISMATCH")
        for name, expected in hashes.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError("PACKAGE_DIGEST_MISMATCH")
    return {"status":"PACKAGE_VERIFIED", "files":len(names), "bytes":package.stat().st_size,
            "sha256":hashlib.sha256(package.read_bytes()).hexdigest(), "base_commit":manifest["base_commit"],
            "remote_deployment":"NOT_ATTEMPTED"}


def extract(package: Path, destination: Path):
    result = verify(package)
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    base = destination.resolve()
    with zipfile.ZipFile(package) as archive:
        for entry in archive.infolist():
            target = base / entry.filename
            if not target.resolve().is_relative_to(base):
                raise ValueError("UNSAFE_PACKAGE_PATH")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                output.write(archive.read(entry))
    return result | {"extracted_root":str(base)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build","verify","extract"])
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    try:
        result = build(args.package) if args.action == "build" else extract(args.package,args.destination) if args.action == "extract" and args.destination else verify(args.package)
        print(json.dumps(result))
    except Exception:
        print(json.dumps({"status":"FAILED","reason_codes":["PACKAGE_CHECK_FAILED"],
                          "guidance":"Build frontend, check allowlisted inputs and use a fresh output/destination."}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
