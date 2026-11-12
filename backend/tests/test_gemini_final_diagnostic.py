"""Offline-only status/TLS diagnostics; no real key or network request."""

import json
import ssl

import httpx2
import pytest
from dotenv import load_dotenv

from backend.app.perception import ProviderError
from backend.tools.live_validation_guard import SingleRequestGuard
from backend.tools import smoke_gemini
from backend.tests.test_live_validation import invoke, no_network, prepared, reviewed


@pytest.mark.parametrize("status,category,code", [
    (400,"REQUEST_ERROR","PROVIDER_UNAVAILABLE"),
    (401,"AUTHENTICATION_FAILURE","PROVIDER_AUTH"),
    (403,"PERMISSION_FAILURE","PROVIDER_AUTH"),
    (404,"MODEL_OR_ENDPOINT_NOT_FOUND","PROVIDER_UNAVAILABLE"),
    (408,"REQUEST_TIMEOUT","PROVIDER_UNAVAILABLE"),
    (429,"RATE_LIMIT","PROVIDER_QUOTA"),
    (500,"SERVER_FAILURE","PROVIDER_UNAVAILABLE"),
    (503,"SERVER_FAILURE","PROVIDER_UNAVAILABLE"),
    (302,"REDIRECT_BLOCKED","PROVIDER_UNAVAILABLE"),
    (422,"HTTP_ERROR","PROVIDER_UNAVAILABLE")])
def test_http_diagnostics_preserve_safe_status_without_payload_or_retry(status,category,code,caplog):
    calls=[]
    def response(request):
        calls.append(1)
        return httpx2.Response(status, headers={"Location":"https://private.example/secret"},
            json={"error":{"code":status,"message":"SECRET_PROVIDER_BODY_MARKER"}})
    guard=SingleRequestGuard(transport=httpx2.MockTransport(response))
    with pytest.raises(ProviderError) as caught:
        invoke(guard)
    assert caught.value.code==code  # Preserve all accepted public error contracts.
    assert guard.response_metadata=={"http_status":status,"error_category":category}
    assert guard.request_count==len(calls)==1
    assert "SECRET_PROVIDER_BODY_MARKER" not in str(caught.value)+caplog.text+json.dumps(guard.response_metadata)
    assert "private.example" not in json.dumps(guard.response_metadata)


@pytest.mark.parametrize("kind,category,code", [
    ("connect","TRANSPORT_FAILURE","PROVIDER_FAILED"),
    ("tls","TLS_FAILURE","PROVIDER_FAILED"),
    ("timeout","TRANSPORT_TIMEOUT","PROVIDER_TIMEOUT")])
def test_transport_diagnostics_use_types_not_secret_messages(kind,category,code):
    def failure(request):
        if kind=="tls":
            raise httpx2.ConnectError("SECRET_TRANSPORT_MARKER") from ssl.SSLCertVerificationError("SECRET_CERT_MARKER")
        if kind=="timeout":
            raise httpx2.ReadTimeout("SECRET_TRANSPORT_MARKER")
        raise httpx2.ConnectError("SECRET_TRANSPORT_MARKER")
    guard=SingleRequestGuard(transport=httpx2.MockTransport(failure))
    with pytest.raises(ProviderError) as caught:
        invoke(guard)
    assert caught.value.code==code
    assert guard.response_metadata=={"error_category":category}
    assert guard.request_count==1
    assert "SECRET" not in json.dumps(guard.response_metadata)+str(caught.value)


def test_failed_validation_runner_persists_safe_status_without_second_send(prepared,monkeypatch,capsys):
    args=reviewed(prepared)
    calls=[]
    def failure(request):
        calls.append(1)
        return httpx2.Response(400,json={"error":{"code":400,"message":"SECRET_REQUEST_MARKER"}})
    monkeypatch.setattr(smoke_gemini,"SingleRequestGuard",lambda model:SingleRequestGuard(model,httpx2.MockTransport(failure)))
    monkeypatch.setattr("sys.argv",["smoke","--allow-billable","--confirm-fictional-consent",
        "--image",str(args.image),"--ground-truth",str(args.ground_truth),"--output",str(args.output)])
    assert smoke_gemini.main()==1
    data=json.loads(args.output.read_text())
    assert data["transport_metadata"]=={"http_status":400,"error_category":"REQUEST_ERROR"}
    assert data["authorization_decision"]=="DENY" and data["request_count"]==1 and data["retry_count"]==0
    assert smoke_gemini.main()==2 and len(calls)==1
    assert "SECRET_REQUEST_MARKER" not in capsys.readouterr().out


def test_dotenv_preserves_process_credential_precedence_with_dummy_values(tmp_path,monkeypatch):
    env=tmp_path/"test.env"
    env.write_text("GEMINI_API_KEY=OFFLINE_FILE_DUMMY\n",encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY","OFFLINE_PROCESS_DUMMY")
    load_dotenv(env,override=False)
    import os
    assert os.environ["GEMINI_API_KEY"]=="OFFLINE_PROCESS_DUMMY"
    monkeypatch.delenv("GEMINI_API_KEY")
    load_dotenv(env,override=False)
    assert os.environ["GEMINI_API_KEY"]=="OFFLINE_FILE_DUMMY"
