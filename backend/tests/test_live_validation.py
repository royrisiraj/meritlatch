"""Offline SDK/transport fixtures only. No real key, human consent or inference."""

import asyncio
from argparse import Namespace
from hashlib import sha256
import json
from pathlib import Path
import socket

import httpx2
import pytest
from PIL import Image
from pydantic import SecretStr

from backend.app.gemini_provider import GeminiPerceptionProvider
from backend.app.perception import PerceptionInput, ProviderError
from backend.app.settings import Settings
from backend.tools import smoke_gemini
from backend.tools.live_validation_guard import SingleRequestGuard, DenySyncTransport


FIELDS = dict(asset_id_observed="PUMP-042", challenge_text_observed="FICTIONAL-TEST-CHALLENGE",
    pressure_value=35, pressure_unit="PSI", equipment_status="RUNNING",
    calibration_expiry_date="2099-12-31", uncertain_fields=[], conflicting_fields=[])


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    original_connect = socket.socket.connect
    def blocked(*args, **kwargs):
        raise AssertionError("Offline validation tests must not open external network sockets")
    def local_event_loop_only(sock, address):
        # Windows ProactorEventLoop creates its self-pipe using loopback TCP.
        if isinstance(address, tuple) and address[0] == "127.0.0.1":
            return original_connect(sock, address)
        return blocked()
    monkeypatch.setattr(socket.socket, "connect", local_event_loop_only)
    monkeypatch.setattr(socket, "create_connection", blocked)


def settings():
    return Settings(provider_mode="LIVE_GEMINI", gemini_model="gemini-3.8-flash",
        gemini_api_key=SecretStr("OFFLINE_TEST_NOT_A_REAL_API_KEY"), allow_billable=True, provider_attempts=1)


def sdk_response(fields=None):
    return dict(candidates=[dict(content=dict(role="model", parts=[dict(text=json.dumps(fields or FIELDS))]), finishReason="STOP")],
        modelVersion="gemini-3.8-flash-OFFLINE_STUB", usageMetadata=dict(promptTokenCount=12, candidatesTokenCount=22, totalTokenCount=34))


def invoke(guard):
    provider = GeminiPerceptionProvider(settings(), guard.client_factory)
    return asyncio.run(provider.inspect(PerceptionInput(b"OFFLINE_STUB_IMAGE_BYTES", "image/png", "offline-fixture")))


def test_real_installed_sdk_uses_single_guarded_request_no_answers_or_tools():
    captured = []
    def handler(request):
        captured.append(json.loads(request.content))
        return httpx2.Response(200, json=sdk_response())
    guard = SingleRequestGuard(transport=httpx2.MockTransport(handler))
    result = invoke(guard)
    assert guard.request_count == len(captured) == 1
    assert result.model_id == "gemini-3.8-flash" and result.fields.pressure_value == 35
    assert guard.response_metadata["usage"]["totalTokenCount"] == 34
    config = captured[0]["generationConfig"]
    # Installed google-genai 3.2.0 forwards this nested protobuf config using
    # original field names; ProtoJSON parsers accept original and JSON names.
    assert config["thinkingConfig"] == {"thinking_level": "LOW", "include_thoughts": False}
    assert config["maxOutputTokens"] == 2048
    assert not captured[0].get("tools")
    assert "PUMP-042" not in json.dumps(captured[0])
    assert "FICTIONAL-TEST-CHALLENGE" not in json.dumps(captured[0])


@pytest.mark.parametrize("status,reason", [(401,"PROVIDER_AUTH"), (404,"PROVIDER_UNAVAILABLE"),
    (429,"PROVIDER_QUOTA"), (503,"PROVIDER_UNAVAILABLE"), (302,"PROVIDER_UNAVAILABLE")])
def test_sdk_failure_and_redirect_never_retry_or_expose_diagnostics(status, reason, caplog):
    calls = []
    def handler(request):
        calls.append(1)
        return httpx2.Response(status, headers={"Location": "https://generativelanguage.googleapis.com/other"},
            json={"error": {"code": status, "message": "PRIVATE_DIAGNOSTIC_MARKER"}})
    guard = SingleRequestGuard(transport=httpx2.MockTransport(handler))
    with pytest.raises(ProviderError) as exc:
        invoke(guard)
    assert exc.value.code == reason
    assert guard.request_count == len(calls) == 1
    assert "PRIVATE_DIAGNOSTIC_MARKER" not in str(exc.value) + caplog.text


def test_transport_blocks_a_second_send_even_if_caller_attempts_it():
    calls = []
    async def run():
        guard = SingleRequestGuard(transport=httpx2.MockTransport(lambda r: calls.append(1) or httpx2.Response(200, json={})))
        async with httpx2.AsyncClient(transport=guard, follow_redirects=False) as client:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
            await client.post(url, json={})
            with pytest.raises(RuntimeError, match="budget exhausted"):
                await client.post(url, json={})
        assert guard.request_count == 1
    asyncio.run(run())
    assert len(calls) == 1


@pytest.mark.parametrize("url", ["http://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
    "https://example.com/v1beta/models/gemini-3.8-flash:generateContent",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key=secret",
    "https://generativelanguage.googleapis.com/v1beta/models"])
def test_transport_rejects_other_destinations_before_any_send(url):
    async def run():
        guard = SingleRequestGuard(transport=httpx2.MockTransport(lambda r: pytest.fail("Unexpected outbound request")))
        with pytest.raises(RuntimeError, match="approved inference endpoint"):
            await guard.handle_async_request(httpx2.Request("POST", url))
        assert guard.request_count == 0
        await guard.aclose()
    asyncio.run(run())


def test_validation_sync_transport_and_model_fallback_are_disabled():
    with pytest.raises(RuntimeError, match="Synchronous"):
        DenySyncTransport().handle_request(httpx2.Request("GET", "https://example.com"))
    with pytest.raises(ValueError, match="only gemini-3.8-flash"):
        SingleRequestGuard("gemini-flash-latest")


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    root = tmp_path / "fixtures/live_inputs/sample"
    root.mkdir(parents=True)
    image = root / "card.png"
    Image.new("RGB", (32,32), "white").save(image)
    truth_path = root / "truth.json"
    truth = dict(origin="CONSENTED_FICTIONAL_NO_CUSTOMER_DATA", human_reviewed=False,
        reviewed_by="REPLACE_WITH_HUMAN_REVIEWER", validation_model="gemini-3.8-flash",
        image_sha256=sha256(image.read_bytes()).hexdigest(), expected_observation=FIELDS,
        policy_context=dict(tenant_id="synthetic-org-a", job_id="synthetic-job-001", asset_id_expected="PUMP-042",
            approved_policy_version="1.0.0", expected_challenge="FICTIONAL-TEST-CHALLENGE",
            challenge_expires_at="2026-11-12T07:00:00Z", evaluated_at="2026-11-12T06:00:00Z"))
    truth_path.write_text(json.dumps(truth), encoding="utf-8")
    # Policy path is source-controlled; inputs are isolated test-owned files.
    (tmp_path / "policies").mkdir()
    (tmp_path / "policies/maintenance_v1.json").write_bytes((smoke_gemini.ROOT / "policies/maintenance_v1.json").read_bytes())
    monkeypatch.setattr(smoke_gemini, "ROOT", tmp_path)
    monkeypatch.setattr(smoke_gemini, "ignored", lambda path: True)
    monkeypatch.setenv("GEMINI_API_KEY", "OFFLINE_TEST_NOT_A_REAL_API_KEY")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.8-flash")
    monkeypatch.setenv("SENTINEL_PROVIDER_MODE", "LIVE_GEMINI")
    monkeypatch.setenv("SENTINEL_ALLOW_BILLABLE", "true")
    monkeypatch.setenv("SENTINEL_PROVIDER_ATTEMPTS", "1")
    monkeypatch.setenv("SENTINEL_ALLOW_SYNTHETIC", "false")
    args = Namespace(image=image, ground_truth=truth_path, output=root/"report.local.json", env_file=None)
    return args, truth


def reviewed(prepared):
    args, truth = prepared
    truth.update(human_reviewed=True, reviewed_by="OFFLINE_TEST_REVIEW_FIXTURE_NOT_REAL_CONSENT")
    truth["human_review_sha256"] = smoke_gemini.review_digest(truth)
    args.ground_truth.write_text(json.dumps(truth), encoding="utf-8")
    return args


def test_preflight_reports_human_review_block_without_provider_or_writes(prepared, monkeypatch):
    args, _ = prepared
    monkeypatch.setattr(smoke_gemini, "GeminiPerceptionProvider", lambda *a,**k: pytest.fail("No provider during preflight"))
    report, payload = smoke_gemini.preflight(args)
    assert report["reason_codes"] == ["HUMAN_IMAGE_AND_GROUND_TRUTH_REVIEW_REQUIRED"]
    assert report["checks"]["GEMINI_API_KEY_PRESENT"] is True
    assert report["checks"]["expected_fixture_policy_max_permission"] == 2
    assert report["request_count"] == 0 and report["network_called"] is False
    assert not args.output.exists() and not payload[-1].exists()


def test_reviewed_preflight_is_ready_without_spending_request_budget(prepared):
    args = reviewed(prepared)
    report, payload = smoke_gemini.preflight(args)
    assert report["status"] == "READY" and report["request_count"] == 0
    assert not payload[-1].exists()


@pytest.mark.parametrize("setting,value", [("GEMINI_MODEL","gemini-3.6-flash"), ("SENTINEL_PROVIDER_ATTEMPTS","2"),
    ("SENTINEL_PROVIDER_MODE","MOCK_AI")])
def test_preflight_requires_exact_configuration(prepared, monkeypatch, setting, value):
    args = reviewed(prepared)
    monkeypatch.setenv(setting, value)
    report, _ = smoke_gemini.preflight(args)
    assert report["status"] == "BLOCKED"
    assert "EXACT_MODEL_LIVE_MODE_AND_ONE_ATTEMPT_REQUIRED" in report["reason_codes"]


def test_image_changed_after_ground_truth_binding_blocks_preflight(prepared):
    args = reviewed(prepared)
    Image.new("RGB", (32,32), "red").save(args.image)
    report, _ = smoke_gemini.preflight(args)
    assert "IMAGE_DIGEST_AND_MODEL_BINDING_REQUIRED" in report["reason_codes"]


def test_expected_values_changed_after_confirmation_require_new_human_review(prepared):
    args = reviewed(prepared)
    truth = json.loads(args.ground_truth.read_text())
    truth["expected_observation"]["pressure_value"] = 36  # Still policy-compliant, but not reviewed.
    args.ground_truth.write_text(json.dumps(truth), encoding="utf-8")
    report, _ = smoke_gemini.preflight(args)
    assert "HUMAN_REVIEW_BINDING_MISSING_OR_CHANGED" in report["reason_codes"]
    assert report["request_count"] == 0


@pytest.mark.parametrize("kind", ["match", "wrong_reading", "provider_error", "schema_error"])
def test_runner_single_request_guard_and_persistent_no_retry_marker(prepared, monkeypatch, capsys, kind):
    args = reviewed(prepared)
    calls = []
    def handler(request):
        calls.append(1)
        if kind == "provider_error":
            return httpx2.Response(503, json={"error": {"code":503,"message":"PRIVATE_MARKER"}})
        fields = {**FIELDS, "pressure_value":36} if kind == "wrong_reading" else {"permission":3} if kind == "schema_error" else FIELDS
        return httpx2.Response(200, json=sdk_response(fields))
    monkeypatch.setattr(smoke_gemini, "SingleRequestGuard", lambda model: SingleRequestGuard(model, httpx2.MockTransport(handler)))
    def argv(output):
        return ["smoke", "--allow-billable", "--confirm-fictional-consent", "--image", str(args.image),
            "--ground-truth", str(args.ground_truth), "--output", str(output)]
    monkeypatch.setattr("sys.argv", argv(args.output))
    assert smoke_gemini.main() == (0 if kind == "match" else 1)
    report = json.loads(args.output.read_text())
    assert report["request_count"] == 1 and report["retry_count"] == 0 and len(calls) == 1
    if kind == "wrong_reading":
        assert report["validation_result"].startswith("PARTIAL")
        assert report["authorization_decision"]["max_permission"] == 2  # False but compliant observation risk.
        assert report["ground_truth_comparison"]["pressure_value"] is False
    if kind in {"provider_error", "schema_error"}:
        assert report["status"] == "FAILED" and report["authorization_decision"] == "DENY"
    monkeypatch.setattr("sys.argv", argv(args.output.parent / "another_output.local.json"))
    assert smoke_gemini.main() == 2
    assert len(calls) == 1  # Changing output cannot consume a second inference.
    assert "PRIVATE_MARKER" not in capsys.readouterr().out
