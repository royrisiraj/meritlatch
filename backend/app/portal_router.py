"""Small scoped read additions for portals; existing mutations stay authoritative."""
from fastapi import APIRouter, Depends, Query
from .api_models import Role
from .errors import not_found
from .workflow_service import WorkflowService
from .assurance_service import AssuranceService


def build_router(service, bearer_token, *, enable_assurance=True):
    router = APIRouter(tags=["portal-reads"])

    @router.get("/v1/assignees")
    def assignees(token: str = Depends(bearer_token), role: Role = Role.CONTRACTOR,
                  limit: int = Query(100, ge=1, le=100), after: str | None = Query(None, max_length=100)):
        with service.repository.transaction() as tx:
            actor = service._actor(tx, token, service._now())
            service._role(actor, Role.MANAGER)
            keys = dict(tenant_id=actor["tenant_id"], role=role.value, active=True)
            if after and not tx.get("users", id=after, **keys):
                raise not_found()
            rows = tx.identifier_page("users", keys, limit + 1, after)
            return dict(items=[{k: u[k] for k in ("id", "username", "role")} for u in rows[:limit]],
                        next_cursor=rows[limit-1]["id"] if len(rows) > limit else None)

    @router.get("/v1/jobs/{job_id}/cases")
    def cases(job_id: str, token: str = Depends(bearer_token), limit: int = Query(25, ge=1, le=100),
              after: str | None = Query(None, max_length=100)):
        with service.repository.transaction() as tx:
            now = service._now()
            actor = service._actor(tx, token, now)
            service._role(actor, Role.MANAGER, Role.CONTRACTOR, Role.ENGINEER)
            job = service._job(tx, actor, job_id)
            keys = dict(tenant_id=actor["tenant_id"], job_id=job_id)
            if after and not tx.get("cases", id=after, **keys):
                raise not_found()
            rows = tx.identifier_page("cases", keys, limit + 1, after)
            items = []
            for row in rows[:limit]:
                case, _ = service._case(tx, actor, row["id"])
                case, result = service._refresh(tx, actor, case, job, now)
                service._event(tx, actor, case, "PORTAL_CASE_LIST_READ", now)
                items.append(WorkflowService.summary(service._view(tx, actor, case, job, now, result)))
            return dict(items=items, next_cursor=rows[limit-1]["id"] if len(rows) > limit else None)

    def history(candidate_id: str, token: str = Depends(bearer_token)):
        assurance = AssuranceService(service)
        with service.repository.transaction() as tx:
            actor, now = assurance.auth(tx, token)
            assurance.scoped(tx, "security_candidates", actor, candidate_id)
            keys = dict(tenant_id=actor["tenant_id"], candidate_id=candidate_id)
            result = {}
            for name in ("proposals", "reviews", "gates"):
                rows = tx.page("security_" + name, keys, 21)
                result[name] = [assurance.gate_view(tx, row) if name == "gates" else row for row in rows[:20]]
                result[name + "_truncated"] = len(rows) > 20
            assurance.event(tx, actor, now, "CANDIDATE_HISTORY_READ", candidate_id)
            return result

    if enable_assurance:
        router.add_api_route("/v1/redteam/candidates/{candidate_id}/history", history, methods=["GET"])
    return router
