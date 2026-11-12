from concurrent.futures import ThreadPoolExecutor
from threading import Event
import asyncio
from dataclasses import replace

import pytest

from backend.app.perception import ProviderError, PerceptionResult, VisualObservation
from .conftest import image_bytes, visual_reply


def fail_once(wf, monkeypatch):
    job, case, ch = wf.setup_case()
    original = wf.provider.inspect
    calls = []
    async def inspect(source):
        calls.append(source.evidence_id)
        if len(calls) == 1: raise ProviderError("PROVIDER_UNAVAILABLE")
        return await original(source)
    monkeypatch.setattr(wf.provider, "inspect", inspect)
    failed = wf.upload(case, ch)
    assert failed.status_code == 502
    return job, failed.json(), ch, calls


def test_explicit_provider_recovery_keeps_evidence_and_history_and_no_extra_billing(wf, monkeypatch):
    job, failed, ch, calls = fail_once(wf, monkeypatch)
    assert failed["max_permission"] == 0
    contractor = wf.request("GET", f"/v1/cases/{failed['id']}", "a_contractor").json()
    assert "request_reanalysis" in contractor["available_actions"]
    recovered = wf.retry(failed)
    assert recovered.status_code == 200, recovered.text
    current = recovered.json()
    assert current["version"] == failed["version"] + 2
    assert current["evidence_version"] == failed["evidence_version"]
    assert current["evidence_id"] == failed["evidence_id"]
    assert current["evidence_sha256"] == failed["evidence_sha256"]
    assert current["max_permission"] == 2
    replay = wf.retry(failed)
    assert replay.status_code == 200 and replay.json()["operation_replayed"]
    assert replay.json()["version"] == current["version"] and len(calls) == 2
    assert wf.approve(current).status_code == 200
    with wf.service.repository.transaction() as tx:
        assert len(tx.find("media_uploads", case_id=current["id"])) == 1
        assert tx.find("media_analyses", case_id=current["id"])[0]["status"] == "FAILED"
        assert tx.find("analysis_results", case_id=current["id"])[0]["status"] == "SUCCESS"


@pytest.mark.parametrize("changes", [{"pressure_value": None}, {"pressure_value": 999}, {"asset_id_observed": "WRONG"}])
def test_insufficient_or_unsafe_success_is_not_retried_into_validity(wf, changes):
    _, case, _ = wf.ready(**changes)
    response = wf.retry(case)
    assert response.status_code == 409
    assert response.json()["reason_codes"] == ["NEW_EVIDENCE_REQUIRED"]


@pytest.mark.parametrize("kind", ["schema", "blocked"])
def test_semantically_invalid_provider_output_requires_new_evidence(wf, monkeypatch, kind):
    job, case, ch = wf.setup_case()
    async def inspect(source): raise ProviderError("PROVIDER_INVALID_OBSERVATION" if kind == "schema" else "PROVIDER_BLOCKED")
    monkeypatch.setattr(wf.provider, "inspect", inspect)
    failed = wf.upload(case, ch).json()
    response = wf.retry(failed)
    assert response.status_code == 409 and response.json()["reason_codes"] == ["NEW_EVIDENCE_REQUIRED"]
    assert "request_reanalysis" not in wf.request("GET", f"/v1/cases/{failed['id']}", "a_contractor").json()["available_actions"]


@pytest.mark.parametrize("key,status", [("a_other_contractor", 404), ("b_contractor", 404), ("a_manager", 403), ("a_engineer", 403), ("a_agent", 403)])
def test_reanalysis_respects_roles_and_assignments(wf, monkeypatch, key, status):
    _, failed, _, _ = fail_once(wf, monkeypatch)
    assert wf.retry(failed, key=key).status_code == status


def test_reanalysis_needs_current_version_current_original_session_and_challenge(wf, monkeypatch):
    job, failed, ch, calls = fail_once(wf, monkeypatch)
    assert wf.retry(failed, expected=failed["version"] - 1).status_code == 409
    fresh = wf.service.login("a", "contractor", wf.passwords["a_contractor"])["access_token"]
    response = wf.client.post(f"/v1/cases/{failed['id']}/evidence/{failed['evidence_id']}/reanalysis",
        headers={"Authorization": "Bearer " + fresh}, json=dict(expected_case_version=failed["version"], idempotency_key="operation_00000001"))
    assert response.status_code == 409
    wf.clock.advance(300)
    assert wf.retry(failed).status_code == 409
    assert len(calls) == 1


def test_retry_attempt_limit_and_no_automatic_loop(wf, monkeypatch):
    job, case, ch = wf.setup_case()
    calls = []
    async def unavailable(source):
        calls.append(source.evidence_id)
        raise ProviderError("PROVIDER_UNAVAILABLE")
    monkeypatch.setattr(wf.provider, "inspect", unavailable)
    current = wf.upload(case, ch).json()
    for attempt in range(3):
        response = wf.retry(current, operation=f"retry_operation_{attempt:04d}")
        assert response.status_code == 502
        current = response.json()
    assert wf.retry(current, operation="retry_operation_9999").status_code == 429
    assert len(calls) == 4


def test_same_upload_operation_replays_only_its_own_verified_request(wf, monkeypatch):
    job, case, ch = wf.setup_case()
    data = image_bytes(text=ch["token"])
    calls = []
    original = wf.provider.inspect
    async def inspect(source):
        calls.append(source.evidence_id)
        return await original(source)
    monkeypatch.setattr(wf.provider, "inspect", inspect)
    header = {"Idempotency-Key": "upload_operation_0001"}
    first = wf.upload(case, ch, data, extra=header)
    assert first.status_code == 200
    second = wf.upload(case, ch, data, extra=header)
    assert second.status_code == 200
    assert second.json()["operation_replayed"] is True
    assert second.json()["evidence_version"] == first.json()["evidence_version"]
    assert second.json()["version"] == first.json()["version"]
    assert len(calls) == 1
    conflict = wf.upload(case, ch, image_bytes(text="different"), extra=header)
    assert conflict.status_code == 409 and conflict.json()["reason_codes"] == ["IDEMPOTENCY_CONFLICT"]
    normal_duplicate = wf.upload(case, ch, data, expected=first.json()["version"])
    assert normal_duplicate.status_code == 409 and normal_duplicate.json()["reason_codes"] == ["EXACT_DUPLICATE"]


def test_failed_upload_operation_replay_does_not_repeat_provider(wf, monkeypatch):
    job, case, ch = wf.setup_case()
    calls = []
    async def failing(source):
        calls.append(source.evidence_id)
        raise ProviderError("PROVIDER_TIMEOUT")
    monkeypatch.setattr(wf.provider, "inspect", failing)
    header = {"Idempotency-Key": "upload_operation_0001"}
    data = image_bytes()
    first = wf.upload(case, ch, data, extra=header)
    second = wf.upload(case, ch, data, extra=header)
    assert first.status_code == second.status_code == 504
    assert second.json()["max_permission"] == 0 and second.json()["operation_replayed"]
    assert len(calls) == 1


def test_operation_key_is_bound_to_login_session_and_cannot_resurrect_rejected_bytes(wf):
    job, case, ch = wf.setup_case()
    header = {"Idempotency-Key": "upload_operation_0001"}
    data = image_bytes()
    accepted = wf.upload(case, ch, data, extra=header).json()
    rejected = wf.reject(accepted).json()
    assert wf.upload(case, ch, data, extra=header).status_code == 409
    fresh = wf.challenge(job, rejected)
    duplicate = wf.upload(case, fresh, data)
    assert duplicate.status_code == 409 and duplicate.json()["reason_codes"] == ["EXACT_DUPLICATE"]


def test_replay_during_analysis_is_pending_and_does_not_run_second_provider(wf, monkeypatch):
    job, case, ch = wf.setup_case()
    started, release = Event(), Event()
    calls = []
    async def waiting(source):
        calls.append(source.evidence_id)
        started.set()
        assert await asyncio.to_thread(release.wait, 10)
        return PerceptionResult(VisualObservation.model_validate(visual_reply(ch)), "mock-observer-v1", "mock-v1")
    monkeypatch.setattr(wf.provider, "inspect", waiting)
    header = {"Idempotency-Key": "upload_operation_0001"}
    data = image_bytes()
    with ThreadPoolExecutor(max_workers=1) as pool:
        running = pool.submit(wf.upload, case, ch, data, "image/png", "a_contractor", None, header)
        assert started.wait(10)
        replay = wf.upload(case, ch, data, extra=header)
        assert replay.status_code == 202
        assert replay.json()["max_permission"] == 0
        pending = replay.json()
        assert wf.retry(pending).status_code == 409  # No concurrent live retry before timeout/grace.
        release.set()
        assert running.result(timeout=10).status_code == 200
    assert len(calls) == 1


def test_live_retry_requires_explicit_per_request_cost_approval_without_network(wf, monkeypatch):
    from fastapi.testclient import TestClient
    from pydantic import SecretStr
    from backend.app.api import create_app
    job, case, ch = wf.setup_case()
    class LiveTransportStub:
        mode = "LIVE_GEMINI"
        model_id = "unit-transport-stub-no-live-inference"
        calls = 0
        async def inspect(self, source):
            self.calls += 1
            raise ProviderError("PROVIDER_UNAVAILABLE")
    stub = LiveTransportStub()
    app = create_app(replace(wf.app.state.settings, provider_mode="LIVE_GEMINI", allow_billable=True,
        gemini_api_key=SecretStr("unit-test-not-a-real-key")), repository=wf.service.repository, clock=wf.clock, perception_provider=stub)
    with TestClient(app) as client:
        headers = {**wf.headers("a_contractor"), "Content-Type": "image/png", "X-Expected-Case-Version": str(ch["case_version"]),
            "X-Challenge-ID": ch["id"], "X-Evidence-Session-ID": ch["evidence_session_id"]}
        failed = client.post(f"/v1/cases/{case['id']}/evidence", headers=headers, content=image_bytes()).json()
        response = client.post(f"/v1/cases/{case['id']}/evidence/{failed['evidence_id']}/reanalysis", headers=wf.headers("a_contractor"),
            json=dict(expected_case_version=failed["version"], idempotency_key="operation_00000001"))
        assert response.status_code == 403
        assert response.json()["reason_codes"] == ["BILLABLE_REANALYSIS_NOT_APPROVED"]
        assert stub.calls == 1


def test_new_login_cannot_reuse_existing_upload_operation_key(wf):
    job, case, ch = wf.setup_case()
    key = {"Idempotency-Key": "upload_operation_0001"}
    data = image_bytes()
    accepted = wf.upload(case, ch, data, extra=key)
    fresh_token = wf.service.login("a", "contractor", wf.passwords["a_contractor"])["access_token"]
    headers = {"Authorization": "Bearer " + fresh_token, "Content-Type": "image/png", "X-Expected-Case-Version": str(ch["case_version"]),
        "X-Challenge-ID": ch["id"], "X-Evidence-Session-ID": ch["evidence_session_id"], **key}
    result = wf.client.post(f"/v1/cases/{case['id']}/evidence", headers=headers, content=data)
    assert result.status_code == 409
    assert result.json()["reason_codes"] == ["CHALLENGE_INVALID"]


def test_reanalysis_pending_after_interruption_requires_grace_and_preserves_version(wf, monkeypatch):
    job, case, ch = wf.setup_case()
    # Reserve the real image transaction without running a provider: a process
    # interruption at this exact boundary leaves this same persisted state.
    from backend.app.media import validate_image
    image = validate_image(image_bytes(), "image/png", wf.app.state.settings)
    reservation = wf.app.state.media._accept(wf.tokens["a_contractor"], case["id"], ch["case_version"], ch["id"], ch["evidence_session_id"], image)
    pending = wf.request("GET", f"/v1/cases/{case['id']}").json()
    assert wf.retry(pending).status_code == 409
    wf.clock.advance(26)
    current = wf.request("GET", f"/v1/cases/{case['id']}", "a_contractor").json()
    assert "request_reanalysis" in current["available_actions"]
    recovered = wf.retry(current)
    assert recovered.status_code == 200
    assert recovered.json()["evidence_version"] == pending["evidence_version"] == 1
    assert recovered.json()["max_permission"] == 2


def test_idempotent_upload_operation_survives_restart(wf):
    from fastapi.testclient import TestClient
    from backend.app.api import create_app
    job, case, ch = wf.setup_case()
    data = image_bytes()
    header = {"Idempotency-Key": "upload_operation_0001"}
    original = wf.upload(case, ch, data, extra=header).json()
    wf.service.repository.close()
    restarted = create_app(wf.app.state.settings, clock=wf.clock)
    with TestClient(restarted) as client:
        headers = {**wf.headers("a_contractor"), "Content-Type": "image/png", "X-Expected-Case-Version": str(ch["case_version"]),
            "X-Challenge-ID": ch["id"], "X-Evidence-Session-ID": ch["evidence_session_id"], **header}
        response = client.post(f"/v1/cases/{case['id']}/evidence", headers=headers, content=data)
        assert response.status_code == 200
        assert response.json()["operation_replayed"] and response.json()["version"] == original["version"]
        assert response.json()["evidence_version"] == 1
