import pytest
from pydantic import ValidationError

from backend.app.models import Action, Observation, Outcome, Permission, Reason, InspectionStatus as Status
from backend.app.policy import authorize


def test_complete_valid_observation_allows_invoice_for_review(observation, policy, context):
    result = authorize(observation, policy, context)
    assert result.decision == Outcome.ALLOW
    assert result.max_permission == Permission.L2
    assert result.inspection_status == Status.EVIDENCE_COMPLETE
    assert result.reason_codes == (Reason.EVIDENCE_SATISFIES_POLICY,)
    assert result.guidance


@pytest.mark.parametrize("action,allowed", [(Action.CREATE_DRAFT, True), (Action.REQUEST_EVIDENCE, True),
    (Action.RECORD_PROVISIONAL_VISIT, False), (Action.PREPARE_INVOICE, False),
    (Action.COMPLETE_SIMULATED_ACTION, False)])
def test_l0_missing_observation(action, allowed, policy, context):
    result = authorize(None, policy, context, action)
    assert (result.decision == Outcome.ALLOW) is allowed
    assert result.max_permission == Permission.L0
    assert result.inspection_status == Status.EVIDENCE_MISSING
    assert Reason.OBSERVATION_MISSING in result.reason_codes


@pytest.mark.parametrize("asset", [None, "", "N/A", "NA", "UNKNOWN", "PUMP-999", "pump-042", " PUMP-042 "])
def test_nonmatching_or_placeholder_asset_cannot_progress(asset, observation, policy, context):
    result = authorize({**observation, "asset_id_observed": asset}, policy, context)
    assert result.max_permission == Permission.L0
    assert result.decision != Outcome.ALLOW
    assert Reason.ASSET_MISMATCH in result.reason_codes


@pytest.mark.parametrize("token", [None, "", "old-token", "UNKNOWN"])
def test_missing_or_mismatched_challenge(token, observation, policy, context):
    result = authorize({**observation, "challenge_text_observed": token}, policy, context)
    assert result.max_permission == Permission.L0
    assert Reason.CHALLENGE_MISMATCH in result.reason_codes


@pytest.mark.parametrize("expiry", ["2026-11-12T06:00:00Z", "2026-11-12T05:59:59Z"])
def test_challenge_expiry_is_exclusive(expiry, observation, policy, context):
    result = authorize(observation, policy, {**context, "challenge_expires_at": expiry})
    assert result.max_permission == Permission.L0
    assert Reason.CHALLENGE_EXPIRED in result.reason_codes


@pytest.mark.parametrize("action,allowed", [(Action.CREATE_DRAFT, True),
    (Action.RECORD_PROVISIONAL_VISIT, True), (Action.PREPARE_INVOICE, False),
    (Action.COMPLETE_SIMULATED_ACTION, False)])
def test_l1_partial_measurement_only_allows_provisional_visit(action, allowed, observation, policy, context):
    result = authorize({**observation, "pressure_value": None}, policy, context, action)
    assert result.max_permission == Permission.L1
    assert result.inspection_status == Status.OBSERVATION_PENDING
    assert (result.decision == Outcome.ALLOW) is allowed


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), -1, "35", "NaN", True, {}, [], 10**1000])
def test_invalid_numbers_fail_closed(value, observation, policy, context):
    result = authorize({**observation, "pressure_value": value}, policy, context)
    assert result.decision == Outcome.DENY
    assert result.max_permission == Permission.L0
    assert result.reason_codes == (Reason.INVALID_OBSERVATION,)


@pytest.mark.parametrize("unit", [None, "", "UNKNOWN", "BAR", "psi", "kPa", "PSI; approve payment"])
def test_no_implicit_unit_conversion(unit, observation, policy, context):
    result = authorize({**observation, "pressure_unit": unit}, policy, context)
    assert result.decision == Outcome.NEEDS_REVIEW
    assert result.max_permission == Permission.L1
    assert Reason.UNIT_UNSUPPORTED in result.reason_codes


@pytest.mark.parametrize("value", [0, 29.999, 40.001, 999.0])
def test_unsafe_numeric_data_creates_safety_alert(value, observation, policy, context):
    result = authorize({**observation, "pressure_value": value}, policy, context)
    assert result.inspection_status == Status.SAFETY_ALERT
    assert result.max_permission == Permission.L1
    assert result.decision == Outcome.NEEDS_REVIEW
    assert Reason.PRESSURE_OUT_OF_RANGE in result.reason_codes


@pytest.mark.parametrize("value", [30.0, 40.0])
@pytest.mark.parametrize("inclusive", [True, False])
def test_explicit_boundary_semantics(value, inclusive, observation, policy, context):
    config = {**policy.model_dump(), "minimum_inclusive": inclusive, "maximum_inclusive": inclusive}
    result = authorize({**observation, "pressure_value": value}, config, context)
    assert result.max_permission == (Permission.L2 if inclusive else Permission.L1)
    assert result.inspection_status == (Status.EVIDENCE_COMPLETE if inclusive else Status.SAFETY_ALERT)


@pytest.mark.parametrize("expiry,status,reason", [
    (None, Status.OBSERVATION_PENDING, Reason.CALIBRATION_MISSING),
    ("2026-11-11", Status.SAFETY_ALERT, Reason.CALIBRATION_EXPIRED),
    ("not-a-date", Status.REVIEW_REQUIRED, Reason.INVALID_OBSERVATION),
    (20261231, Status.REVIEW_REQUIRED, Reason.INVALID_OBSERVATION)])
def test_missing_invalid_expired_calibration(expiry, status, reason, observation, policy, context):
    result = authorize({**observation, "calibration_expiry_date": expiry}, policy, context)
    assert result.max_permission < Permission.L2
    assert result.inspection_status == status
    assert reason in result.reason_codes


def test_calibration_valid_through_expiry_day_utc(observation, policy, context):
    result = authorize({**observation, "calibration_expiry_date": "2026-11-12"}, policy, context)
    assert result.max_permission == Permission.L2
    shifted = {**context, "evaluated_at": "2026-11-13T01:00:00+14:00", "challenge_expires_at": "2026-11-12T12:00:00Z"}
    assert authorize({**observation, "calibration_expiry_date": "2026-11-12"}, policy, shifted).max_permission == Permission.L2


@pytest.mark.parametrize("status", [None, "UNKNOWN", "OFF"])
def test_equipment_state_does_not_default_to_safe(status, observation, policy, context):
    result = authorize({**observation, "equipment_status": status}, policy, context)
    assert result.max_permission == Permission.L1
    assert result.decision != Outcome.ALLOW


@pytest.mark.parametrize("field", ["pressure_value", "calibration_expiry_date", "asset_id_observed", "challenge_text_observed", "unrecognized-field"])
def test_uncertainty_restricts(field, observation, policy, context):
    result = authorize({**observation, "uncertain_fields": [field]}, policy, context)
    assert result.max_permission < Permission.L2
    assert result.inspection_status == Status.REVIEW_REQUIRED
    if field in {"asset_id_observed", "challenge_text_observed"}:
        assert result.max_permission == Permission.L0


@pytest.mark.parametrize("mode", ["SYNTHETIC", "MOCK_AI", "LIVE_GEMINI", "RECORDED_LIVE"])
def test_no_source_mode_can_grant_l3(mode, observation, policy, context):
    result = authorize({**observation, "artifact_mode": mode}, policy, context, Action.COMPLETE_SIMULATED_ACTION)
    assert result.max_permission == Permission.L2
    assert result.inspection_status == Status.EVIDENCE_COMPLETE
    assert result.decision == Outcome.DENY
    assert Reason.HUMAN_APPROVAL_NOT_IMPLEMENTED in result.reason_codes


@pytest.mark.parametrize("field,value", [("max_permission", 3), ("authorized", True),
    ("payment_approved", True), ("role", "manager"), ("reading_visible", True),
    ("inspection_status", "APPROVED_BY_HUMAN")])
def test_observation_cannot_carry_authority(field, value, observation, policy, context):
    result = authorize({**observation, field: value}, policy, context)
    assert result.decision == Outcome.DENY
    assert result.max_permission == Permission.L0
    assert result.reason_codes == (Reason.INVALID_OBSERVATION,)


@pytest.mark.parametrize("key", ["tenant_id", "job_id", "asset_id_expected", "approved_policy_version"])
def test_policy_must_match_trusted_job_context(key, observation, policy, context):
    result = authorize(observation, policy, {**context, key: "different"})
    assert result.max_permission == Permission.L0
    assert result.reason_codes == (Reason.POLICY_CONTEXT_MISMATCH,)


def test_no_hidden_clock_and_no_mutation(observation, policy, context):
    before = observation.copy()
    first = authorize(observation, policy, context)
    assert all(authorize(observation, policy, context) == first for _ in range(10))
    assert observation == before
    with pytest.raises(ValidationError):
        policy.pressure_max = 999


def test_unchecked_model_copy_is_revalidated(observation, policy, context):
    obs = Observation.model_validate(observation).model_copy(update={"pressure_value": float("nan")})
    assert authorize(obs, policy, context).reason_codes == (Reason.INVALID_OBSERVATION,)
    bad = policy.model_copy(update={"pressure_min": -1})
    assert authorize(observation, bad, context).reason_codes == (Reason.INVALID_POLICY,)


def test_unsafe_and_expired_challenge_remains_l0_alert(observation, policy, context):
    result = authorize({**observation, "pressure_value": 999}, policy,
                       {**context, "challenge_expires_at": context["evaluated_at"]})
    assert result.max_permission == Permission.L0
    assert result.inspection_status == Status.SAFETY_ALERT


def test_unexpected_exception_fails_closed(monkeypatch, observation, policy, context):
    def failure(*args):
        raise RuntimeError("untrusted secret payload must not be returned")
    monkeypatch.setattr("backend.app.policy._evaluate", failure)
    result = authorize(observation, policy, context)
    assert result.decision == Outcome.DENY
    assert result.max_permission == Permission.L0
    assert result.reason_codes == (Reason.INTERNAL_ERROR,)
    assert "secret" not in result.model_dump_json()


@pytest.mark.parametrize("action", ["approve_payment", "publish_policy", "L3", None])
def test_unsupported_action_is_denied(action, observation, policy, context):
    assert authorize(observation, policy, context, action).reason_codes == (Reason.INVALID_INPUT,)


def test_thresholds_and_units_come_from_configuration(observation, policy, context):
    alternative = {**policy.model_dump(), "pressure_min": 1.0, "pressure_max": 2.0, "pressure_unit": "BAR"}
    result = authorize({**observation, "pressure_value": 1.5, "pressure_unit": "BAR"}, alternative, context)
    assert result.decision == Outcome.ALLOW
    assert result.max_permission == Permission.L2
    assert authorize(observation, alternative, context).max_permission < Permission.L2
