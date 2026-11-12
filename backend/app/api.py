"""Phase 01 application factory. No synthetic intake or policy-publishing route."""

from contextlib import asynccontextmanager
import asyncio
from pathlib import Path
import re

from fastapi import FastAPI, Depends, Request, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .api_models import Login, JobCreate, CaseCreate, ChallengeRequest, ActionRequest, Versioned, InvoiceChange, PolicyChange, AssignmentChange
from .case_service import CaseService
from .config import load_policy
from .errors import AppError
from .main import healthz, Health
from .http_limits import BoundedBody
from .repository import SQLiteRepository
from .settings import Settings
from .media_service import MediaService
from .media_storage import LocalPrivateMediaStorage
from .perception import MockPerceptionProvider

bearer = HTTPBearer(auto_error=False)


def bearer_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials or credentials.scheme.lower() != "bearer" or not re.fullmatch(r"[A-Za-z0-9_-]{43}", credentials.credentials):
        raise AppError(401, "AUTHENTICATION_REQUIRED", "Log in and provide your bearer token in the Authorization header.")
    return credentials.credentials


def create_app(settings: Settings | None = None, repository=None, clock=None, perception_provider=None, media_storage=None):
    settings = settings or Settings.from_env()
    owned = repository is None
    repository = repository or SQLiteRepository(settings.database_path)
    template = load_policy(Path(__file__).resolve().parents[2] / "policies/maintenance_v1.json")
    service = CaseService(repository, settings, template, clock)
    if perception_provider is not None and perception_provider.mode != settings.provider_mode:
        raise ValueError("Injected provider must match the explicitly configured provider mode.")
    if perception_provider is None and settings.provider_mode == "MOCK_AI":
        perception_provider = MockPerceptionProvider()
    if perception_provider is None and settings.provider_mode == "LIVE_GEMINI":
        from .gemini_provider import GeminiPerceptionProvider
        perception_provider = GeminiPerceptionProvider(settings)
    media = MediaService(service, perception_provider, media_storage or LocalPrivateMediaStorage(settings.media_root))

    @asynccontextmanager
    async def lifespan(app):
        yield
        if owned:
            repository.close()

    app = FastAPI(title="SENTINEL//LADDER", version="0.2.0", redoc_url=None, lifespan=lifespan)
    app.state.service = service
    app.state.settings = settings
    app.state.media = media

    @app.middleware("http")
    async def operational_headers(request: Request, call_next):
        # No cookies/CORS: credentials are explicit Authorization headers only.
        size = request.headers.get("content-length", "0")
        maximum = settings.max_image_bytes if settings.provider_mode != "DISABLED" and request.method == "POST" and re.fullmatch(r"/v1/cases/[^/]+/evidence", request.url.path) else 16384
        if not size.isdigit() or len(size) > 12 or int(size) > maximum:
            return JSONResponse(status_code=413, content={"decision": "DENY", "reason_codes": ["REQUEST_TOO_LARGE"], "guidance": "Use a JSON request under 16 KiB."})
        try:
            response = await call_next(request)
        except Exception:
            # Handle before Uvicorn's generic exception logger can print payloads.
            response = JSONResponse(status_code=500, content={"decision": "DENY", "reason_codes": ["INTERNAL_ERROR"],
                "guidance": "Request failed. Reload current state and contact the local operator before retrying."})
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(AppError)
    async def application_error(request, exc):
        return JSONResponse(status_code=exc.status,
            headers={"WWW-Authenticate": "Bearer"} if exc.status == 401 else None,
            content={"decision": "DENY", "reason_codes": [exc.code], "guidance": exc.guidance})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Pydantic's default input echo can contain passwords or untrusted payloads.
        return JSONResponse(status_code=422, content={"decision": "DENY", "reason_codes": ["INVALID_REQUEST"],
                                                     "guidance": "Check required fields and types in /docs; authority fields are not accepted."})

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        return JSONResponse(status_code=500, content={"decision": "DENY", "reason_codes": ["INTERNAL_ERROR"],
                                                     "guidance": "Request failed. Reload current state and contact the local operator before retrying."})

    app.add_middleware(BoundedBody, image_maximum=settings.max_image_bytes if settings.provider_mode != "DISABLED" else None)

    app.add_api_route("/healthz", healthz, methods=["GET"], response_model=Health, tags=["health"])

    @app.post("/v1/auth/login", tags=["identity"])
    def login(data: Login):
        return service.login(data.tenant_id, data.username, data.password.get_secret_value())

    @app.post("/v1/auth/logout", tags=["identity"])
    def logout(token: str = Depends(bearer_token)):
        return service.logout(token)

    @app.get("/v1/me", tags=["identity"])
    def me(token: str = Depends(bearer_token)):
        return service.me(token)

    @app.post("/v1/jobs", status_code=201, tags=["jobs"])
    def create_job(data: JobCreate, token: str = Depends(bearer_token)):
        return service.create_job(token, data.model_dump())

    @app.get("/v1/jobs", tags=["jobs"])
    def list_jobs(token: str = Depends(bearer_token)):
        return service.list_jobs(token)

    @app.get("/v1/jobs/{job_id}", tags=["jobs"])
    def get_job(job_id: str, token: str = Depends(bearer_token)):
        return service.get_job(token, job_id)

    @app.patch("/v1/jobs/{job_id}/assignment", tags=["jobs"])
    def assign(job_id: str, data: AssignmentChange, token: str = Depends(bearer_token)):
        return service.reassign(token, job_id, data.expected_job_version, data.contractor_id)

    @app.post("/v1/jobs/{job_id}/challenges", tags=["jobs"])
    def challenge(job_id: str, data: ChallengeRequest, token: str = Depends(bearer_token)):
        return service.challenge(token, job_id, data.case_id, data.expected_case_version)

    @app.post("/v1/cases", status_code=201, tags=["cases"])
    def create_case(data: CaseCreate, token: str = Depends(bearer_token)):
        return service.create_case(token, data.model_dump())

    @app.get("/v1/cases/{case_id}", tags=["cases"])
    def get_case(case_id: str, token: str = Depends(bearer_token)):
        return service.get_case(token, case_id)

    @app.patch("/v1/cases/{case_id}/invoice", tags=["cases"])
    def invoice(case_id: str, data: InvoiceChange, token: str = Depends(bearer_token)):
        return service.change_invoice(token, case_id, data.expected_case_version, data.invoice_amount_paise)

    @app.patch("/v1/cases/{case_id}/policy", tags=["cases"])
    def select_policy(case_id: str, data: PolicyChange, token: str = Depends(bearer_token)):
        return service.select_policy(token, case_id, data.expected_case_version, data.policy_version)

    @app.post("/v1/cases/{case_id}/actions/evaluate", tags=["actions"])
    def evaluate(case_id: str, data: ActionRequest, token: str = Depends(bearer_token)):
        status, result = service.action(token, case_id, data.expected_case_version, data.action)
        return JSONResponse(status_code=status, content=result)

    @app.post("/v1/cases/{case_id}/actions/execute", tags=["actions"])
    def execute(case_id: str, data: ActionRequest, token: str = Depends(bearer_token)):
        status, result = service.action(token, case_id, data.expected_case_version, data.action, execute=True)
        return JSONResponse(status_code=status, content=result)

    @app.post("/v1/cases/{case_id}/approvals", tags=["review"])
    def approve(case_id: str, data: Versioned, token: str = Depends(bearer_token)):
        return service.approve(token, case_id, data.expected_case_version)

    @app.get("/v1/cases/{case_id}/audit", tags=["review"])
    def audit(case_id: str, token: str = Depends(bearer_token)):
        return service.audit(token, case_id)

    @app.post("/v1/cases/{case_id}/evidence", tags=["evidence"], openapi_extra={"requestBody": {"required": True,
        "content": {kind: {"schema": {"type": "string", "format": "binary"}} for kind in ("image/jpeg", "image/png")}}})
    async def upload_evidence(case_id: str, request: Request, token: str = Depends(bearer_token),
            expected: str | None = Header(None, alias="X-Expected-Case-Version"),
            challenge_id: str | None = Header(None, alias="X-Challenge-ID"),
            evidence_session_id: str | None = Header(None, alias="X-Evidence-Session-ID")):
        await asyncio.to_thread(media.gate, token, case_id)
        if expected is None or not re.fullmatch(r"[1-9][0-9]{0,9}", expected) or not challenge_id or not evidence_session_id or max(len(challenge_id), len(evidence_session_id)) > 100:
            raise AppError(422, "INVALID_EVIDENCE_BINDING", "Provide the current case version, issued challenge ID and evidence session in the documented headers.")
        status, view = await media.submit(token, case_id, int(expected), challenge_id, evidence_session_id,
                                         await request.body(), request.headers.get("content-type", "application/octet-stream"))
        return JSONResponse(status_code=status, content=view)

    @app.get("/v1/cases/{case_id}/evidence/{evidence_id}/content", tags=["evidence"])
    def private_content(case_id: str, evidence_id: str, token: str = Depends(bearer_token)):
        data, mime = media.content(token, case_id, evidence_id)
        return Response(data, media_type=mime, headers={"Content-Disposition": "attachment; filename=evidence-image",
                                                       "Content-Security-Policy": "default-src 'none'; sandbox"})

    return app
