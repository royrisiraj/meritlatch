"""Manager review and bounded queue orchestration using the existing case service."""

import json

from .api_models import Role
from .case_service import uid
from .errors import AppError, not_found
from .models import Action, Policy
from .workflow_models import BusinessStatus, CaseSummary, RejectionReason


class WorkflowService:
    def __init__(self, cases):
        self.cases = cases

    def templates(self, token):
        with self.cases.repository.transaction() as tx:
            actor = self.cases._actor(tx, token, self.cases._now())
            self.cases._role(actor, Role.MANAGER)
            data = self.cases.template.model_dump(mode="json")
            return [{k: v for k, v in data.items() if k not in {"tenant_id", "job_id", "asset_id_expected"}}]

    @staticmethod
    def summary(view):
        data = {name: view.get(name) for name in CaseSummary.model_fields}
        data["provider_mode"] = view.get("provider_mode", view.get("artifact_mode"))
        return CaseSummary.model_validate(data).model_dump(mode="json")

    def queue(self, token, limit=25, cursor=None, business_status=None, inspection_status=None,
              approval_eligible=None, contractor_id=None, attention_only=True):
        with self.cases.repository.transaction() as tx:
            now = self.cases._now()
            actor = self.cases._actor(tx, token, now)
            self.cases._role(actor, Role.MANAGER)
            if contractor_id and not tx.get("users", id=contractor_id, tenant_id=actor["tenant_id"], role="CONTRACTOR"):
                raise not_found()
            rows = tx.case_page(actor["tenant_id"], cursor, 501, contractor_id)
            items, scanned, position = [], 0, None
            attention = {"AWAITING_REVIEW", "CORRECTION_REQUIRED", "REJECTED"}
            for row in rows[:500]:
                case, job = self.cases._case(tx, actor, row["id"])
                case, result = self.cases._refresh(tx, actor, case, job, now)
                view = self.cases._view(tx, actor, case, job, now, result)
                scanned += 1
                position = row["id"]
                match = (not attention_only or view["business_status"] in attention)
                match &= business_status is None or view["business_status"] == business_status
                match &= inspection_status is None or view["inspection_status"] == inspection_status
                match &= approval_eligible is None or view["approval_eligible"] is approval_eligible
                if match:
                    items.append(self.summary(view))
                    self.cases._event(tx, actor, case, "REVIEW_QUEUE_READ", now, decision=result["decision"], reasons=result["reason_codes"])
                if len(items) >= limit:
                    break
            return dict(items=items, next_cursor=position if scanned < len(rows) else None, scanned=scanned, snapshot_at=now)

    def details(self, token, case_id):
        with self.cases.repository.transaction() as tx:
            now = self.cases._now()
            actor = self.cases._actor(tx, token, now)
            self.cases._role(actor, Role.MANAGER)
            case, job = self.cases._case(tx, actor, case_id)
            case, result = self.cases._refresh(tx, actor, case, job, now)
            view = self.cases._view(tx, actor, case, job, now, result)
            policy = tx.get("policies", tenant_id=actor["tenant_id"], job_id=job["id"], version=case["policy_version"])
            history = tx.recent("manager_reviews", {"tenant_id": actor["tenant_id"], "case_id": case_id}, "effective_case_version", 101)
            public = [{key: value for key, value in row.items() if key not in {"tenant_id", "case_id", "internal_approval_id", "challenge_id"}} for row in history[:100]]
            self.cases._event(tx, actor, case, "MANAGER_REVIEW_READ", now, decision=result["decision"], reasons=result["reason_codes"])
            return dict(case=self.summary(view), observation=view.get("observation", {}), missing_fields=view["missing_fields"],
                uncertain_fields=view["uncertain_fields"], policy_constraints=Policy.model_validate_json(policy["config_json"]).model_dump(mode="json"),
                media=view.get("media"), current_attachment=f"/v1/cases/{case_id}/evidence/{case['evidence_id']}/content" if view.get("media") else None,
                reviews=public, history_truncated=len(history) > 100)

    def reject(self, token, case_id, expected, reason):
        reason = RejectionReason(reason).value
        with self.cases.repository.transaction() as tx:
            now = self.cases._now()
            actor = self.cases._actor(tx, token, now)
            self.cases._role(actor, Role.MANAGER)
            case, job = self.cases._case(tx, actor, case_id)
            self.cases._version(case, expected)
            ev = tx.get("evidence", id=case["evidence_id"], tenant_id=actor["tenant_id"], case_id=case_id)
            if not ev:
                raise AppError(409, "EVIDENCE_REQUIRED", "Wait for submitted evidence before recording an evidence rejection.")
            if self.cases._rejected(tx, case, ev):
                raise AppError(409, "EVIDENCE_ALREADY_REJECTED", "This evidence already requires a fresh challenge and corrected resubmission.")
            approval = tx.get("approvals", id=case["approval_id"]) if case["approval_id"] else None
            if approval and tx.get("action_runs", case_id=case_id, action=Action.COMPLETE_SIMULATED_ACTION.value, binding_sha256=approval["binding_sha256"]):
                raise AppError(409, "SIMULATION_ALREADY_COMPLETED", "A completed receipt is historical; submit a new evidence cycle instead of rewriting it.")
            review = dict(id=uid(), tenant_id=case["tenant_id"], case_id=case_id, decision="REJECTED", reviewer_id=actor["id"],
                created_at=now, reviewed_case_version=expected, effective_case_version=expected + 1,
                evidence_id=ev["id"], evidence_version=ev["version"], evidence_sha256=ev["sha256"], policy_version=case["policy_version"],
                invoice_amount_paise=case["invoice_amount_paise"], invoice_revision=case["invoice_revision"], challenge_id=ev["challenge_id"],
                reason_code=reason, internal_approval_id=None)
            tx.add("manager_reviews", review)
            case = tx.cas_case(case, expected, {"approval_id": None})
            self.cases._event(tx, actor, case, "MANAGER_REJECTED_EVIDENCE", now, Action.COMPLETE_SIMULATED_ACTION.value,
                              "DENY", ["MANAGER_REJECTED_EVIDENCE", reason], review_reference=review["id"])
            return self.cases._view(tx, actor, case, job, now)
