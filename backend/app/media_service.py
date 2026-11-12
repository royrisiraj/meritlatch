"""Authenticated two-phase intake; provider work never holds a DB transaction."""

import asyncio
from hashlib import sha256
import json
import re
from time import monotonic

from .api_models import Role
from .case_service import canonical, uid
from .errors import AppError, not_found
from .media import validate_image
from .perception import PerceptionInput, VisualObservation, ProviderError
from .media_state import media_observation

PROVIDER_CODES = {"PROVIDER_TIMEOUT", "PROVIDER_QUOTA", "PROVIDER_AUTH", "PROVIDER_UNAVAILABLE",
                  "PROVIDER_FAILED", "PROVIDER_INVALID_OBSERVATION", "PROVIDER_BLOCKED"}


class MediaService:
    def __init__(self, cases, provider, storage):
        self.cases = cases
        self.settings = cases.settings
        self.provider = provider
        self.storage = storage

    def gate(self, token, case_id):
        with self.cases.repository.transaction() as tx:
            actor = self.cases._actor(tx, token, self.cases._now())
            self.cases._role(actor, Role.CONTRACTOR)
            self.cases._case(tx, actor, case_id)
            if not self.provider:
                raise AppError(404, "EVIDENCE_INTAKE_DISABLED", "Configure an explicit perception mode before submitting images.")

    def _checked(self, tx, token, case_id, expected, challenge_id, evidence_session_id, check_version=True):
        now = self.cases._now()
        actor = self.cases._actor(tx, token, now)
        self.cases._role(actor, Role.CONTRACTOR)
        case, job = self.cases._case(tx, actor, case_id)
        if check_version:
            self.cases._version(case, expected)
        challenge = tx.get("challenges", id=case["challenge_id"], tenant_id=case["tenant_id"], case_id=case_id)
        if not self.cases._challenge_valid(tx, case, job, challenge, now) or challenge["id"] != challenge_id or challenge["evidence_session_id"] != evidence_session_id or challenge["auth_session_id"] != actor["session_id"]:
            raise AppError(409, "CHALLENGE_INVALID", "Request a fresh challenge in this authenticated contractor session.")
        if tx.get("manager_reviews", tenant_id=case["tenant_id"], case_id=case_id, decision="REJECTED", challenge_id=challenge_id):
            raise AppError(409, "FRESH_CHALLENGE_REQUIRED", "Manager rejection requires a fresh challenge and corrected new evidence.")
        return actor, case, job, challenge, now

    def _operation_response(self, tx, actor, case, job, now):
        case, decision = self.cases._refresh(tx, actor, case, job, now)
        view = self.cases._view(tx, actor, case, job, now, decision)
        view["operation_replayed"] = True
        status = 202 if view.get("analysis_status") == "PENDING" else 504 if "PROVIDER_TIMEOUT" in view["reason_codes"] else 502 if view.get("analysis_status") == "FAILED" else 200
        self.cases._event(tx, actor, case, "EVIDENCE_OPERATION_REPLAYED", now, decision=decision["decision"], reasons=decision["reason_codes"])
        return status, view

    def _submission_replay(self, tx, checked, expected, challenge_id, session_id, key, fingerprint, declared):
        actor, case, job, challenge, now = checked
        if key:
            operation = tx.get("submission_operations", tenant_id=case["tenant_id"], actor_id=actor["id"], key_hash=sha256(key.encode()).hexdigest())
            if operation:
                if (operation["case_id"], operation["auth_session_id"], operation["challenge_id"], operation["evidence_session_id"], operation["expected_case_version"], operation["request_sha256"], operation["declared_type"]) != (case["id"], actor["session_id"], challenge_id, session_id, expected, fingerprint, declared):
                    raise AppError(409, "IDEMPOTENCY_CONFLICT", "This operation key is already bound to a different request or authenticated session.")
                if case["evidence_id"] != operation["evidence_id"]:
                    raise AppError(409, "OPERATION_SUPERSEDED", "Newer evidence replaced this operation. Reload the current case.")
                return self._operation_response(tx, actor, case, job, now)
        self.cases._version(case, expected)
        return None

    def preflight(self, token, case_id, expected, challenge_id, evidence_session_id, operation_key=None, fingerprint=None, declared=None):
        if not self.provider:
            raise AppError(404, "EVIDENCE_INTAKE_DISABLED", "Configure an explicit perception mode before submitting images.")
        with self.cases.repository.transaction() as tx:
            checked = self._checked(tx, token, case_id, expected, challenge_id, evidence_session_id, check_version=not operation_key)
            return self._submission_replay(tx, checked, expected, challenge_id, evidence_session_id, operation_key, fingerprint, declared)

    def _accept(self, token, case_id, expected, challenge_id, evidence_session_id, image, operation_key=None, declared=None):
        key = None
        try:
            with self.cases.repository.transaction() as tx:
                checked = self._checked(tx, token, case_id, expected, challenge_id, evidence_session_id, check_version=not operation_key)
                replay = self._submission_replay(tx, checked, expected, challenge_id, evidence_session_id, operation_key, image.sha256, declared)
                if replay:
                    return {"replayed_response": replay}
                actor, case, job, challenge, now = checked
                if tx.get("media_uploads", tenant_id=case["tenant_id"], sha256=image.sha256):
                    raise AppError(409, "EXACT_DUPLICATE", "These exact bytes already exist in this tenant. Request review; duplication alone is not proof of fraud.")
                key = self.storage.put(image.original)
                blank = dict(artifact_mode=self.provider.mode, asset_id_observed=None, challenge_text_observed=None,
                    pressure_value=None, pressure_unit=None, equipment_status="UNKNOWN", calibration_expiry_date=None, uncertain_fields=[])
                ev = dict(id=uid(), tenant_id=case["tenant_id"], case_id=case_id, challenge_id=challenge["id"],
                    version=case["evidence_version"] + 1, sha256=image.sha256, observation_json=canonical(blank),
                    artifact_mode=self.provider.mode, submitted_by=actor["id"])
                tx.add("evidence", ev)
                case = tx.cas_case(case, expected, dict(evidence_id=ev["id"], evidence_version=ev["version"], approval_id=None))
                upload = dict(id=uid(), tenant_id=case["tenant_id"], case_id=case_id, evidence_id=ev["id"],
                    storage_key=key, sha256=image.sha256, provider_sha256=image.provider_sha256, mime_type=image.mime_type,
                    byte_size=len(image.original), width=image.width, height=image.height,
                    provenance_json=canonical(image.provenance), provider_mode=self.provider.mode,
                    accepted_case_version=case["version"], created_at=now)
                tx.add("media_uploads", upload)
                if operation_key:
                    tx.add("submission_operations", dict(id=uid(), tenant_id=case["tenant_id"], case_id=case_id, actor_id=actor["id"],
                        auth_session_id=actor["session_id"], key_hash=sha256(operation_key.encode()).hexdigest(), request_sha256=image.sha256,
                        declared_type=declared, challenge_id=challenge_id, evidence_session_id=evidence_session_id,
                        expected_case_version=expected, evidence_id=ev["id"], created_at=now))
                self.cases._event(tx, actor, case, "IMAGE_ACCEPTED", now, reasons=["OBSERVATION_PENDING", "APPROVAL_INVALIDATED"])
                reservation = dict(upload=upload, evidence=ev, actor_id=actor["id"],
                                   challenge_id=challenge_id, evidence_session_id=evidence_session_id)
            return reservation
        except BaseException:
            if key:
                self.storage.discard_uncommitted(key)
            raise

    def _finish(self, token, reservation, observation, model_version, elapsed, error):
        upload, ev = reservation["upload"], reservation["evidence"]
        with self.cases.repository.transaction() as tx:
            now = self.cases._now()
            case = tx.get("cases", id=upload["case_id"], tenant_id=upload["tenant_id"])
            job = tx.get("jobs", id=case["job_id"], tenant_id=case["tenant_id"])
            stale, http_status = None, 200
            try:
                actor = self.cases._actor(tx, token, now)
                self.cases._role(actor, Role.CONTRACTOR)
                self.cases._job(tx, actor, job["id"])
            except AppError as exc:
                stale, http_status = "ANALYSIS_AUTHORIZATION_CHANGED", exc.status
                actor = {"id": reservation["actor_id"]}
            challenge = tx.get("challenges", id=case["challenge_id"], tenant_id=case["tenant_id"], case_id=case["id"])
            if not stale and (case["version"] != upload["accepted_case_version"] or case["evidence_id"] != ev["id"] or case["evidence_version"] != ev["version"] or case["challenge_id"] != reservation["challenge_id"] or not self.cases._challenge_valid(tx, case, job, challenge, now) or challenge["evidence_session_id"] != reservation["evidence_session_id"]):
                stale, http_status = "ANALYSIS_STALE", 409
            reason = stale or error
            record = dict(id=uid(), tenant_id=case["tenant_id"], case_id=case["id"], evidence_id=ev["id"],
                status="STALE" if stale else "FAILED" if error else "SUCCESS", observation_json=observation.model_dump_json() if observation is not None and not reason else None,
                reason_code=reason, model_id=self.provider.model_id, model_version=model_version,
                elapsed_seconds=elapsed, created_at=now)
            if reservation.get("run_id"):
                tx.add("analysis_results", {**record, "run_id": reservation["run_id"]})
            else:
                tx.add("media_analyses", record)
            if stale:
                self.cases._event(tx, actor, case, "ANALYSIS_DISCARDED", now, decision="DENY", reasons=[stale], source_evidence=ev)
                return http_status, dict(decision="DENY", reason_codes=[stale], guidance="Current state or challenge changed during analysis. Reload state and submit fresh evidence.")
            case = tx.cas_case(case, upload["accepted_case_version"], {"approval_id": None})
            self.cases._event(tx, actor, case, "ANALYSIS_FAILED" if error else "ANALYSIS_COMPLETED", now,
                              decision="DENY" if error else None, reasons=[error] if error else [])
            view = self.cases._view(tx, actor, case, job, now)
            view["analysis_elapsed_seconds"] = elapsed
            return (504 if error == "PROVIDER_TIMEOUT" else 502 if error else 200), view

    async def submit(self, token, case_id, expected, challenge_id, evidence_session_id, data, declared_type, operation_key=None):
        declared = declared_type.split(";", 1)[0].strip().lower()
        replay = await asyncio.to_thread(self.preflight, token, case_id, expected, challenge_id, evidence_session_id,
                                        operation_key, sha256(data).hexdigest(), declared)
        if replay:
            return replay
        image = await asyncio.to_thread(validate_image, data, declared_type, self.settings)
        reservation = await asyncio.to_thread(self._accept, token, case_id, expected, challenge_id, evidence_session_id, image, operation_key, declared)
        if "replayed_response" in reservation:
            return reservation["replayed_response"]
        return await self._analyze(token, reservation, image)

    async def _analyze(self, token, reservation, image):
        started = monotonic()
        observation, model_version, error = None, None, None
        try:
            async with asyncio.timeout(self.settings.provider_timeout_seconds):
                result = await self.provider.inspect(PerceptionInput(image.provider_bytes, "image/png", reservation["evidence"]["id"]))
            fields = VisualObservation.model_validate(result.fields)
            observation = fields.observation(self.provider.mode)
            if isinstance(result.model_version, str) and re.fullmatch(r"[A-Za-z0-9._/-]{1,100}", result.model_version):
                model_version = result.model_version
        except TimeoutError:
            error = "PROVIDER_TIMEOUT"
        except ProviderError as exc:
            error = exc.code if exc.code in PROVIDER_CODES else "PROVIDER_FAILED"
        except (ValueError, TypeError, AttributeError):
            error = "PROVIDER_INVALID_OBSERVATION"
        except Exception:
            error = "PROVIDER_FAILED"
        # Never log provider payloads/exceptions. A cancelled process/request leaves
        # a pending, non-authorizing reservation; no background callback grants it.
        return await asyncio.to_thread(self._finish, token, reservation, observation, model_version, monotonic() - started, error)

    def _start_reanalysis(self, token, case_id, evidence_id, expected, key, allow_billable):
        with self.cases.repository.transaction() as tx:
            now = self.cases._now()
            actor = self.cases._actor(tx, token, now)
            self.cases._role(actor, Role.CONTRACTOR)
            case, job = self.cases._case(tx, actor, case_id)
            if not self.provider:
                raise AppError(404, "EVIDENCE_INTAKE_DISABLED", "Configure a perception provider first.")
            if case["evidence_id"] != evidence_id:
                raise not_found()
            ev = tx.get("evidence", id=evidence_id, tenant_id=case["tenant_id"], case_id=case_id)
            challenge = tx.get("challenges", id=case["challenge_id"], tenant_id=case["tenant_id"], case_id=case_id)
            if not self.cases._challenge_valid(tx, case, job, challenge, now) or challenge["auth_session_id"] != actor["session_id"] or ev["challenge_id"] != challenge["id"]:
                raise AppError(409, "CHALLENGE_INVALID", "Reanalysis requires the original current challenge and authenticated evidence session.")
            if self.cases._rejected(tx, case, ev):
                raise AppError(409, "NEW_EVIDENCE_REQUIRED", "Rejected evidence cannot be reanalyzed into approval. Request a fresh challenge and submit corrected evidence.")
            upload, analysis, observation = media_observation(tx, case, ev)
            if not upload or upload["provider_mode"] != self.provider.mode:
                raise AppError(409, "PROVIDER_MODE_MISMATCH", "Reanalysis cannot change evidence provenance or fall back to a different mode.")
            known = tx.get("analysis_runs", tenant_id=case["tenant_id"], actor_id=actor["id"], key_hash=sha256(key.encode()).hexdigest())
            if known:
                if (known["case_id"], known["evidence_id"], known["auth_session_id"], known["expected_case_version"]) != (case_id, evidence_id, actor["session_id"], expected):
                    raise AppError(409, "IDEMPOTENCY_CONFLICT", "This reanalysis key is bound to a different request/session.")
                latest = tx.recent("analysis_runs", {"case_id": case_id, "tenant_id": case["tenant_id"], "evidence_id": evidence_id}, "started_case_version", 1)
                if latest[0]["id"] != known["id"]:
                    raise AppError(409, "OPERATION_SUPERSEDED", "A newer analysis attempt superseded this operation.")
                return {"replayed_response": self._operation_response(tx, actor, case, job, now)}
            self.cases._version(case, expected)
            runs = tx.recent("analysis_runs", {"tenant_id": case["tenant_id"], "case_id": case_id, "evidence_id": evidence_id}, "started_case_version", 4)
            if len(runs) >= 3:
                raise AppError(429, "REANALYSIS_LIMIT", "This evidence has reached its three explicit retries. Request review or submit new evidence.")
            if analysis and (analysis["status"] == "SUCCESS" or analysis["reason_code"] in {"PROVIDER_INVALID_OBSERVATION", "PROVIDER_BLOCKED"}):
                raise AppError(409, "NEW_EVIDENCE_REQUIRED", "Interpreted or semantically invalid evidence needs correction, not repeated inference on identical bytes.")
            started = runs[0]["created_at"] if runs else upload["created_at"]
            if not analysis and now < started + self.settings.provider_timeout_seconds + 5:
                raise AppError(409, "ANALYSIS_IN_PROGRESS", "The attempt may still be running. Wait until its deadline and recovery grace have elapsed.")
            if self.provider.mode == "LIVE_GEMINI" and not allow_billable:
                raise AppError(403, "BILLABLE_REANALYSIS_NOT_APPROVED", "A live retry needs explicit per-request billable-call approval.")
            data = self.storage.read(upload["storage_key"], self.settings.max_image_bytes)
            if sha256(data).hexdigest() != ev["sha256"]:
                raise AppError(503, "MEDIA_INTEGRITY_ERROR", "Stored bytes changed; request operator review rather than reanalysis.")
            image = validate_image(data, upload["mime_type"], self.settings)
            run = dict(id=uid(), tenant_id=case["tenant_id"], case_id=case_id, evidence_id=evidence_id,
                actor_id=actor["id"], auth_session_id=actor["session_id"], key_hash=sha256(key.encode()).hexdigest(),
                expected_case_version=expected, started_case_version=expected + 1, provider_mode=self.provider.mode,
                model_id=self.provider.model_id, created_at=now)
            tx.add("analysis_runs", run)
            case = tx.cas_case(case, expected, {"approval_id": None})
            self.cases._event(tx, actor, case, "REANALYSIS_STARTED", now, decision="DENY", reasons=["OBSERVATION_PENDING"])
            return dict(upload={**upload, "accepted_case_version": case["version"]}, evidence=ev, actor_id=actor["id"],
                        challenge_id=challenge["id"], evidence_session_id=challenge["evidence_session_id"], run_id=run["id"], image=image)

    async def reanalyze(self, token, case_id, evidence_id, expected, key, allow_billable=False):
        reservation = await asyncio.to_thread(self._start_reanalysis, token, case_id, evidence_id, expected, key, allow_billable)
        if "replayed_response" in reservation:
            return reservation["replayed_response"]
        return await self._analyze(token, reservation, reservation["image"])

    def content(self, token, case_id, evidence_id):
        with self.cases.repository.transaction() as tx:
            now = self.cases._now()
            actor = self.cases._actor(tx, token, now)
            self.cases._role(actor, Role.CONTRACTOR, Role.MANAGER)
            case, job = self.cases._case(tx, actor, case_id)
            if case["evidence_id"] != evidence_id:
                raise not_found()
            upload = tx.get("media_uploads", tenant_id=case["tenant_id"], case_id=case_id, evidence_id=evidence_id)
            if not upload:
                raise not_found()
            data = self.storage.read(upload["storage_key"], self.settings.max_image_bytes)
            if sha256(data).hexdigest() != upload["sha256"]:
                raise AppError(503, "MEDIA_INTEGRITY_ERROR", "Stored bytes differ from the accepted digest; request operator review.")
            self.cases._event(tx, actor, case, "PRIVATE_MEDIA_READ", now)
            return data, upload["mime_type"]
