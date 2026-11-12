from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
import asyncio
from hashlib import sha256

import pytest

from backend.app.perception import PerceptionResult, VisualObservation
from .conftest import image_bytes, visual_reply


@pytest.mark.parametrize("finish_order", ["old_first", "new_first"])
def test_out_of_order_results_cannot_authorize_replaced_evidence(media_world, monkeypatch, finish_order):
    w = media_world
    job, case, ch = w.setup_case()
    started = [Event(), Event()]
    release = [Event(), Event()]
    lock, calls = Lock(), []
    async def delayed(source):
        with lock:
            index = len(calls)
            calls.append(source.evidence_id)
        started[index].set()
        assert await asyncio.to_thread(release[index].wait, 10)
        return PerceptionResult(VisualObservation.model_validate(visual_reply(ch, pressure_value=999 if index == 0 else 35)), "mock-observer-v1", "mock-v1")
    monkeypatch.setattr(w.provider, "inspect", delayed)
    old_bytes, new_bytes = image_bytes(text="old"), image_bytes(text="new")
    with ThreadPoolExecutor(max_workers=2) as pool:
        old = pool.submit(w.upload, case, ch, old_bytes)
        assert started[0].wait(10)
        pending = w.request("GET", f"/v1/cases/{case['id']}").json()
        assert pending["max_permission"] == 0
        assert pending["inspection_status"] == "OBSERVATION_PENDING"
        newer = pool.submit(w.upload, case, ch, new_bytes, "image/png", "a_contractor", pending["version"])
        assert started[1].wait(10)
        first = 0 if finish_order == "old_first" else 1
        release[first].set()
        (old if first == 0 else newer).result(timeout=10)
        release[1-first].set()
        old_response, new_response = old.result(timeout=10), newer.result(timeout=10)
    assert old_response.status_code == 409
    assert old_response.json()["reason_codes"] == ["ANALYSIS_STALE"]
    assert new_response.status_code == 200
    current = w.request("GET", f"/v1/cases/{case['id']}").json()
    assert current["max_permission"] == 2
    assert current["evidence_sha256"] == sha256(new_bytes).hexdigest()
    assert current["observation"]["pressure_value"] == 35
    with w.service.repository.transaction() as tx:
        assert sorted(row["status"] for row in tx.find("media_analyses")) == ["STALE", "SUCCESS"]


@pytest.mark.parametrize("change", ["expiry", "logout", "invoice", "policy", "assignment", "challenge"])
def test_scope_or_version_changes_during_analysis_fail_closed(media_world, monkeypatch, change):
    w = media_world
    job, case, ch = w.setup_case()
    started, release = Event(), Event()
    async def delayed(source):
        started.set()
        assert await asyncio.to_thread(release.wait, 10)
        return PerceptionResult(VisualObservation.model_validate(visual_reply(ch)), "mock-observer-v1", "mock-v1")
    monkeypatch.setattr(w.provider, "inspect", delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        submitted = pool.submit(w.upload, case, ch)
        assert started.wait(10)
        pending = w.request("GET", f"/v1/cases/{case['id']}").json()
        assert pending["max_permission"] == 0
        if change == "expiry": w.clock.advance(300)
        if change == "logout": assert w.request("POST", "/v1/auth/logout", "a_contractor").status_code == 200
        if change == "invoice": assert w.request("PATCH", f"/v1/cases/{case['id']}/invoice", data=dict(expected_case_version=pending["version"], invoice_amount_paise=500001)).status_code == 200
        if change == "policy": assert w.request("PATCH", f"/v1/cases/{case['id']}/policy", "a_engineer", dict(expected_case_version=pending["version"], policy_version="1.0.0")).status_code == 200
        if change == "assignment": assert w.request("PATCH", f"/v1/jobs/{job['id']}/assignment", data=dict(expected_job_version=job["version"], contractor_id=w.ids["a_other_contractor"])).status_code == 200
        if change == "challenge": w.challenge(job, pending)
        release.set()
        response = submitted.result(timeout=10)
    assert response.status_code in {401, 404, 409}
    assert response.json()["decision"] == "DENY"
    current = w.request("GET", f"/v1/cases/{case['id']}").json()
    assert current["max_permission"] == 0
    assert w.approve(current).status_code == 409


def test_acceptance_immediately_invalidates_l3_while_provider_is_running(media_world, monkeypatch):
    w = media_world
    job, case, ch = w.setup_case()
    complete = w.upload(case, ch).json()
    approved = w.approve(complete).json()
    started, release = Event(), Event()
    original = w.provider.inspect
    async def delayed(source):
        started.set()
        assert await asyncio.to_thread(release.wait, 10)
        return await original(source)
    monkeypatch.setattr(w.provider, "inspect", delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        request = pool.submit(w.upload, case, ch, image_bytes(text="replacement"), "image/png", "a_contractor", approved["version"])
        assert started.wait(10)
        pending = w.request("GET", f"/v1/cases/{case['id']}").json()
        assert pending["max_permission"] == 0
        assert pending["inspection_status"] == "OBSERVATION_PENDING"
        assert w.approve(pending).status_code == 409
        assert w.act(pending, "complete_simulated_action", execute=True).json()["decision"] == "DENY"
        release.set()
        result = request.result(timeout=10)
    assert result.status_code == 200
    assert result.json()["max_permission"] == 2


def test_failure_after_analysis_insert_rolls_back_finalization(media_world, monkeypatch):
    w = media_world
    job, case, ch = w.setup_case()
    original = w.service._event
    def event(tx, actor, state, kind, *args, **kwargs):
        if kind == "ANALYSIS_COMPLETED":
            raise RuntimeError("private-model-marker")
        return original(tx, actor, state, kind, *args, **kwargs)
    monkeypatch.setattr(w.service, "_event", event)
    response = w.upload(case, ch)
    assert response.status_code == 500
    assert "private-model-marker" not in response.text
    with w.service.repository.transaction() as tx:
        assert len(tx.find("media_uploads")) == 1
        assert not tx.find("media_analyses")
        assert tx.get("cases", id=case["id"])["version"] == ch["case_version"] + 1
    monkeypatch.setattr(w.service, "_event", original)
    current = w.request("GET", f"/v1/cases/{case['id']}").json()
    assert current["max_permission"] == 0
    assert current["inspection_status"] == "OBSERVATION_PENDING"
