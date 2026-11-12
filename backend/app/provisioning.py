"""Offline trusted-operator functions. No HTTP access or model tools."""

from datetime import datetime, timezone, timedelta
import json
import secrets

from .api_models import Role
from .auth import hash_password
from .case_service import uid
from .errors import AppError, forbidden
from .models import Policy, Observation, EvaluationContext, Action
from .policy import authorize


def provision_user(repository, tenant_id, username, role, password):
    role = Role(role)
    if not tenant_id.strip() or not username.strip() or len(tenant_id) > 100 or len(username) > 100:
        raise ValueError("Tenant and username must be nonblank and at most 100 characters.")
    password_hash = hash_password(password)
    with repository.transaction() as tx:
        if not tx.get("tenants", id=tenant_id):
            tx.add("tenants", {"id": tenant_id})
        if tx.get("users", tenant_id=tenant_id, username=username):
            raise ValueError("Account already exists; credentials were not overwritten.")
        user = dict(id=uid(), tenant_id=tenant_id, username=username, role=role.value,
                    password_hash=password_hash, active=True)
        tx.add("users", user)
        return {k: user[k] for k in ("id", "tenant_id", "username", "role")}


def policy_regression_guard(policy: Policy):
    """Small structural regression guard, not Phase 04 adversarial certification."""
    policy = Policy.model_validate(policy)
    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    ctx = EvaluationContext(tenant_id=policy.tenant_id, job_id=policy.job_id,
        asset_id_expected=policy.asset_id_expected, approved_policy_version=policy.version,
        expected_challenge=token, challenge_expires_at=now + timedelta(minutes=5), evaluated_at=now)
    obs = Observation(artifact_mode="SYNTHETIC", asset_id_observed=policy.asset_id_expected,
        challenge_text_observed=token, pressure_value=(policy.pressure_min + policy.pressure_max) / 2,
        pressure_unit=policy.pressure_unit, equipment_status=policy.required_equipment_status,
        calibration_expiry_date=now.date())
    valid = authorize(obs, policy, ctx)
    unsafe = authorize(obs.model_copy(update={"pressure_value": policy.pressure_max + max(1.0, policy.pressure_max)}), policy, ctx)
    checks = [valid.max_permission == 2, valid.decision.value == "ALLOW",
        authorize(None, policy, ctx).max_permission == 0,
        authorize(obs, policy, ctx, Action.COMPLETE_SIMULATED_ACTION).decision.value == "DENY",
        unsafe.inspection_status.value == "SAFETY_ALERT", unsafe.max_permission < 2,
        authorize(obs.model_copy(update={"pressure_unit": "UNKNOWN"}), policy, ctx).max_permission < 2,
        authorize(obs.model_copy(update={"uncertain_fields": ("pressure_value",)}), policy, ctx).max_permission < 2]
    if not all(checks):
        raise ValueError("Candidate policy failed the structural regression guard.")


def register_reviewed_policy(service, author_token, reviewer_token, policy, review_reference):
    """Two independently authenticated engineers register, never auto-activate, a version."""
    policy = Policy.model_validate(policy)
    if not review_reference.strip() or len(review_reference) > 300:
        raise ValueError("Supply a restricted engineering review reference (1–300 characters).")
    policy_regression_guard(policy)
    with service.repository.transaction() as tx:
        now = service._now()
        author = service._actor(tx, author_token, now)
        reviewer = service._actor(tx, reviewer_token, now)
        if author["role"] != Role.ENGINEER or reviewer["role"] != Role.ENGINEER:
            raise forbidden()
        if author["id"] == reviewer["id"] or author["tenant_id"] != reviewer["tenant_id"] or policy.tenant_id != author["tenant_id"]:
            raise AppError(403, "INDEPENDENT_ENGINEERING_REVIEW_REQUIRED", "Use two separate engineering accounts in this tenant.")
        job = service._job(tx, author, policy.job_id)
        if policy.asset_id_expected != job["asset_id"] or policy.policy_id != service.template.policy_id:
            raise ValueError("Reviewed policy must match this job's authoritative asset and policy family.")
        if tx.get("policies", tenant_id=policy.tenant_id, job_id=policy.job_id, version=policy.version):
            raise AppError(409, "POLICY_VERSION_EXISTS", "Register a new version; existing policy versions are append-only.")
        row = dict(id=uid(), tenant_id=policy.tenant_id, job_id=policy.job_id, version=policy.version,
            config_json=policy.model_dump_json(), author_id=author["id"], reviewer_id=reviewer["id"],
            review_reference=review_reference)
        tx.add("policies", row)
        return {"policy_version": policy.version, "activated": False, "structural_regression": "passed"}
