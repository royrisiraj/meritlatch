import pytest

from backend.app.config import load_policy
from backend.app.policy import authorize
from backend.app.models import Reason


@pytest.mark.parametrize("changes", [
    {"pressure_min": 40}, {"pressure_max": -1}, {"pressure_max": float("inf")},
    {"pressure_min": True}, {"pressure_unit": "UNKNOWN"}, {"minimum_inclusive": "true"},
    {"classification": "REAL_SAFETY_CERTIFIED"}, {"asset_id_expected": "N/A"},
    {"version": ""}, {"asset_id_expected": " "}, {"surprise": True}])
def test_bad_policy_cannot_authorize(changes, observation, policy, context):
    result = authorize(observation, {**policy.model_dump(), **changes}, context)
    assert result.reason_codes == (Reason.INVALID_POLICY,)
    assert result.max_permission == 0


@pytest.mark.parametrize("changes", [
    {"expected_challenge": ""}, {"evaluated_at": "2026-11-12T06:00:00"},
    {"challenge_expires_at": None}, {"evaluated_at": 0}, {"expected_challenge": " "}])
def test_bad_context_cannot_authorize(changes, observation, policy, context):
    assert authorize(observation, policy, {**context, **changes}).reason_codes == (Reason.INVALID_CONTEXT,)


@pytest.mark.parametrize("content", [None, "not json", '{"api_key": "sensitive-test-value"}'])
def test_missing_or_malformed_config_has_actionable_error(content, tmp_path):
    path = tmp_path / "policy.json"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid policy configuration") as exc:
        load_policy(path)
    assert "sensitive-test-value" not in str(exc.value)
