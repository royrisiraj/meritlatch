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

    def _checked(self, tx, token, case_id, expected, challenge_id, evidence_session_id):
        now = self.cases._now()
        actor = self.cases._actor(tx, token, now)
        self.cases._role(actor, Role.CONTRACTOR)
        case, job = self.cases._case(tx, actor, case_id)
        self.cases._version(case, expected)
        challenge = tx.get("challenges", id=case["challenge_id"], tenant_id=case["tenant_id"], case_id=case_id)
        if not self.cases._challenge_valid(tx, case, job, challenge, now) or challenge["id"] != challenge_id or challenge["evidence_session_id"] != evidence_session_id or challenge["auth_session_id"] != actor["session_id"]:
            raise AppError(409, "CHALLENGE_INVALID", "Request a fresh challenge in this authenticated contractor session.")
        return actor, case, job, challenge, now

    def preflight(self, token, case_id, expected, challenge_id, evidence_session_id):
        if not self.provider:
            raise AppError(404, "EVIDENCE_INTAKE_DISABLED", "Configure an explicit perception mode before submitting images.")
        with self.cases.repository.transaction() as tx:
            self._checked(tx, token, case_id, expected, challenge_id, evidence_session_id)

    def _accept(self, token, case_id, expected, challenge_id, evidence_session_id, image):
        key = None
        try:
            with self.cases.repository.transaction() as tx:
                actor, case, job, challenge, now = self._checked(tx, token, case_id, expected, challenge_id, evidence_session_id)
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
            tx.add("media_analyses", dict(id=uid(), tenant_id=case["tenant_id"], case_id=case["id"], evidence_id=ev["id"],
                status="STALE" if stale else "FAILED" if error else "SUCCESS", observation_json=observation.model_dump_json() if observation is not None and not reason else None,
                reason_code=reason, model_id=self.provider.model_id, model_version=model_version,
                elapsed_seconds=elapsed, created_at=now))
            if stale:
                self.cases._event(tx, actor, case, "ANALYSIS_DISCARDED", now, decision="DENY", reasons=[stale])
                return http_status, dict(decision="DENY", reason_codes=[stale], guidance="Current state or challenge changed during analysis. Reload state and submit fresh evidence.")
            case = tx.cas_case(case, upload["accepted_case_version"], {"approval_id": None})
            self.cases._event(tx, actor, case, "ANALYSIS_FAILED" if error else "ANALYSIS_COMPLETED", now,
                              decision="DENY" if error else None, reasons=[error] if error else [])
            view = self.cases._view(tx, actor, case, job, now)
            view["analysis_elapsed_seconds"] = elapsed
            return (504 if error == "PROVIDER_TIMEOUT" else 502 if error else 200), view

    async def submit(self, token, case_id, expected, challenge_id, evidence_session_id, data, declared_type):
        await asyncio.to_thread(self.preflight, token, case_id, expected, challenge_id, evidence_session_id)
        image = await asyncio.to_thread(validate_image, data, declared_type, self.settings)
        reservation = await asyncio.to_thread(self._accept, token, case_id, expected, challenge_id, evidence_session_id, image)
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
