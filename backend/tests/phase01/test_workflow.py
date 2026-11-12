import json

import pytest
from fastapi.testclient import TestClient

from backend.app.api import create_app
from backend.app.errors import AppError
from backend.app.models import Policy
from backend.app.settings import Settings
from backend.app.provisioning import register_reviewed_policy


def test_complete_authenticated_l0_l1_l2_l3_and_idempotent_simulation(world):
    job, case = world.new()
    assert case["max_permission"] == 0
    assert world.act(case, "prepare_invoice").json()["decision"] == "DENY"
    assert world.approve(case).status_code == 409
    ch = world.challenge(job, case)
    partial = world.inject(case, ch, {"pressure_value": None})
    assert partial["max_permission"] == 1
    assert partial["inspection_status"] == "OBSERVATION_PENDING"
    assert world.act(partial, "record_provisional_visit", "a_contractor", True).json()["decision"] == "ALLOW"
    assert world.act(partial, "prepare_invoice").json()["decision"] == "DENY"
    complete = world.inject(case, ch, expected=partial["version"])
    assert complete["max_permission"] == 2
    assert complete["artifact_mode"] == "SYNTHETIC"
    assert "manager review" in complete["guidance"]
    assert "Phase 00" not in complete["guidance"]
    assert world.act(complete, "prepare_invoice", execute=True).json()["decision"] == "ALLOW"
    assert world.act(complete, "complete_simulated_action", execute=True).json()["decision"] == "DENY"
    approved = world.approve(complete)
    assert approved.status_code == 200
    assert approved.json()["inspection_status"] == "APPROVED_BY_HUMAN"
    assert approved.json()["max_permission"] == 3
    first = world.act(approved.json(), "complete_simulated_action", execute=True)
    second = world.act(approved.json(), "complete_simulated_action", execute=True)
    assert first.json()["decision"] == second.json()["decision"] == "ALLOW"
    assert first.json()["receipt_id"] == second.json()["receipt_id"]
    assert first.json()["already_executed"] is False
    assert second.json()["already_executed"] is True
    assert world.request("GET", f"/v1/cases/{case['id']}").json()["simulated_completed"] is True
    audit = world.request("GET", f"/v1/cases/{case['id']}/audit").json()
    assert sum(row["event_type"] == "SIMULATED_ACTION_EXECUTED" and row["action"] == "complete_simulated_action" for row in audit) == 1


@pytest.mark.parametrize("key", ["a_contractor", "a_engineer", "a_agent"])
def test_nonmanager_cannot_approve_even_with_complete_evidence(world, key):
    job, case, ch = world.ready()
    assert world.approve(case, key).status_code == 403
    assert world.request("GET", f"/v1/cases/{case['id']}").json()["max_permission"] == 2


@pytest.mark.parametrize("key,action", [("a_contractor", "prepare_invoice"), ("a_contractor", "complete_simulated_action"),
    ("a_engineer", "prepare_invoice"), ("a_engineer", "complete_simulated_action"),
    ("a_manager", "prepare_invoice"), ("a_manager", "complete_simulated_action")])
def test_action_roles_are_enforced_even_after_manager_approval(world, key, action):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    assert world.act(approved, action, key, True).status_code == 403


@pytest.mark.parametrize("changes,status,maximum,reason", [
    ({"asset_id_observed": "N/A"}, "EVIDENCE_MISSING", 0, "ASSET_MISMATCH"),
    ({"asset_id_observed": "PUMP-999"}, "EVIDENCE_MISSING", 0, "ASSET_MISMATCH"),
    ({"challenge_text_observed": "old-token"}, "EVIDENCE_MISSING", 0, "CHALLENGE_MISMATCH"),
    ({"pressure_value": None}, "OBSERVATION_PENDING", 1, "PRESSURE_MISSING"),
    ({"pressure_unit": None}, "REVIEW_REQUIRED", 1, "UNIT_UNSUPPORTED"),
    ({"pressure_unit": "BAR"}, "REVIEW_REQUIRED", 1, "UNIT_UNSUPPORTED"),
    ({"pressure_value": 999.0}, "SAFETY_ALERT", 1, "PRESSURE_OUT_OF_RANGE"),
    ({"calibration_expiry_date": "2026-11-11"}, "SAFETY_ALERT", 1, "CALIBRATION_EXPIRED"),
    ({"uncertain_fields": ["pressure_value"]}, "REVIEW_REQUIRED", 1, "UNCERTAIN_OBSERVATION"),
])
def test_persisted_invalid_observation_stays_restricted(world, changes, status, maximum, reason):
    job, case = world.new()
    ch = world.challenge(job, case)
    current = world.inject(case, ch, changes)
    assert current["max_permission"] == maximum
    assert current["inspection_status"] == status
    evaluated = world.act(current, "prepare_invoice").json()
    assert evaluated["decision"] == "DENY"
    assert reason in evaluated["reason_codes"]
    assert world.approve(current).status_code == 409


@pytest.mark.parametrize("changes", [{"pressure_value": -1}, {"pressure_value": float("nan")},
    {"pressure_value": float("inf")}, {"pressure_value": "35"}, {"permission_level": 3},
    {"authorized": True}, {"role": "MANAGER"}, {"payment_approved": True}])
def test_untrusted_authority_or_invalid_numeric_data_is_rejected_before_persistence(world, changes):
    job, case = world.new()
    ch = world.challenge(job, case)
    with pytest.raises(AppError) as exc:
        world.inject(case, ch, changes)
    assert exc.value.code == "INVALID_OBSERVATION"
    with world.service.repository.transaction() as tx:
        assert tx.find("evidence", case_id=case["id"]) == []


def test_evidence_change_invalidates_approval_even_when_new_evidence_is_valid(world):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    replaced = world.inject(case, ch, {"pressure_value": 36.0}, expected=approved["version"])
    assert replaced["max_permission"] == 2
    assert replaced["evidence_version"] == case["evidence_version"] + 1
    assert replaced["evidence_sha256"] != case["evidence_sha256"]
    assert world.act(replaced, "complete_simulated_action").json()["decision"] == "DENY"
    assert world.approve(replaced).json()["max_permission"] == 3


def test_amount_change_invalidates_approval_and_rebinding_uses_integer_paise(world):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    response = world.request("PATCH", f"/v1/cases/{case['id']}/invoice", data=dict(expected_case_version=approved["version"], invoice_amount_paise=500001))
    assert response.status_code == 200
    changed = response.json()
    assert changed["max_permission"] == 2
    assert changed["invoice_amount_paise"] == 500001
    assert world.act(changed, "complete_simulated_action").json()["decision"] == "DENY"


@pytest.mark.parametrize("key", ["a_contractor", "a_engineer", "a_agent"])
def test_only_manager_can_change_invoice_details(world, key):
    job, case = world.new()
    response = world.request("PATCH", f"/v1/cases/{case['id']}/invoice", key,
        dict(expected_case_version=case["version"], invoice_amount_paise=500001))
    assert response.status_code == 403
    assert world.request("GET", f"/v1/cases/{case['id']}").json()["invoice_amount_paise"] == 500000


def candidate(world, job, version="1.0.1"):
    return Policy.model_validate({**world.service.template.model_dump(), "tenant_id": "a", "job_id": job["id"], "version": version})


def test_only_reviewed_policy_version_can_be_selected_and_it_invalidates_approval(world):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    data = dict(expected_case_version=approved["version"], policy_version="1.0.1")
    assert world.request("PATCH", f"/v1/cases/{case['id']}/policy", "a_manager", data).status_code == 403
    assert world.request("PATCH", f"/v1/cases/{case['id']}/policy", "a_engineer", data).status_code == 422
    result = register_reviewed_policy(world.service, world.tokens["a_engineer"], world.tokens["a_reviewer"], candidate(world, job), "SYNTHETIC-engineering-review-001")
    assert result["activated"] is False
    current = world.request("GET", f"/v1/cases/{case['id']}").json()
    assert current["max_permission"] == 3
    changed = world.request("PATCH", f"/v1/cases/{case['id']}/policy", "a_engineer", data)
    assert changed.status_code == 200
    assert changed.json()["policy_version"] == "1.0.1"
    assert changed.json()["max_permission"] == 2
    assert world.act(changed.json(), "complete_simulated_action").json()["decision"] == "DENY"


@pytest.mark.parametrize("author,reviewer", [("a_engineer", "a_engineer"), ("a_engineer", "b_engineer"), ("a_manager", "a_reviewer")])
def test_policy_registration_requires_independent_authorized_engineers(world, author, reviewer):
    job, case = world.new()
    with pytest.raises(AppError) as exc:
        register_reviewed_policy(world.service, world.tokens[author], world.tokens[reviewer], candidate(world, job), "SYNTHETIC-test-review")
    assert exc.value.status == 403


def test_approval_binding_contains_all_required_dimensions_and_is_not_exposed(world):
    job, case, ch = world.ready()
    approved = world.approve(case)
    with world.service.repository.transaction() as tx:
        row = tx.find("approvals", case_id=case["id"])[0]
        binding = json.loads(row["binding_json"])
        ev = tx.get("evidence", id=binding["evidence_id"])
    assert binding.items() >= dict(tenant_id="a", case_id=case["id"], job_id=job["id"],
        action="complete_simulated_action", invoice_amount_paise=500000, evidence_sha256=case["evidence_sha256"],
        evidence_version=case["evidence_version"], case_version=case["version"], policy_version="1.0.0",
        reviewer_id=world.ids["a_manager"], evidence_session_id=ch["evidence_session_id"]).items()
    from backend.app.case_service import digest
    assert row["binding_sha256"] == digest(binding)
    assert ev["sha256"] == digest(json.loads(ev["observation_json"]))
    assert row["id"] not in approved.text
    assert row["binding_sha256"] not in approved.text


@pytest.mark.parametrize("operation", ["invoice", "approval", "challenge", "evaluate"])
def test_stale_expected_version_is_rejected(world, operation):
    job, stale, ch = world.ready()
    current = world.approve(stale).json()
    if operation == "invoice":
        response = world.request("PATCH", f"/v1/cases/{stale['id']}/invoice", data=dict(expected_case_version=stale["version"], invoice_amount_paise=1))
    elif operation == "approval":
        response = world.approve(stale)
    elif operation == "challenge":
        response = world.request("POST", f"/v1/jobs/{job['id']}/challenges", "a_contractor", dict(case_id=stale["id"], expected_case_version=stale["version"]))
    else:
        response = world.act(stale, "prepare_invoice")
    assert response.status_code == 409
    assert "VERSION_CONFLICT" in response.json()["reason_codes"]
    assert world.request("GET", f"/v1/cases/{stale['id']}").json()["version"] == current["version"]


@pytest.mark.parametrize("extra", [{"max_permission": 3}, {"role": "MANAGER"}, {"approved": True}, {"case_version": 999}])
def test_direct_api_cannot_supply_permissions_or_approval_authority(world, extra):
    job, case = world.new()
    response = world.request("POST", f"/v1/cases/{case['id']}/actions/execute", "a_agent",
                             dict(expected_case_version=1, action="complete_simulated_action", **extra))
    assert response.status_code == 422
    assert world.request("GET", f"/v1/cases/{case['id']}").json()["max_permission"] == 0


def test_engineer_gets_redacted_observation_and_audit_has_no_tokens_or_payloads(world):
    job, case, ch = world.ready()
    redacted = world.request("GET", f"/v1/cases/{case['id']}", "a_engineer").json()
    assert "observation" not in redacted
    audit = world.request("GET", f"/v1/cases/{case['id']}/audit", "a_engineer")
    assert audit.status_code == 200
    for forbidden in [ch["token"], ch["evidence_session_id"], world.tokens["a_manager"], "pressure_value", "password_hash"]:
        assert forbidden not in audit.text


def test_normal_factory_disables_synthetic_intake_and_existing_test_artifacts(world):
    job, case, ch = world.ready()
    normal = create_app(Settings(database_path=world.app.state.settings.database_path), repository=world.service.repository, clock=world.clock)
    with TestClient(normal) as client:
        for path in (f"/v1/cases/{case['id']}/evidence/fixture", f"/v1/cases/{case['id']}/evidence", "/v1/policies/release"):
            assert client.post(path, headers=world.headers("a_contractor"), json={"max_permission": 3}).status_code == 404
        result = client.get(f"/v1/cases/{case['id']}", headers=world.headers()).json()
        assert result["max_permission"] == 0
        assert "TEST_EVIDENCE_DISABLED" in result["reason_codes"]
    with pytest.raises(AppError) as exc:
        normal.state.service.inject_synthetic_evidence(world.tokens["a_contractor"], "id", 1, "id", "id", {})
    assert exc.value.code == "TEST_EVIDENCE_DISABLED"


def test_fail_closed_errors_do_not_echo_exception_or_password(world, monkeypatch):
    def failure(*args, **kwargs):
        raise RuntimeError("sensitive-marker-do-not-log")
    monkeypatch.setattr(world.service, "get_case", failure)
    response = world.request("GET", "/v1/cases/id")
    assert response.status_code == 500
    assert response.json()["reason_codes"] == ["INTERNAL_ERROR"]
    assert "sensitive-marker" not in response.text
