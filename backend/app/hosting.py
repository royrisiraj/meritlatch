"""Native offline hosting wrapper. Does not change business authorization."""
import hashlib
from pathlib import Path
import re
import secrets

from fastapi import Request
from fastapi.responses import Response, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware


CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; "
       "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")


def bundle_files(root: Path):
    root = root.resolve()
    files = [root / "index.html", *sorted((root / "assets").glob("*"))]
    if not (root / "index.html").is_file() or len(files) < 3:
        raise ValueError("FRONTEND_BUILD_REQUIRED")
    hashes = {}
    for path in files:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("UNSAFE_FRONTEND_BUILD")
        relative = path.relative_to(root).as_posix()
        if relative != "index.html" and not re.fullmatch(r"assets/[A-Za-z0-9_-]+\.(js|css)", relative):
            raise ValueError("UNEXPECTED_FRONTEND_ASSET")
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def mount_hosting(app, frontend_root: Path):
    settings = app.state.settings
    if settings.provider_mode not in {"DISABLED", "MOCK_AI"} or settings.allow_billable or settings.gemini_api_key:
        raise ValueError("OFFLINE_CONFIGURATION_REQUIRED")
    root = frontend_root.resolve()
    hashes = bundle_files(root)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    def read_asset(name):
        path = root / name
        if name not in hashes or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("ASSET_UNAVAILABLE")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != hashes[name]:
            raise ValueError("ASSET_CHANGED")
        return data

    def ready():
        probe = None
        try:
            # BEGIN IMMEDIATE proves a local SQLite transaction can start, not
            # disk durability or cloud readiness. No business rows are mutated.
            with app.state.service.repository.transaction() as tx:
                if not tx.get("schema_migrations", version=1):
                    return False
            media = settings.media_root
            media.mkdir(parents=True, exist_ok=True, mode=0o700)
            probe = media / (".ready-" + secrets.token_hex(16))
            with probe.open("xb") as target:
                target.write(b"ready")
            probe.unlink()
            probe = None
            for name in hashes:
                read_asset(name)
            return True
        except Exception:
            return False
        finally:
            if probe is not None:
                try:
                    probe.unlink(missing_ok=True)  # Only this probe's own file.
                except OSError:
                    pass

    app.state.local_ready = ready

    @app.middleware("http")
    async def hosting_headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = CSP
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.get("/readyz", include_in_schema=False)
    def readiness():
        ok = ready()
        return JSONResponse({"status": "ready" if ok else "not_ready"}, status_code=200 if ok else 503)

    # Offline package never loads Swagger's external CDN resources.
    app.router.routes[:] = [route for route in app.router.routes if getattr(route, "path", "") != "/docs"]

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str, request: Request):
        name = path if path.startswith("assets/") else "index.html"
        is_page = not path or path == "login" or path == "restricted" or re.fullmatch(
            r"(?:contractor|manager|engineer)(?:/[A-Za-z0-9_-]+)*", path)
        if path.startswith(("v1/", "_local/", ".", "docs", "openapi")) or (name == "index.html" and not is_page):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        try:
            data = read_asset(name)
        except Exception:
            return JSONResponse({"status": "unavailable"}, status_code=503)
        mime = "text/html" if name == "index.html" else "text/javascript" if name.endswith(".js") else "text/css"
        return Response(data, media_type=mime, headers={"Cache-Control": "no-store"})

    return app
