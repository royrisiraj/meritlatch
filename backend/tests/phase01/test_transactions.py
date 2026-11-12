from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier, Event

import pytest

from backend.app.errors import AppError
from backend.app.models import Action


@pytest.mark.parametrize("first", ["approval", "evidence", "simultaneous"])
def test_concurrent_approval_and_evidence_replacement_cannot_restore_stale_approval(world, first):
    job, case, ch = world.ready()
    barrier = Barrier(2)
    finished_first = Event()

    def operation(kind):
        barrier.wait(timeout=10)
        if first != "simultaneous" and first != kind:
            assert finished_first.wait(timeout=10)
        try:
            if kind == "approval":
                value = world.service.approve(world.tokens["a_manager"], case["id"], case["version"])
            else:
                value = world.inject(case, ch, {"pressure_value": 36}, expected=case["version"])
            return 200, value
        except AppError as exc:
            return exc.status, exc.code
        finally:
            if kind == first:
                finished_first.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        approval = pool.submit(operation, "approval")
        replacement = pool.submit(operation, "evidence")
        approval_result, evidence_result = approval.result(timeout=15), replacement.result(timeout=15)
    assert sorted([approval_result[0], evidence_result[0]]) == [200, 409]
    current = world.service.get_case(world.tokens["a_manager"], case["id"])
    if evidence_result[0] == 409:
        # Approval won. Replacement was rejected, so retry with current version.
        assert current["evidence_sha256"] == case["evidence_sha256"]
        current = world.inject(case, ch, {"pressure_value": 36}, expected=current["version"])
    assert current["evidence_sha256"] != case["evidence_sha256"]
    assert current["max_permission"] == 2
    with world.service.repository.transaction() as tx:
        persisted = tx.get("cases", id=case["id"])
        assert persisted["approval_id"] is None
        current_ev = tx.get("evidence", id=persisted["evidence_id"])
        assert current_ev["sha256"] == current["evidence_sha256"]
    assert world.act(current, "complete_simulated_action", execute=True).json()["decision"] == "DENY"


def test_concurrent_manager_approvals_have_one_winner(world):
    job, case, ch = world.ready()
    barrier = Barrier(2)

    def approve():
        barrier.wait(timeout=10)
        try:
            world.service.approve(world.tokens["a_manager"], case["id"], case["version"])
            return 200
        except AppError as exc:
            return exc.status

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: approve(), range(2)))
    assert sorted(results) == [200, 409]
    with world.service.repository.transaction() as tx:
        assert len(tx.find("approvals", case_id=case["id"])) == 1


def test_concurrent_completion_has_one_persistent_receipt(world):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    barrier = Barrier(4)

    def execute():
        barrier.wait(timeout=10)
        return world.service.action(world.tokens["a_agent"], case["id"], approved["version"], Action.COMPLETE_SIMULATED_ACTION, True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: execute(), range(4)))
    assert all(status == 200 and value["decision"] == "ALLOW" for status, value in results)
    assert len({value["receipt_id"] for _, value in results}) == 1
    assert sum(not value["already_executed"] for _, value in results) == 1
    with world.service.repository.transaction() as tx:
        assert len(tx.find("action_runs", case_id=case["id"], action="complete_simulated_action")) == 1


@pytest.mark.parametrize("first", ["completion", "replacement"])
def test_completion_racing_with_replacement_never_authorizes_new_evidence(world, first):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    barrier, done = Barrier(2), Event()

    def run(kind):
        barrier.wait(timeout=10)
        if kind != first:
            assert done.wait(timeout=10)
        try:
            if kind == "completion":
                return world.service.action(world.tokens["a_agent"], case["id"], approved["version"], Action.COMPLETE_SIMULATED_ACTION, True)
            return 200, world.inject(case, ch, {"pressure_value": 36}, expected=approved["version"])
        finally:
            if kind == first:
                done.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        completion = pool.submit(run, "completion")
        replacement = pool.submit(run, "replacement")
        completed, replaced = completion.result(timeout=15), replacement.result(timeout=15)
    assert replaced[0] == 200
    current = world.service.get_case(world.tokens["a_manager"], case["id"])
    assert current["max_permission"] == 2
    assert current["simulated_completed"] is False
    assert world.act(current, "complete_simulated_action", execute=True).json()["decision"] == "DENY"
    if first == "replacement":
        assert completed[0] == 409
    else:
        assert completed[1]["decision"] == "ALLOW"  # Receipt applies to the old reviewed version only.


def test_transaction_rolls_back_approval_case_and_event_on_failure(world, monkeypatch):
    job, case, ch = world.ready()
    original = world.service._event
    def failure(*args, **kwargs):
        raise RuntimeError("private-untrusted-exception-marker")
    monkeypatch.setattr(world.service, "_event", failure)
    response = world.approve(case)
    assert response.status_code == 500
    assert "private-untrusted" not in response.text
    with world.service.repository.transaction() as tx:
        current = tx.get("cases", id=case["id"])
        assert current["version"] == case["version"]
        assert current["approval_id"] is None
        assert tx.find("approvals", case_id=case["id"]) == []
    monkeypatch.setattr(world.service, "_event", original)
    assert world.approve(case).status_code == 200


def test_authorization_samples_server_clock_after_waiting_for_transaction_lock(world, monkeypatch):
    job, case, ch = world.ready()
    approved = world.approve(case).json()
    original = world.service.repository.transaction

    @contextmanager
    def lock_wait():
        with original() as tx:
            world.clock.advance(300)  # Simulate expiry while waiting for the DB lock.
            yield tx

    monkeypatch.setattr(world.service.repository, "transaction", lock_wait)
    status, result = world.service.action(world.tokens["a_agent"], case["id"], approved["version"], Action.COMPLETE_SIMULATED_ACTION, True)
    assert status == 409
    assert result["decision"] == "DENY"
    monkeypatch.setattr(world.service.repository, "transaction", original)
    with original() as tx:
        assert tx.get("cases", id=case["id"])["approval_id"] is None
        assert not tx.find("action_runs", case_id=case["id"])
