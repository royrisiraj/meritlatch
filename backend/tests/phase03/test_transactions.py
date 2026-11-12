from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
import asyncio

import pytest

from backend.app.perception import PerceptionResult, VisualObservation, ProviderError
from .conftest import image_bytes, visual_reply


@pytest.mark.parametrize("first", ["approval", "rejection", "simultaneous"])
def test_approval_rejection_race_has_one_current_version_winner(wf, first):
    job, case, ch = wf.ready()
    barrier, done = Barrier(2), Event()
    def run(kind):
        barrier.wait(timeout=10)
        if first != "simultaneous" and kind != first: assert done.wait(10)
        try: return wf.approve(case) if kind == "approval" else wf.reject(case)
        finally:
            if kind == first: done.set()
    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = pool.submit(run, "approval"), pool.submit(run, "rejection")
        approved, rejected = a.result(timeout=10), b.result(timeout=10)
    assert sorted([approved.status_code, rejected.status_code]) == [200, 409]
    current = wf.request("GET", f"/v1/cases/{case['id']}").json()
    if rejected.status_code == 200:
        assert current["max_permission"] == 0 and current["business_status"] == "REJECTED"
        assert wf.approve(current).status_code == 409
    else:
        assert current["max_permission"] == 3
        assert wf.reject(current).json()["max_permission"] == 0


def test_rejection_during_processing_discards_provider_result(wf, monkeypatch):
    job, case, ch = wf.setup_case()
    started, release = Event(), Event()
    async def delayed(source):
        started.set()
        assert await asyncio.to_thread(release.wait, 10)
        return PerceptionResult(VisualObservation.model_validate(visual_reply(ch)), "mock-observer-v1", "mock-v1")
    monkeypatch.setattr(wf.provider, "inspect", delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        submitted = pool.submit(wf.upload, case, ch)
        assert started.wait(10)
        pending = wf.request("GET", f"/v1/cases/{case['id']}").json()
        rejected = wf.reject(pending)
        assert rejected.status_code == 200
        release.set()
        discarded = submitted.result(timeout=10)
    assert discarded.status_code == 409
    current = wf.request("GET", f"/v1/cases/{case['id']}").json()
    assert current["business_status"] == "REJECTED" and current["max_permission"] == 0


@pytest.mark.parametrize("change", ["invoice", "policy", "new_evidence", "expiry", "reassignment"])
def test_reanalysis_finalizes_only_against_current_state(wf, monkeypatch, change):
    job, case, ch = wf.setup_case()
    calls = []
    started, release = Event(), Event()
    async def provider(source):
        calls.append(source.evidence_id)
        if len(calls) == 1: raise ProviderError("PROVIDER_UNAVAILABLE")
        if len(calls) == 2:
            started.set()
            assert await asyncio.to_thread(release.wait, 10)
        return PerceptionResult(VisualObservation.model_validate(visual_reply(ch)), "mock-observer-v1", "mock-v1")
    monkeypatch.setattr(wf.provider, "inspect", provider)
    failed = wf.upload(case, ch).json()
    with ThreadPoolExecutor(max_workers=1) as pool:
        retry = pool.submit(wf.retry, failed)
        assert started.wait(10)
        pending = wf.request("GET", f"/v1/cases/{case['id']}").json()
        if change == "invoice": assert wf.request("PATCH", f"/v1/cases/{case['id']}/invoice", data=dict(expected_case_version=pending["version"], invoice_amount_paise=500001)).status_code == 200
        if change == "policy": assert wf.request("PATCH", f"/v1/cases/{case['id']}/policy", "a_engineer", dict(expected_case_version=pending["version"], policy_version="1.0.0")).status_code == 200
        if change == "new_evidence": assert wf.upload(case, ch, image_bytes(text="new current image"), expected=pending["version"]).status_code == 200
        if change == "expiry": wf.clock.advance(300)
        if change == "reassignment": assert wf.request("PATCH", f"/v1/jobs/{job['id']}/assignment", data=dict(expected_job_version=job["version"], contractor_id=wf.ids["a_other_contractor"])).status_code == 200
        release.set()
        result = retry.result(timeout=10)
    assert result.status_code in {404, 409}
    current = wf.request("GET", f"/v1/cases/{case['id']}").json()
    assert current["max_permission"] == (2 if change == "new_evidence" else 0)
    with wf.service.repository.transaction() as tx:
        assert tx.find("analysis_results", case_id=case["id"])[0]["status"] == "STALE"


def test_concurrent_same_operation_uploads_create_one_evidence_and_provider_call(wf, monkeypatch):
    job, case, ch = wf.setup_case()
    started, release = Event(), Event()
    count = []
    async def provider(source):
        count.append(source.evidence_id)
        started.set()
        assert await asyncio.to_thread(release.wait, 10)
        return PerceptionResult(VisualObservation.model_validate(visual_reply(ch)), "mock-observer-v1", "mock-v1")
    monkeypatch.setattr(wf.provider, "inspect", provider)
    data = image_bytes()
    extra = {"Idempotency-Key": "upload_operation_0001"}
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(wf.upload, case, ch, data, "image/png", "a_contractor", None, extra)
        assert started.wait(10)
        second = pool.submit(wf.upload, case, ch, data, "image/png", "a_contractor", None, extra)
        replayed = second.result(timeout=10)
        assert replayed.status_code == 202
        release.set()
        assert first.result(timeout=10).status_code == 200
    assert len(count) == 1
    with wf.service.repository.transaction() as tx:
        assert len(tx.find("evidence", case_id=case["id"])) == 1
        assert len(tx.find("submission_operations", case_id=case["id"])) == 1


def test_two_distinct_concurrent_uploads_with_same_version_have_one_winner(wf, monkeypatch):
    job, case, ch = wf.setup_case()
    barrier = Barrier(2)
    def upload(index):
        barrier.wait(timeout=10)
        return wf.upload(case, ch, image_bytes(text=f"image {index}"))
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(upload, range(2)))
    assert sorted(response.status_code for response in responses) == [200, 409]
    with wf.service.repository.transaction() as tx:
        assert len(tx.find("evidence", case_id=case["id"])) == 1


def test_manager_rejection_rolls_back_review_case_and_audit_together(wf, monkeypatch):
    job, case, ch = wf.ready()
    original = wf.service._event
    def event(tx, actor, state, kind, *args, **kwargs):
        if kind == "MANAGER_REJECTED_EVIDENCE": raise RuntimeError("private-review-marker")
        return original(tx, actor, state, kind, *args, **kwargs)
    monkeypatch.setattr(wf.service, "_event", event)
    response = wf.reject(case)
    assert response.status_code == 500 and "private-review-marker" not in response.text
    with wf.service.repository.transaction() as tx:
        assert not tx.find("manager_reviews", case_id=case["id"])
        assert tx.get("cases", id=case["id"])["version"] == case["version"]
    monkeypatch.setattr(wf.service, "_event", original)
    assert wf.approve(case).status_code == 200
