"""Pure deterministic decision point: no I/O, clock, API, provider or storage imports."""

from collections.abc import Mapping
from datetime import timezone
from typing import Any

from pydantic import ValidationError

from .models import (
    Action, Decision, EvaluationContext, InspectionStatus as Status, Observation,
    Outcome, Permission, Policy, Reason,
)


REQUIRED_PERMISSION = {
    Action.CREATE_DRAFT: Permission.L0,
    Action.REQUEST_EVIDENCE: Permission.L0,
    Action.RECORD_PROVISIONAL_VISIT: Permission.L1,
    Action.PREPARE_INVOICE: Permission.L2,
    Action.COMPLETE_SIMULATED_ACTION: Permission.L3,
}


def _invalid(reason: Reason) -> Decision:
    return Decision(
        decision=Outcome.DENY, inspection_status=Status.REVIEW_REQUIRED,
        max_permission=Permission.L0, reason_codes=(reason,),
        guidance="Correct the input or configuration and retry; no restricted action is permitted.",
    )


def authorize(
    observation: Observation | Mapping[str, Any] | None,
    policy: Policy | Mapping[str, Any],
    context: EvaluationContext | Mapping[str, Any],
    action: Action | str = Action.PREPARE_INVOICE,
) -> Decision:
    """Evaluate evidence eligibility only. This is not actor/job authorization.

    Phase 00 has no human approval path and therefore cannot grant L3.
    Revalidation also catches unchecked Pydantic model_copy/model_construct inputs.
    """
    try:
        try:
            validated_policy = Policy.model_validate(policy)
        except (ValidationError, ValueError, TypeError):
            return _invalid(Reason.INVALID_POLICY)
        try:
            validated_context = EvaluationContext.model_validate(context)
        except (ValidationError, ValueError, TypeError):
            return _invalid(Reason.INVALID_CONTEXT)
        try:
            requested_action = Action(action)
        except (ValueError, TypeError):
            return _invalid(Reason.INVALID_INPUT)
        try:
            validated_observation = None if observation is None else Observation.model_validate(observation)
        except (ValidationError, ValueError, TypeError):
            return _invalid(Reason.INVALID_OBSERVATION)
        return _evaluate(validated_observation, validated_policy, validated_context, requested_action)
    except Exception:
        # Do not log untrusted values or expose exception text. No exception grants access.
        return _invalid(Reason.INTERNAL_ERROR)


def _evaluate(obs: Observation | None, policy: Policy, ctx: EvaluationContext, action: Action) -> Decision:
    if (policy.tenant_id, policy.job_id, policy.asset_id_expected, policy.version) != (
        ctx.tenant_id, ctx.job_id, ctx.asset_id_expected, ctx.approved_policy_version
    ):
        return _invalid(Reason.POLICY_CONTEXT_MISMATCH)

    tier = Permission.L0
    status = Status.EVIDENCE_MISSING
    reasons: list[Reason] = []
    if obs is None:
        reasons.append(Reason.OBSERVATION_MISSING)
    else:
        if obs.asset_id_observed != ctx.asset_id_expected:
            reasons.append(Reason.ASSET_MISMATCH)
        if obs.challenge_text_observed != ctx.expected_challenge:
            reasons.append(Reason.CHALLENGE_MISMATCH)
        if ctx.evaluated_at >= ctx.challenge_expires_at:
            reasons.append(Reason.CHALLENGE_EXPIRED)
        identity_valid = not reasons
        if identity_valid:
            tier = Permission.L1
            status = Status.OBSERVATION_PENDING

        missing = False
        review = False
        unsafe = False
        if obs.uncertain_fields:
            reasons.append(Reason.UNCERTAIN_OBSERVATION)
            review = True
            # Uncertainty in identity prevents even provisional progression.
            if {"asset_id_observed", "challenge_text_observed"} & set(obs.uncertain_fields):
                tier = Permission.L0
        if obs.pressure_value is None:
            reasons.append(Reason.PRESSURE_MISSING)
            missing = True
        if obs.pressure_unit != policy.pressure_unit:
            reasons.append(Reason.UNIT_UNSUPPORTED)
            review = True
        elif obs.pressure_value is not None:
            value = obs.pressure_value
            low = value < policy.pressure_min if policy.minimum_inclusive else value <= policy.pressure_min
            high = value > policy.pressure_max if policy.maximum_inclusive else value >= policy.pressure_max
            if low or high:
                reasons.append(Reason.PRESSURE_OUT_OF_RANGE)
                unsafe = True
        if obs.equipment_status in (None, "UNKNOWN"):
            reasons.append(Reason.EQUIPMENT_STATUS_MISSING)
            missing = True
        elif obs.equipment_status != policy.required_equipment_status:
            reasons.append(Reason.EQUIPMENT_STATUS_MISMATCH)
            review = True
        if obs.calibration_expiry_date is None:
            reasons.append(Reason.CALIBRATION_MISSING)
            missing = True
        elif obs.calibration_expiry_date < ctx.evaluated_at.astimezone(timezone.utc).date():
            reasons.append(Reason.CALIBRATION_EXPIRED)
            unsafe = True

        if unsafe:
            status = Status.SAFETY_ALERT
        elif review:
            status = Status.REVIEW_REQUIRED
        elif identity_valid and not missing:
            tier = Permission.L2
            status = Status.EVIDENCE_COMPLETE
            reasons.append(Reason.EVIDENCE_SATISFIES_POLICY)

    if action == Action.COMPLETE_SIMULATED_ACTION:
        outcome = Outcome.DENY
        reasons.append(Reason.HUMAN_APPROVAL_NOT_IMPLEMENTED)
    elif REQUIRED_PERMISSION[action] <= tier:
        outcome = Outcome.ALLOW
    else:
        outcome = Outcome.NEEDS_REVIEW if status in (Status.SAFETY_ALERT, Status.REVIEW_REQUIRED) else Outcome.DENY
        reasons.append(Reason.PERMISSION_INSUFFICIENT)
    guidance = {
        Status.EVIDENCE_MISSING: "Provide matching asset evidence and a current server-issued challenge.",
        Status.OBSERVATION_PENDING: "Resubmit the missing legible measurements, unit, status and calibration date.",
        Status.EVIDENCE_COMPLETE: "Prepare the simulated invoice for human review; completion is unavailable in Phase 00.",
        Status.SAFETY_ALERT: "Stop invoice progression and request qualified safety review; do not infer safe operation.",
        Status.REVIEW_REQUIRED: "Request review and replace conflicting or uncertain observations.",
    }[status]
    return Decision(decision=outcome, inspection_status=status, max_permission=tier,
                    reason_codes=tuple(reasons), guidance=guidance)
