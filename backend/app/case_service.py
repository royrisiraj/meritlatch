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
from .media_state import media_observation
from .workflow_models import project_business


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
        meta = tx.get("case_workflow", tenant_id=actor["tenant_id"], case_id=case_id)
        case["invoice_revision"] = meta["invoice_revision"] if meta else 1
        return case, self._job(tx, actor, case["job_id"])

    @staticmethod
    def _version(case, expected):
        if case["version"] != expected:
            raise conflict()

    def _event(self, tx, actor, case, event_type, now, action=None, decision=None, reasons=(), review_reference=None, completion_reference=None, source_evidence=None):
        ev = tx.get("evidence", id=case["evidence_id"]) if case["evidence_id"] else None
        audit_ev = source_evidence or ev
        event_id = uid()
        tx.add("decision_events", dict(id=event_id, tenant_id=case["tenant_id"], case_id=case["id"],
            actor_id=actor["id"], event_type=event_type, case_version=case["version"],
            evidence_version=audit_ev["version"] if audit_ev else case["evidence_version"], evidence_sha256=audit_ev["sha256"] if audit_ev else None,
            policy_version=case["policy_version"], action=action, decision=decision or "RECORDED",
            reason_codes_json=canonical(list(reasons)), created_at=now))
        job = tx.get("jobs", tenant_id=case["tenant_id"], id=case["job_id"])
        base, current_ev, challenge = self._base(tx, case, job, now)
        approval = self._valid_approval(tx, case, job, base, current_ev, challenge)
        projected = {**base, "max_permission": 3} if approval else base
        completed = bool(approval and tx.get("action_runs", case_id=case["id"], action=Action.COMPLETE_SIMULATED_ACTION.value, binding_sha256=approval["binding_sha256"]))
        rejected = self._rejected(tx, case, ev)
        tx.add("workflow_events", dict(event_id=event_id, tenant_id=case["tenant_id"], case_id=case["id"], job_id=job["id"],
            business_status=project_business(case, projected, bool(rejected), completed), source_mode=audit_ev["artifact_mode"] if audit_ev else None,
            source_evidence_id=audit_ev["id"] if audit_ev else None,
            review_reference=review_reference, completion_reference=completion_reference))

    def _rejected(self, tx, case, ev):
        return tx.get("manager_reviews", tenant_id=case["tenant_id"], case_id=case["id"],
                      decision="REJECTED", evidence_sha256=ev["sha256"]) if ev else None

    def _job_view(self, tx, job):
        meta = tx.get("job_workflow", job_id=job["id"], tenant_id=job["tenant_id"])
        return {**job, "business_status": "ASSIGNED", "policy_id": meta["policy_id"] if meta else self.template.policy_id,
            "policy_version": meta["policy_version"] if meta else self.template.version,
            "invoice_amount_paise": meta["invoice_amount_paise"] if meta else 500000,
            "created_at": meta["created_at"] if meta else None,
            "recent_events": tx.recent("job_events", {"tenant_id": job["tenant_id"], "job_id": job["id"]}, "created_at", 20)}

    def _job_event(self, tx, actor, job, kind, now):
        tx.add("job_events", dict(id=uid(), tenant_id=job["tenant_id"], job_id=job["id"], actor_id=actor["id"],
                                 job_version=job["version"], event_type=kind, created_at=now))

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
            selected_id = data.get("policy_id") or self.template.policy_id
            selected_version = data.get("policy_version") or self.template.version
            if (selected_id, selected_version) != (self.template.policy_id, self.template.version):
                raise AppError(422, "POLICY_NOT_REVIEWED", "Select an existing approved template; managers cannot create policy rules.")
            job = dict(id=uid(), tenant_id=actor["tenant_id"], version=1,
                       **{key: data[key] for key in ("asset_id", "contractor_id", "engineer_id", "service_agent_id")})
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
            tx.add("job_workflow", dict(job_id=job["id"], tenant_id=job["tenant_id"], policy_id=selected_id,
                policy_version=selected_version, invoice_amount_paise=data.get("invoice_amount_paise", 500000), created_at=now))
            self._job_event(tx, actor, job, "JOB_CREATED_AND_ASSIGNED", now)
            return self._job_view(tx, job)

    def list_jobs(self, token):
        with self.repository.transaction() as tx:
            actor = self._actor(tx, token, self._now())
            self._role(actor, Role.CONTRACTOR, Role.MANAGER, Role.ENGINEER)
            keys = {"tenant_id": actor["tenant_id"]}
            if actor["role"] == Role.CONTRACTOR:
                keys["contractor_id"] = actor["id"]
            if actor["role"] == Role.ENGINEER:
                keys["engineer_id"] = actor["id"]
            return [self._job_view(tx, job) for job in tx.find("jobs", **keys)]

    def get_job(self, token, job_id):
        with self.repository.transaction() as tx:
            actor = self._actor(tx, token, self._now())
            self._role(actor, Role.CONTRACTOR, Role.MANAGER, Role.ENGINEER)
            return self._job_view(tx, self._job(tx, actor, job_id))

    def create_case(self, token, data):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.MANAGER)
            job = self._job(tx, actor, data["job_id"])
            defaults = self._job_view(tx, job)
            version = data.get("policy_version") or defaults["policy_version"]
            if not tx.get("policies", tenant_id=actor["tenant_id"], job_id=job["id"], version=version):
                raise AppError(422, "POLICY_NOT_REVIEWED", "Choose an approved policy version for this job.")
            case = dict(id=uid(), tenant_id=actor["tenant_id"], job_id=job["id"], version=1,
                evidence_version=0, evidence_id=None, approval_id=None, challenge_id=None,
                policy_version=version, invoice_amount_paise=data.get("invoice_amount_paise") or defaults["invoice_amount_paise"])
            tx.add("cases", case)
            tx.add("case_workflow", dict(case_id=case["id"], tenant_id=case["tenant_id"], created_at=now, invoice_revision=1))
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
        upload, analysis = None, None
        if ev:
            upload, analysis, extracted = media_observation(tx, case, ev)
            if upload:
                observation = extracted
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
        if ev and not upload and (ev["artifact_mode"] != "SYNTHETIC" or not self.settings.allow_synthetic):
            result.update(max_permission=0, decision="DENY", inspection_status="REVIEW_REQUIRED",
                          reason_codes=["TEST_EVIDENCE_DISABLED"], guidance="Phase 01 accepts synthetic observations only in its internal test factory.")
        if upload:
            if upload["provider_mode"] == "MOCK_AI" and self.settings.provider_mode != "MOCK_AI":
                result.update(max_permission=0, decision="DENY", inspection_status="REVIEW_REQUIRED",
                    reason_codes=["MOCK_EVIDENCE_DISABLED"], guidance="Mock observations cannot authorize actions outside explicit mock mode.")
            elif not analysis:
                result.update(max_permission=0, decision="DENY", inspection_status="OBSERVATION_PENDING",
                    reason_codes=["OBSERVATION_PENDING"], guidance="Analysis is pending; no restricted action is eligible.")
            elif analysis["status"] != "SUCCESS":
                result.update(max_permission=0, decision="DENY", inspection_status="REVIEW_REQUIRED",
                    reason_codes=[analysis["reason_code"] or "PROVIDER_FAILED"], guidance="Analysis failed or became stale. Request review and submit new evidence with a current challenge.")
            elif result["inspection_status"] == "OBSERVATION_PENDING":
                result["inspection_status"] = "REVIEW_REQUIRED"
                result["guidance"] = "Resubmit legible required measurements or request human review; incomplete model observations cannot earn L2."
        rejection = self._rejected(tx, case, ev)
        if rejection:
            result.update(max_permission=0, decision="DENY", reason_codes=[*result["reason_codes"], "MANAGER_REJECTED_EVIDENCE", rejection["reason_code"]],
                          guidance="Manager rejected these evidence bytes. Request a fresh challenge and submit corrected new evidence.")
        return result, ev, challenge

    def _binding(self, case, job, ev, challenge, reviewer_id, reviewed_version):
        return dict(tenant_id=case["tenant_id"], case_id=case["id"], job_id=job["id"],
            asset_id=job["asset_id"], job_version=job["version"], contractor_id=job["contractor_id"],
            action=Action.COMPLETE_SIMULATED_ACTION.value, invoice_amount_paise=case["invoice_amount_paise"],
            evidence_sha256=ev["sha256"], evidence_version=case["evidence_version"],
            evidence_id=ev["id"], case_version=reviewed_version, policy_version=case["policy_version"],
            reviewer_id=reviewer_id, challenge_id=challenge["id"], evidence_session_id=challenge["evidence_session_id"],
            auth_session_id=challenge["auth_session_id"], challenge_expires_at=challenge["expires_at"])

    def _valid_approval(self, tx, case, job, result, ev, challenge):
        approval = tx.get("approvals", id=case["approval_id"], tenant_id=case["tenant_id"]) if case["approval_id"] else None
        if approval:
            reviewer = tx.get("users", id=approval["reviewer_id"], tenant_id=case["tenant_id"], active=True) if approval else None
            valid = bool(approval and reviewer and reviewer["role"] == Role.MANAGER and ev and challenge and
                reviewer["id"] != ev["submitted_by"] and result["max_permission"] == 2 and
                case["version"] == approval["effective_case_version"])
            if valid:
                binding = self._binding(case, job, ev, challenge, reviewer["id"], approval["reviewed_case_version"])
                valid = digest(binding) == approval["binding_sha256"] and canonical(binding) == approval["binding_json"]
            if valid:
                return approval
        return None

    def _refresh(self, tx, actor, case, job, now):
        result, ev, challenge = self._base(tx, case, job, now)
        if case["approval_id"]:
            if self._valid_approval(tx, case, job, result, ev, challenge):
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
        if ev:
            upload, analysis, extracted = media_observation(tx, case, ev)
            if upload:
                view.update(evidence_id=ev["id"], provider_mode=upload["provider_mode"],
                    analysis_status=analysis["status"] if analysis else "PENDING",
                    model_id=analysis["model_id"] if analysis else None,
                    model_version=analysis["model_version"] if analysis else None)
                if actor["role"] in {Role.MANAGER, Role.CONTRACTOR}:
                    view["observation"] = {k: v for k, v in (extracted or {}).items() if k != "challenge_text_observed"}
                    view["media"] = dict(mime_type=upload["mime_type"], width=upload["width"], height=upload["height"],
                        byte_size=upload["byte_size"], provenance=json.loads(upload["provenance_json"]))
        else:
            upload = None
        meta = tx.get("case_workflow", tenant_id=case["tenant_id"], case_id=case["id"])
        rejected = self._rejected(tx, case, ev)
        history = tx.recent("manager_reviews", {"tenant_id": case["tenant_id"], "case_id": case["id"]}, "effective_case_version", 1)
        fields = view.get("observation", {})
        missing = [name for name in ("asset_id_observed", "pressure_value", "pressure_unit", "equipment_status", "calibration_expiry_date") if fields.get(name) in (None, "UNKNOWN", "")]
        available = ["view_case", "view_audit"] if actor["role"] != Role.SERVICE_AGENT else []
        if actor["role"] == Role.CONTRACTOR:
            available += ["request_challenge", "submit_corrected_evidence"]
            if upload and not rejected:
                challenge = tx.get("challenges", id=case["challenge_id"])
                runs = tx.recent("analysis_runs", {"tenant_id": case["tenant_id"], "case_id": case["id"], "evidence_id": ev["id"]}, "started_case_version", 3)
                failed = analysis and analysis["status"] != "SUCCESS" and analysis["reason_code"] not in {"PROVIDER_INVALID_OBSERVATION", "PROVIDER_BLOCKED"}
                aged = not analysis and now >= (runs[0]["created_at"] if runs else upload["created_at"]) + self.settings.provider_timeout_seconds + 5
                if (failed or aged) and len(runs) < 3 and self._challenge_valid(tx, case, job, challenge, now) and challenge["auth_session_id"] == actor["session_id"] and self.settings.provider_mode == upload["provider_mode"]:
                    available.append("request_reanalysis")
        approval_eligible = bool(result["max_permission"] == 2 and result["decision"] == "ALLOW" and ev and ev["submitted_by"] != actor["id"] and actor["role"] == Role.MANAGER)
        if actor["role"] == Role.MANAGER:
            available += ["view_review", "change_invoice"]
            if approval_eligible: available.append("approve_simulation")
            if ev and not rejected and not completed: available.append("reject_evidence")
        for action in Action:
            try:
                if self._authorize_action(actor, action, result)["decision"] == "ALLOW": available.append(action.value)
            except AppError:
                pass
        view.update(evidence_id=ev["id"] if ev else None, contractor_id=job["contractor_id"],
            invoice_revision=meta["invoice_revision"] if meta else 1, created_at=meta["created_at"] if meta else None,
            submitted_at=upload["created_at"] if upload else None, processing_status=view.get("analysis_status", "NOT_SUBMITTED" if not ev else "COMPLETE"),
            business_status=project_business(case, result, bool(rejected), completed),
            review_state="REJECTED" if rejected else "APPROVED" if result["max_permission"] == 3 else "AWAITING_REVIEW" if result["max_permission"] == 2 else "CORRECTION_REQUIRED" if history and history[0]["decision"] == "REJECTED" else "NOT_REVIEWED",
            approval_eligible=approval_eligible, available_actions=sorted(set(available)),
            missing_fields=missing if actor["role"] in {Role.MANAGER, Role.CONTRACTOR} else [],
            uncertain_fields=fields.get("uncertain_fields", []) if actor["role"] in {Role.MANAGER, Role.CONTRACTOR} else [])
        view.setdefault("provider_mode", ev["artifact_mode"] if ev else None)
        view["last_review"] = {key: history[0][key] for key in ("id", "decision", "reviewer_id", "created_at", "evidence_version", "reviewed_case_version", "reason_code")} if history else None
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
                    self._event(tx, actor, case, "SIMULATED_ACTION_EXECUTED", now, action.value, "ALLOW", result["reason_codes"], completion_reference=receipt["id"])
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
            if self._valid_approval(tx, case, job, result, ev, ch):
                return {**self._view(tx, actor, case, job, now), "already_approved": True}
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
            review_id = uid()
            meta = tx.get("case_workflow", tenant_id=case["tenant_id"], case_id=case_id)
            tx.add("manager_reviews", dict(id=review_id, tenant_id=case["tenant_id"], case_id=case_id, decision="APPROVED",
                reviewer_id=actor["id"], created_at=now, reviewed_case_version=expected, effective_case_version=case["version"],
                evidence_id=ev["id"], evidence_version=ev["version"], evidence_sha256=ev["sha256"], policy_version=case["policy_version"],
                invoice_amount_paise=case["invoice_amount_paise"], invoice_revision=meta["invoice_revision"] if meta else 1,
                challenge_id=ch["id"], reason_code=None, internal_approval_id=approval["id"]))
            self._event(tx, actor, case, "MANAGER_APPROVED_SIMULATION", now,
                        Action.COMPLETE_SIMULATED_ACTION.value, "ALLOW", ["CURRENT_HUMAN_APPROVAL"], review_reference=review_id)
            return self._view(tx, actor, case, job, now)

    def change_invoice(self, token, case_id, expected, amount):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.MANAGER)
            case, job = self._case(tx, actor, case_id)
            self._version(case, expected)
            meta = tx.get("case_workflow", tenant_id=case["tenant_id"], case_id=case_id)
            tx.change("case_workflow", {"case_id": case_id, "tenant_id": case["tenant_id"]}, {"invoice_revision": meta["invoice_revision"] + 1})
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
            updated = {**job, "contractor_id": contractor_id, "version": expected + 1}
            self._job_event(tx, actor, updated, "CONTRACTOR_REASSIGNED", now)
            return self._job_view(tx, updated)

    def audit(self, token, case_id, limit=100, before=None, event_type=None):
        with self.repository.transaction() as tx:
            now = self._now()
            actor = self._actor(tx, token, now)
            self._role(actor, Role.CONTRACTOR, Role.MANAGER, Role.ENGINEER)
            case, job = self._case(tx, actor, case_id)
            case, result = self._refresh(tx, actor, case, job, now)
            self._event(tx, actor, case, "AUDIT_READ", now)
            rows = tx.audit_page(actor["tenant_id"], case_id, before, event_type, limit)
            return [{k: v for k, v in row.items() if k != "reason_codes_json"} | {"reason_codes": json.loads(row["reason_codes_json"])} for row in rows]
