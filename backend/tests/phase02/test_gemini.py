from dataclasses import replace
import asyncio
import json
from types import SimpleNamespace

import pytest
from pydantic import SecretStr
from google.genai import errors

from backend.app.gemini_provider import GeminiPerceptionProvider, OBSERVER_INSTRUCTIONS
from backend.app.perception import PerceptionInput, ProviderError
from backend.app.settings import Settings
from .conftest import visual_reply


class SDKStub:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []
        self.closed = False
        self.aio = self
        self.models = self

    async def __aenter__(self): return self
    async def __aexit__(self, *args): return False
    def close(self): self.closed = True

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        result = next(self.responses)
        if isinstance(result, Exception): raise result
        return result


def live_settings(**changes):
    return Settings(provider_mode="LIVE_GEMINI", gemini_api_key=SecretStr("unit-test-not-a-real-key"), allow_billable=True, **changes)


def invoke(stub, settings=None):
    received = []
    def factory(**kwargs):
        received.append(kwargs)
        return stub
    provider = GeminiPerceptionProvider(settings or live_settings(), factory)
    result = asyncio.run(provider.inspect(PerceptionInput(b"image-data-not-network", "image/png", "evidence-test")))
    return result, received


def test_sdk_transport_receives_actual_bytes_schema_and_no_authorizing_tools():
    payload = visual_reply({"token": "observed-only-from-image"})
    stub = SDKStub([SimpleNamespace(text=json.dumps(payload), model_version="gemini-3.6-flash-verified-stub")])
    result, received = invoke(stub)
    assert result.fields.pressure_value == 35
    assert result.model_id == "gemini-3.6-flash"
    assert result.model_version == "gemini-3.6-flash-verified-stub"
    assert received[0]["http_options"].timeout == 20000
    assert received[0]["http_options"].retry_options.attempts == 1
    assert received[0]["vertexai"] is False and received[0]["enterprise"] is False
    call = stub.calls[0]
    assert call["contents"][0].inline_data.data == b"image-data-not-network"
    assert call["config"].tools == []
    assert call["config"].automatic_function_calling.disable is True
    assert call["config"].automatic_continuation is False
    assert call["config"].response_mime_type == "application/json"
    assert "max_permission" not in call["config"].response_json_schema["properties"]
    assert "observed-only-from-image" not in call["config"].system_instruction
    assert "unit-test-not-a-real-key" not in repr(call)
    assert stub.closed


@pytest.mark.parametrize("payload,reason", [("not JSON", "PROVIDER_INVALID_OBSERVATION"),
    ('{"max_permission":3}', "PROVIDER_INVALID_OBSERVATION"), (None, "PROVIDER_BLOCKED"),
    ("x" * 17000, "PROVIDER_INVALID_OBSERVATION")])
def test_invalid_or_blocked_sdk_responses(payload, reason):
    with pytest.raises(ProviderError) as exc:
        invoke(SDKStub([SimpleNamespace(text=payload, model_version=None)]))
    assert exc.value.code == reason


@pytest.mark.parametrize("code,reason", [(401, "PROVIDER_AUTH"), (403, "PROVIDER_AUTH"),
    (404, "PROVIDER_UNAVAILABLE"), (429, "PROVIDER_QUOTA"), (503, "PROVIDER_UNAVAILABLE")])
def test_sdk_error_classification_never_exposes_exception_text(code, reason):
    stub = SDKStub([errors.APIError(code, {"error": {"message": "private-key-or-customer-marker"}})])
    with pytest.raises(ProviderError) as exc:
        invoke(stub)
    assert exc.value.code == reason
    assert "private-key" not in str(exc.value)
    assert len(stub.calls) == 1


def test_retries_are_explicit_bounded_and_do_not_retry_quota_errors():
    success = SimpleNamespace(text=json.dumps(visual_reply({"token": "observed"})), model_version=None)
    retry = SDKStub([errors.APIError(503, {}), success])
    result, _ = invoke(retry, live_settings(provider_attempts=2))
    assert len(retry.calls) == 2 and result.fields.pressure_value == 35
    quota = SDKStub([errors.APIError(429, {}), success])
    with pytest.raises(ProviderError): invoke(quota, live_settings(provider_attempts=2))
    assert len(quota.calls) == 1


def test_no_live_configuration_without_key_and_explicit_billing_approval():
    with pytest.raises(ValueError, match="explicit"):
        Settings(provider_mode="LIVE_GEMINI", gemini_api_key=SecretStr("unit-test-key"))
    with pytest.raises(ValueError): Settings(provider_mode="LIVE_GEMINI", allow_billable=True)
    with pytest.raises(ValueError): Settings(provider_mode="AUTO")
    with pytest.raises(ValueError): Settings(provider_timeout_seconds=61)
    with pytest.raises(ValueError): Settings(provider_attempts=3)
    with pytest.raises(ValueError): Settings(gemini_model="https://untrusted.example/model?key=secret")
    assert "unit-test-not-a-real-key" not in repr(live_settings())


def test_sdk_deadline_and_transport_timeout_are_redacted():
    import httpx2
    timed_out = SDKStub([httpx2.ReadTimeout("private-timeout-marker")])
    with pytest.raises(ProviderError) as exc:
        invoke(timed_out)
    assert exc.value.code == "PROVIDER_TIMEOUT"
    assert "private-timeout" not in str(exc.value)
    class SlowSDK(SDKStub):
        async def generate_content(self, **kwargs):
            await asyncio.sleep(5)
    slow = SlowSDK([])
    with pytest.raises(ProviderError) as exc:
        invoke(slow, live_settings(provider_timeout_seconds=0.01))
    assert exc.value.code == "PROVIDER_TIMEOUT"
    assert slow.closed
