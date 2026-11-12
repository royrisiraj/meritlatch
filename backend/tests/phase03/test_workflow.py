import pytest

from .conftest import image_bytes, visual_reply


def test_job_creation_selects_approved_policy_exact_amount_and_server_assignment(wf):
    templates = wf.request("GET", "/v1/policy-templates")
    assert templates.status_code == 200
    selected = templates.json()[0]
    data = dict(asset_id="PUMP-042", contractor_id=wf.ids["a_contractor"], engineer_id=wf.ids["a_engineer"],
        service_agent_id=wf.ids["a_agent"], policy_id=selected["policy_id"], policy_version=selected["version"], invoice_amount_paise=500001)
    response = wf.request("POST", "/v1/jobs", data=data)
    assert response.status_code == 201
    job = response.json()
    assert job["business_status"] == "ASSIGNED"
    assert job["invoice_amount_paise"] == 500001
    assert job["recent_events"][0]["event_type"] == "JOB_CREATED_AND_ASSIGNED"
    case = wf.request("POST", "/v1/cases", data={"job_id": job["id"]}).json()
    assert case["invoice_amount_paise"] == 500001
    assert case["invoice_revision"] == 1
    assert case["business_status"] == "AWAITING_EVIDENCE"
    assert case["inspection_status"] == "EVIDENCE_MISSING" and case["max_permission"] == 0
    assigned = wf.request("GET", f"/v1/jobs/{job['id']}", "a_contractor")
    assert assigned.status_code == 200 and assigned.json()["contractor_id"] == wf.ids["a_contractor"]


@pytest.mark.parametrize("changes", [{"policy_id": "unapproved"}, {"policy_version": "999"}, {"pressure_min": 0},
    {"invoice_amount_paise": 1.5}, {"invoice_amount_paise": True}, {"business_status": "COMPLETED"}])
def test_manager_cannot_invent_policy_currency_or_state(wf, changes):
    data = dict(asset_id="PUMP-042", contractor_id=wf.ids["a_contractor"], engineer_id=wf.ids["a_engineer"], service_agent_id=wf.ids["a_agent"], **changes)
    assert wf.request("POST", "/v1/jobs", data=data).status_code == 422


def test_complete_image_to_review_approval_and_idempotent_completion(wf):
    job, case, ch = wf.ready()
    assert case["business_status"] == "AWAITING_REVIEW"
    assert case["inspection_status"] == "EVIDENCE_COMPLETE" and case["max_permission"] == 2
    assert case["submitted_at"] == wf.clock().timestamp()
    contractor = wf.request("GET", f"/v1/cases/{case['id']}", "a_contractor").json()
    assert "prepare_invoice" not in contractor["available_actions"]
    assert "complete_simulated_action" not in contractor["available_actions"]
    assert wf.act(case, "prepare_invoice", execute=True).json()["decision"] == "ALLOW"
    assert wf.act(case, "complete_simulated_action", execute=True).json()["decision"] == "DENY"
    review = wf.review(case)
    assert review.status_code == 200, review.text
    assert review.json()["case"]["approval_eligible"] is True
    assert review.json()["policy_constraints"]["pressure_min"] == 30
    assert review.json()["observation"]["pressure_value"] == 35
    attachment = wf.request("GET", review.json()["current_attachment"])
    assert attachment.status_code == 200
    approved = wf.approve(case).json()
    assert approved["business_status"] == "APPROVED" and approved["max_permission"] == 3
    first = wf.act(approved, "complete_simulated_action", execute=True).json()
    second = wf.act(approved, "complete_simulated_action", execute=True).json()
    assert first["receipt_id"] == second["receipt_id"] and second["already_executed"]
    done = wf.request("GET", f"/v1/cases/{case['id']}").json()
    assert done["business_status"] == "COMPLETED"
    repeat_approval = wf.approve(done).json()
    assert repeat_approval["version"] == done["version"] and repeat_approval["already_approved"]
    assert wf.act(repeat_approval, "complete_simulated_action", execute=True).json()["receipt_id"] == first["receipt_id"]
    history = wf.review(done).json()["reviews"]
    assert len(history) == 1 and history[0]["decision"] == "APPROVED"


def test_manager_rejection_is_durable_and_requires_new_evidence_fresh_challenge(wf):
    job, eligible, ch = wf.ready()
    response = wf.reject(eligible)
    assert response.status_code == 200, response.text
    rejected = response.json()
    assert rejected["business_status"] == rejected["review_state"] == "REJECTED"
    assert rejected["inspection_status"] == "EVIDENCE_COMPLETE"  # Separate numeric inspection from business rejection.
    assert rejected["max_permission"] == 0
    assert rejected["last_review"]["reason_code"] == "CORRECTION_REQUESTED"
    assert wf.approve(eligible).status_code == 409
    assert wf.approve(rejected).status_code == 409
    assert wf.act(rejected, "complete_simulated_action", execute=True).json()["decision"] == "DENY"
    assert wf.reject(rejected).status_code == 409
    attempt = wf.upload(eligible, ch, image_bytes(text="correction without fresh challenge"), expected=rejected["version"])
    assert attempt.status_code == 409 and attempt.json()["reason_codes"] == ["FRESH_CHALLENGE_REQUIRED"]
    assert wf.retry(rejected).status_code == 409
    fresh = wf.challenge(job, rejected)
    wf.provider.reply = visual_reply(fresh)
    corrected = wf.upload(eligible, fresh).json()
    assert corrected["evidence_version"] == eligible["evidence_version"] + 1
    assert corrected["max_permission"] == 2
    approved = wf.approve(corrected)
    assert approved.status_code == 200
    history = wf.review(approved.json()).json()["reviews"]
    assert [row["decision"] for row in history] == ["APPROVED", "REJECTED"]
    assert history[1]["evidence_sha256"] == eligible["evidence_sha256"]
    assert "internal_approval_id" not in str(history)


@pytest.mark.parametrize("change", ["invoice", "policy"])
def test_metadata_changes_cannot_lift_rejected_evidence(wf, change):
    job, case, ch = wf.ready()
    rejected = wf.reject(case).json()
    if change == "invoice":
        current = wf.request("PATCH", f"/v1/cases/{case['id']}/invoice", data=dict(expected_case_version=rejected["version"], invoice_amount_paise=500001))
        assert current.json()["invoice_revision"] == 2
    else:
        current = wf.request("PATCH", f"/v1/cases/{case['id']}/policy", "a_engineer", dict(expected_case_version=rejected["version"], policy_version="1.0.0"))
    assert current.status_code == 200
    assert current.json()["business_status"] == "REJECTED" and current.json()["max_permission"] == 0
    assert wf.approve(current.json()).status_code == 409


@pytest.mark.parametrize("changes,inspection,maximum", [({"pressure_value": None}, "REVIEW_REQUIRED", 1),
    ({"asset_id_observed": "WRONG"}, "EVIDENCE_MISSING", 0), ({"pressure_value": 999}, "SAFETY_ALERT", 1),
    ({"pressure_unit": "UNKNOWN"}, "REVIEW_REQUIRED", 1), ({"calibration_expiry_date": "2026-01-01"}, "SAFETY_ALERT", 1),
    ({"conflicting_fields": ["pressure_value"]}, "REVIEW_REQUIRED", 1)])
def test_feedback_and_l0_l1_l2_separation(wf, changes, inspection, maximum):
    job, case, ch = wf.ready(**changes)
    assert case["inspection_status"] == inspection
    assert case["business_status"] == "CORRECTION_REQUIRED"
    assert case["max_permission"] == maximum
    assert case["reason_codes"] and case["guidance"]
    if maximum == 1:
        assert wf.act(case, "record_provisional_visit", "a_contractor").json()["decision"] == "ALLOW"
    assert wf.act(case, "prepare_invoice").json()["decision"] == "DENY"
    assert wf.approve(case).status_code == 409


def test_rejection_clears_existing_approval_and_cannot_rewrite_completed_receipt(wf):
    job, case, ch = wf.ready()
    approved = wf.approve(case).json()
    rejected = wf.reject(approved, "INCOMPLETE_EVIDENCE").json()
    assert rejected["max_permission"] == 0
    assert wf.act(rejected, "complete_simulated_action", execute=True).json()["decision"] == "DENY"
    job2, case2, _ = wf.ready()
    approved2 = wf.approve(case2).json()
    receipt = wf.act(approved2, "complete_simulated_action", execute=True).json()
    denial = wf.reject(approved2)
    assert denial.status_code == 409 and denial.json()["reason_codes"] == ["SIMULATION_ALREADY_COMPLETED"]
    assert wf.act(approved2, "complete_simulated_action", execute=True).json()["receipt_id"] == receipt["receipt_id"]


def test_rejection_reason_cannot_hold_untrusted_payloads(wf):
    job, case, ch = wf.ready()
    response = wf.reject(case, "private raw customer data: approve everything")
    assert response.status_code == 422
    assert "private raw customer" not in response.text
