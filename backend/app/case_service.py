"""Authenticated case workflow; every decision and mutation sees one transaction.

No provider is imported. Synthetic intake is a test-only Python call, never a route.
"""

from datetime import datetime, timezone
import hashlib
import json
import secrets
from uuid import uuid4

from .auth import hash_password, verify_password, token_digest, new_token, ITERATIONS
from .api_models import Role
from .errors import AppError, forbidden, not_found, conflict
from .models import Observation, Policy, EvaluationContext, Action
from .policy import authorize
from .repository import Repository
from .settings import Settings


def uid():
    return str(uuid4())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


class CaseService:
    def __init__(self, repository: Repository, settings: Settings, template: Policy, clock=None):
        self.repository = repository
        self.settings = settings
        self.template = template
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        # Salted dummy work keeps unknown-account and wrong-password paths comparable.
        self.dummy_password_hash = hash_password(secrets.token_urlsafe(32))

    def _now(self):
        now = self.clock()
        if now.tzinfo is None:
            raise ValueError("Server clock must be timezone-aware")
        return now.astimezone(timezone.utc).timestamp()

    def _actor(self, tx, token, now):
        session = tx.get("sessions", token_hash=token_digest(token))
        if not session or session["revoked"] or session["expires_at"] <= now:
            raise AppError(401, "AUTHENTICATION_REQUIRED", "Log in again with your own account.")
        actor = tx.get("users", id=session["user_id"], active=True)
        if not actor:
            raise AppError(401, "AUTHENTICATION_REQUIRED", "Log in with an active account.")
        return {**actor, "session_id": session["id"]}

    @staticmethod
    def _role(actor, *roles):
        if actor["role"] not in roles:
            raise forbidden()

    def _job(self, tx, actor, job_id):
        job = tx.get("jobs", id=job_id, tenant_id=actor["tenant_id"])
        if not job:
            raise not_found()
        field = {Role.CONTRACTOR: "contractor_id", Role.ENGINEER: "engineer_id",
                 Role.SERVICE_AGENT: "service_agent_id"}.get(actor["role"])
        if field and job[field] != actor["id"]:
            raise not_found()
        return job

    def _case(self, tx, actor, case_id):
        case = tx.get("cases", id=case_id, tenant_id=actor["tenant_id"])
        if not case:
            raise not_found()
        return case, self._job(tx, actor, case["job_id"])

    @staticmethod
    def _version(case, expected):
        if case["version"] != expected:
            raise conflict()

    def _event(self, tx, actor, case, event_type, now, action=None, decision=None, reasons=()):
        ev = tx.get("evidence", id=case["evidence_id"]) if case["evidence_id"] else None
        tx.add("decision_events", dict(id=uid(), tenant_id=case["tenant_id"], case_id=case["id"],
            actor_id=actor["id"], event_type=event_type, case_version=case["version"],
            evidence_version=case["evidence_version"], evidence_sha256=ev["sha256"] if ev else None,
            policy_version=case["policy_version"], action=action, decision=decision,
            reason_codes_json=canonical(list(reasons)), created_at=now))

    def login(self, tenant_id, username, password):
        bucket = digest([tenant_id, username])
        error = None
        result = None
        with self.repository.transaction() as tx:
            now = self._now()
            limit = tx.get("auth_limits", id=bucket)
            if limit and limit["resets_at"] > now and limit["attempts"] >= 5:
                error = AppError(429, "LOGIN_RATE_LIMITED", "Wait up to 15 minutes before trying again.")
            else:
                actor = tx.get("users", tenant_id=tenant_id, username=username)
                valid = verify_password(password, actor["password_hash"] if actor else self.dummy_password_hash)
                if not valid or not actor or not actor["active"]:
                    attempts = limit["attempts"] + 1 if limit and limit["resets_at"] > now else 1
                    values = dict(attempts=attempts, resets_at=limit["resets_at"] if limit and limit["resets_at"] > now else now + 900)
                    if limit:
                        tx.change("auth_limits", {"id": bucket}, values)
                    else:
                        tx.add("auth_limits", {"id": bucket, **values})
                    error = AppError(401, "INVALID_CREDENTIALS", "Check your tenant, username and password.")
                else:
                    if limit:
                        tx.change("auth_limits", {"id": bucket}, dict(attempts=0, resets_at=now + 900))
                    token = new_token()
                    tx.add("sessions", dict(id=uid(), token_hash=token_digest(token), user_id=actor["id"],
                                             expires_at=now + self.settings.session_seconds, revoked=False))
                    result = dict(access_token=token, token_type="bearer", expires_in=self.settings.session_seconds)
        # Raise after commit so failed attempts cannot be rolled back by the error.
        if error:
            raise error
        return result

    def me(self, token):
        with self.repository.transaction() as tx:
            actor = self._actor(tx, token, self._now())
            return {k: actor[k] for k in ("id", "tenant_id", "username", "role")}

    def logout(self, token):
        with self.repository.transaction() as tx:
            actor = self._actor(tx, token, self._now())
            tx.change("sessions", {"id": actor["session_id"]}, {"revoked": True})
        return {"status": "logged_out"}

    def create_job(self, token, data):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.MANAGER)
            for field, role in (("contractor_id", Role.CONTRACTOR), ("engineer_id", Role.ENGINEER),
                                ("service_agent_id", Role.SERVICE_AGENT)):
                user = tx.get("users", id=data[field], tenant_id=actor["tenant_id"], active=True)
                if not user or user["role"] != role:
                    raise AppError(422, "INVALID_ASSIGNMENT", "Choose an active account with the required role in this tenant.")
            job = dict(id=uid(), tenant_id=actor["tenant_id"], version=1, **data)
            try:
                policy = Policy.model_validate({**self.template.model_dump(), "tenant_id": job["tenant_id"],
                                                "job_id": job["id"], "asset_id_expected": job["asset_id"]})
            except ValueError as exc:
                raise AppError(422, "INVALID_JOB", "Use a non-placeholder exact asset identifier.") from exc
            tx.add("jobs", job)
            # This template is source-controlled and covered by the accepted pure-policy tests.
            tx.add("policies", dict(id=uid(), tenant_id=job["tenant_id"], job_id=job["id"], version=policy.version,
                config_json=policy.model_dump_json(), author_id="SOURCE_CONTROL", reviewer_id="PHASE_00_ACCEPTED",
                review_reference="policies/maintenance_v1.json; accepted Phase 00 regression suite"))
            return job

    def list_jobs(self, token):
        with self.repository.transaction() as tx:
            actor = self._actor(tx, token, self._now())
            self._role(actor, Role.CONTRACTOR, Role.MANAGER, Role.ENGINEER)
            keys = {"tenant_id": actor["tenant_id"]}
            if actor["role"] == Role.CONTRACTOR:
                keys["contractor_id"] = actor["id"]
            if actor["role"] == Role.ENGINEER:
                keys["engineer_id"] = actor["id"]
            return tx.find("jobs", **keys)

    def get_job(self, token, job_id):
        with self.repository.transaction() as tx:
            actor = self._actor(tx, token, self._now())
            self._role(actor, Role.CONTRACTOR, Role.MANAGER, Role.ENGINEER)
            return self._job(tx, actor, job_id)

    def create_case(self, token, data):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.MANAGER)
            job = self._job(tx, actor, data["job_id"])
            case = dict(id=uid(), tenant_id=actor["tenant_id"], job_id=job["id"], version=1,
                evidence_version=0, evidence_id=None, approval_id=None, challenge_id=None,
                policy_version=self.template.version, invoice_amount_paise=data["invoice_amount_paise"])
            tx.add("cases", case)
            self._event(tx, actor, case, "CASE_CREATED", now)
            return self._view(tx, actor, case, job, now)

    def _challenge_valid(self, tx, case, job, challenge, now):
        if not challenge or (challenge["tenant_id"], challenge["job_id"], challenge["asset_id"], challenge["case_id"]) != (
            case["tenant_id"], job["id"], job["asset_id"], case["id"]):
            return False
        session = tx.get("sessions", id=challenge["auth_session_id"])
        submitter = tx.get("users", id=challenge["actor_id"], tenant_id=case["tenant_id"], active=True)
        return bool(challenge["expires_at"] > now and session and not session["revoked"] and
                    session["expires_at"] > now and session["user_id"] == job["contractor_id"] and
                    submitter and submitter["role"] == Role.CONTRACTOR and submitter["id"] == job["contractor_id"])

    def _base(self, tx, case, job, now):
        row = tx.get("policies", tenant_id=case["tenant_id"], job_id=job["id"], version=case["policy_version"])
        policy = Policy.model_validate_json(row["config_json"])
        challenge = tx.get("challenges", id=case["challenge_id"], tenant_id=case["tenant_id"], case_id=case["id"]) if case["challenge_id"] else None
        ev = tx.get("evidence", id=case["evidence_id"], tenant_id=case["tenant_id"], case_id=case["id"]) if case["evidence_id"] else None
        observation = json.loads(ev["observation_json"]) if ev else None
        ctx = EvaluationContext(tenant_id=case["tenant_id"], job_id=job["id"], asset_id_expected=job["asset_id"],
            approved_policy_version=case["policy_version"], expected_challenge=challenge["token"] if challenge else "NO_ACTIVE_CHALLENGE",
            challenge_expires_at=datetime.fromtimestamp(challenge["expires_at"] if challenge else now, timezone.utc),
            evaluated_at=datetime.fromtimestamp(now, timezone.utc))
        result = authorize(observation, policy, ctx).model_dump(mode="json")
        if result["max_permission"] == 2:
            result["guidance"] = "Prepare the simulated invoice for independent manager review; approval is required before completion."
        valid = self._challenge_valid(tx, case, job, challenge, now)
        if ev and (not valid or ev["challenge_id"] != case["challenge_id"] or ev["version"] != case["evidence_version"]):
            result.update(max_permission=0, decision="DENY")
            if result["inspection_status"] != "SAFETY_ALERT":
                result["inspection_status"] = "EVIDENCE_MISSING"
            result["reason_codes"] = list(dict.fromkeys([*result["reason_codes"], "CHALLENGE_OR_SESSION_INVALID"]))
            result["guidance"] = "Request a fresh challenge in your active session and resubmit evidence."
        if ev and (ev["artifact_mode"] != "SYNTHETIC" or not self.settings.allow_synthetic):
            result.update(max_permission=0, decision="DENY", inspection_status="REVIEW_REQUIRED",
                          reason_codes=["TEST_EVIDENCE_DISABLED"], guidance="Phase 01 accepts synthetic observations only in its internal test factory.")
        return result, ev, challenge

    def _binding(self, case, job, ev, challenge, reviewer_id, reviewed_version):
        return dict(tenant_id=case["tenant_id"], case_id=case["id"], job_id=job["id"],
            asset_id=job["asset_id"], job_version=job["version"], contractor_id=job["contractor_id"],
            action=Action.COMPLETE_SIMULATED_ACTION.value, invoice_amount_paise=case["invoice_amount_paise"],
            evidence_sha256=ev["sha256"], evidence_version=case["evidence_version"],
            evidence_id=ev["id"], case_version=reviewed_version, policy_version=case["policy_version"],
            reviewer_id=reviewer_id, challenge_id=challenge["id"], evidence_session_id=challenge["evidence_session_id"],
            auth_session_id=challenge["auth_session_id"], challenge_expires_at=challenge["expires_at"])

    def _refresh(self, tx, actor, case, job, now):
        result, ev, challenge = self._base(tx, case, job, now)
        approval = tx.get("approvals", id=case["approval_id"], tenant_id=case["tenant_id"]) if case["approval_id"] else None
        if case["approval_id"]:
            reviewer = tx.get("users", id=approval["reviewer_id"], tenant_id=case["tenant_id"], active=True) if approval else None
            valid = bool(approval and reviewer and reviewer["role"] == Role.MANAGER and ev and challenge and
                reviewer["id"] != ev["submitted_by"] and result["max_permission"] == 2 and
                case["version"] == approval["effective_case_version"])
            if valid:
                binding = self._binding(case, job, ev, challenge, reviewer["id"], approval["reviewed_case_version"])
                valid = digest(binding) == approval["binding_sha256"] and canonical(binding) == approval["binding_json"]
            if valid:
                result.update(max_permission=3, inspection_status="APPROVED_BY_HUMAN", decision="ALLOW",
                              reason_codes=["CURRENT_HUMAN_APPROVAL"], guidance="Only simulated completion is authorized; no payment or equipment control exists.")
            else:
                case = tx.cas_case(case, case["version"], {"approval_id": None})
                self._event(tx, actor, case, "APPROVAL_INVALIDATED", now, reasons=["APPROVAL_STALE"])
        return case, result

    def _view(self, tx, actor, case, job, now, result=None):
        if result is None:
            case, result = self._refresh(tx, actor, case, job, now)
        ev = tx.get("evidence", id=case["evidence_id"]) if case["evidence_id"] else None
        approval = tx.get("approvals", id=case["approval_id"]) if case["approval_id"] else None
        completed = bool(approval and tx.get("action_runs", case_id=case["id"],
            action=Action.COMPLETE_SIMULATED_ACTION.value, binding_sha256=approval["binding_sha256"]))
        view = {k: case[k] for k in ("id", "tenant_id", "job_id", "version", "invoice_amount_paise", "evidence_version", "policy_version")}
        view.update(asset_id=job["asset_id"], **result, simulated=True, simulated_completed=completed,
                    evidence_sha256=ev["sha256"] if ev else None, artifact_mode=ev["artifact_mode"] if ev else None)
        if ev and actor["role"] in {Role.MANAGER, Role.CONTRACTOR}:
            view["observation"] = {k: v for k, v in json.loads(ev["observation_json"]).items() if k != "challenge_text_observed"}
        return view

    def get_case(self, token, case_id):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.CONTRACTOR, Role.MANAGER, Role.ENGINEER)
            case, job = self._case(tx, actor, case_id)
            case, result = self._refresh(tx, actor, case, job, now)
            self._event(tx, actor, case, "CASE_READ", now, decision=result["decision"], reasons=result["reason_codes"])
            return self._view(tx, actor, case, job, now, result)

    def challenge(self, token, job_id, case_id, expected):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.CONTRACTOR)
            case, job = self._case(tx, actor, case_id)
            if job["id"] != job_id:
                raise not_found()
            self._version(case, expected)
            issued = tx.find("challenges", tenant_id=actor["tenant_id"], job_id=job_id, actor_id=actor["id"])
            if sum(ch["created_at"] > now - 600 for ch in issued) >= self.settings.max_challenges_per_window:
                raise AppError(429, "CHALLENGE_RATE_LIMITED", "Wait up to 10 minutes before requesting another challenge.")
            ch = dict(id=uid(), tenant_id=case["tenant_id"], case_id=case_id, job_id=job_id, asset_id=job["asset_id"],
                evidence_session_id=secrets.token_urlsafe(32), auth_session_id=actor["session_id"], actor_id=actor["id"],
                token=secrets.token_urlsafe(32), created_at=now, expires_at=now + self.settings.challenge_seconds)
            tx.add("challenges", ch)
            had_approval = bool(case["approval_id"])
            case = tx.cas_case(case, expected, dict(challenge_id=ch["id"], evidence_id=None, approval_id=None))
            self._event(tx, actor, case, "CHALLENGE_ISSUED", now, reasons=["APPROVAL_INVALIDATED"] if had_approval else [])
            return {k: ch[k] for k in ("id", "tenant_id", "case_id", "job_id", "asset_id", "evidence_session_id", "token", "expires_at")} | {"case_version": case["version"], "supporting_evidence_only": True}

    def inject_synthetic_evidence(self, token, case_id, expected, challenge_id, evidence_session_id, observation):
        """Internal test-only intake. Hashes canonical fixture bytes, not real media."""
        if self.settings.environment != "test" or not self.settings.allow_synthetic:
            raise AppError(403, "TEST_EVIDENCE_DISABLED", "Synthetic input is available only through the internal test factory.")
        try:
            obs = Observation.model_validate(observation)
            if obs.artifact_mode != "SYNTHETIC":
                raise ValueError("Not synthetic")
        except ValueError as exc:
            raise AppError(422, "INVALID_OBSERVATION", "Provide typed SYNTHETIC observation data without authority fields.") from exc
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.CONTRACTOR)
            case, job = self._case(tx, actor, case_id)
            self._version(case, expected)
            ch = tx.get("challenges", id=case["challenge_id"])
            if not self._challenge_valid(tx, case, job, ch, now) or ch["id"] != challenge_id or ch["evidence_session_id"] != evidence_session_id or ch["auth_session_id"] != actor["session_id"]:
                raise AppError(409, "CHALLENGE_INVALID", "Request a current challenge in this authenticated session.")
            payload = obs.model_dump(mode="json")
            ev = dict(id=uid(), tenant_id=case["tenant_id"], case_id=case_id, challenge_id=ch["id"],
                version=case["evidence_version"] + 1, sha256=digest(payload), observation_json=canonical(payload),
                artifact_mode="SYNTHETIC", submitted_by=actor["id"])
            tx.add("evidence", ev)
            had_approval = bool(case["approval_id"])
            case = tx.cas_case(case, expected, dict(evidence_id=ev["id"], evidence_version=ev["version"], approval_id=None))
            self._event(tx, actor, case, "SYNTHETIC_EVIDENCE_REPLACED", now, reasons=["APPROVAL_INVALIDATED"] if had_approval else [])
            return self._view(tx, actor, case, job, now)

    def _authorize_action(self, actor, action, result):
        allowed_roles = {
            Action.CREATE_DRAFT: {Role.CONTRACTOR, Role.MANAGER, Role.SERVICE_AGENT},
            Action.REQUEST_EVIDENCE: {Role.CONTRACTOR, Role.MANAGER, Role.SERVICE_AGENT},
            Action.RECORD_PROVISIONAL_VISIT: {Role.CONTRACTOR, Role.SERVICE_AGENT},
            Action.PREPARE_INVOICE: {Role.SERVICE_AGENT},
            Action.COMPLETE_SIMULATED_ACTION: {Role.SERVICE_AGENT},
        }
        self._role(actor, *allowed_roles[action])
        required = {Action.CREATE_DRAFT: 0, Action.REQUEST_EVIDENCE: 0, Action.RECORD_PROVISIONAL_VISIT: 1,
                    Action.PREPARE_INVOICE: 2, Action.COMPLETE_SIMULATED_ACTION: 3}[action]
        result = {**result, "reason_codes": list(result["reason_codes"])}
        # Internal validation errors cannot authorize even an L0 action.
        invalid = any(code.startswith("INVALID_") or code in {"INTERNAL_ERROR", "TEST_EVIDENCE_DISABLED", "POLICY_CONTEXT_MISMATCH"} for code in result["reason_codes"])
        if result["max_permission"] < required or invalid:
            result["decision"] = "DENY"
            result["reason_codes"].append("PERMISSION_INSUFFICIENT")
            result["guidance"] = "Supply current valid evidence and, for completion, obtain independent manager approval."
        else:
            result["decision"] = "ALLOW"
        return result

    def action(self, token, case_id, expected, action, execute=False):
        action = Action(action)
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            case, job = self._case(tx, actor, case_id)
            case, base = self._refresh(tx, actor, case, job, now)
            # Expiry invalidation must commit even if it bumps a version; return a
            # denied current-state decision instead of rolling invalidation back.
            if case["version"] != expected:
                result = dict(base, decision="DENY", reason_codes=["VERSION_CONFLICT"],
                              guidance="Reload the current case and retry with its current version.")
                status = 409
            else:
                result = self._authorize_action(actor, action, base)
                status = 200
            receipt = None
            replay = False
            if execute and result["decision"] == "ALLOW":
                approval = tx.get("approvals", id=case["approval_id"]) if case["approval_id"] else None
                binding = approval["binding_sha256"] if action == Action.COMPLETE_SIMULATED_ACTION else digest([case["id"], case["version"], action.value])
                receipt = tx.get("action_runs", case_id=case_id, action=action.value, binding_sha256=binding)
                replay = bool(receipt)
                if not receipt:
                    receipt = dict(id=uid(), tenant_id=case["tenant_id"], case_id=case_id, action=action.value,
                                   binding_sha256=binding, actor_id=actor["id"], created_at=now)
                    tx.add("action_runs", receipt)
                    self._event(tx, actor, case, "SIMULATED_ACTION_EXECUTED", now, action.value, "ALLOW", result["reason_codes"])
            if not execute or result["decision"] != "ALLOW":
                self._event(tx, actor, case, "ACTION_EVALUATED", now, action.value, result["decision"], result["reason_codes"])
            return status, {**result, "case_version": case["version"], "action": action.value, "simulated": True,
                            "receipt_id": receipt["id"] if receipt else None, "already_executed": replay}

    def approve(self, token, case_id, expected):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.MANAGER)
            case, job = self._case(tx, actor, case_id)
            self._version(case, expected)
            result, ev, ch = self._base(tx, case, job, now)
            if not ev or result["max_permission"] != 2 or result["decision"] != "ALLOW":
                raise AppError(409, "L2_REQUIRED", "Review complete current evidence under the approved policy before signing off.")
            if ev["submitted_by"] == actor["id"]:
                raise AppError(403, "INDEPENDENT_REVIEW_REQUIRED", "A different authenticated manager must review this evidence.")
            binding = self._binding(case, job, ev, ch, actor["id"], expected)
            approval = dict(id=secrets.token_urlsafe(32), tenant_id=case["tenant_id"], case_id=case_id,
                reviewer_id=actor["id"], reviewed_case_version=expected, effective_case_version=expected + 1,
                binding_json=canonical(binding), binding_sha256=digest(binding), created_at=now)
            tx.add("approvals", approval)
            case = tx.cas_case(case, expected, {"approval_id": approval["id"]})
            self._event(tx, actor, case, "MANAGER_APPROVED_SIMULATION", now,
                        Action.COMPLETE_SIMULATED_ACTION.value, "ALLOW", ["CURRENT_HUMAN_APPROVAL"])
            return self._view(tx, actor, case, job, now)

    def change_invoice(self, token, case_id, expected, amount):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.MANAGER)
            case, job = self._case(tx, actor, case_id)
            self._version(case, expected)
            case = tx.cas_case(case, expected, {"invoice_amount_paise": amount, "approval_id": None})
            self._event(tx, actor, case, "INVOICE_CHANGED", now, reasons=["APPROVAL_INVALIDATED"])
            return self._view(tx, actor, case, job, now)

    def select_policy(self, token, case_id, expected, version):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.ENGINEER)
            case, job = self._case(tx, actor, case_id)
            self._version(case, expected)
            if not tx.get("policies", tenant_id=case["tenant_id"], job_id=job["id"], version=version):
                raise AppError(422, "POLICY_NOT_REVIEWED", "Choose an already reviewed policy version; HTTP cannot publish policies.")
            case = tx.cas_case(case, expected, {"policy_version": version, "approval_id": None})
            self._event(tx, actor, case, "REVIEWED_POLICY_SELECTED", now, reasons=["APPROVAL_INVALIDATED"])
            return self._view(tx, actor, case, job, now)

    def reassign(self, token, job_id, expected, contractor_id):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.MANAGER)
            job = self._job(tx, actor, job_id)
            if job["version"] != expected:
                raise conflict()
            if not tx.get("users", id=contractor_id, tenant_id=actor["tenant_id"], role=Role.CONTRACTOR.value, active=True):
                raise AppError(422, "INVALID_ASSIGNMENT", "Choose an active contractor in this tenant.")
            tx.change("jobs", {"id": job_id, "version": expected}, {"contractor_id": contractor_id, "version": expected + 1})
            for case in tx.find("cases", tenant_id=actor["tenant_id"], job_id=job_id):
                case = tx.cas_case(case, case["version"], dict(approval_id=None, challenge_id=None, evidence_id=None))
                self._event(tx, actor, case, "JOB_REASSIGNED", now, reasons=["APPROVAL_INVALIDATED", "NEW_EVIDENCE_REQUIRED"])
            return {**job, "contractor_id": contractor_id, "version": expected + 1}

    def audit(self, token, case_id):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.CONTRACTOR, Role.MANAGER, Role.ENGINEER)
            case, job = self._case(tx, actor, case_id)
            case, result = self._refresh(tx, actor, case, job, now)
            self._event(tx, actor, case, "AUDIT_READ", now)
            rows = sorted(tx.find("decision_events", tenant_id=actor["tenant_id"], case_id=case_id),
                          key=lambda row: (row["created_at"], row["id"]))[-100:]
            return [{k: v for k, v in row.items() if k != "reason_codes_json"} | {"reason_codes": json.loads(row["reason_codes_json"])} for row in rows]
