"""Actual authenticated image POST through backend.app.api:create_app, MOCK_AI only."""

from io import BytesIO
import json
from pathlib import Path
import secrets
import socket
from tempfile import TemporaryDirectory
from threading import Thread
import time

import httpx
from PIL import Image, ImageDraw
import uvicorn

from backend.app.api import create_app
from backend.app.settings import Settings
from backend.app.perception import MockPerceptionProvider
from backend.app.provisioning import provision_user


def main():
    with TemporaryDirectory(prefix="sentinel-phase02-smoke-") as folder:
        root = Path(folder)
        provider = MockPerceptionProvider()
        app = create_app(Settings(database_path=root / "smoke.sqlite", media_root=root / "private",
                                 provider_mode="MOCK_AI"), perception_provider=provider)
        service = app.state.service
        passwords, ids = {}, {}
        for name, role in (("contractor", "CONTRACTOR"), ("manager", "MANAGER"), ("engineer", "ENGINEER"), ("agent", "SERVICE_AGENT")):
            passwords[name] = secrets.token_urlsafe(24)
            ids[name] = provision_user(service.repository, "smoke-fictional", name, role, passwords[name])["id"]
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False))
        thread = Thread(target=lambda: server.run(sockets=[listener]), daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and thread.is_alive() and time.monotonic() < deadline:
                time.sleep(0.02)
            if not server.started: raise RuntimeError("Smoke listener did not start")
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=10) as client:
                tokens = {}
                def request(method, path, role=None, data=None, status=200):
                    response = client.request(method, path, headers={"Authorization": "Bearer " + tokens[role]} if role else {}, json=data)
                    assert response.status_code == status, f"Unexpected HTTP status {response.status_code}"
                    return response
                request("GET", "/healthz")
                request("GET", "/docs")
                for name in passwords:
                    tokens[name] = request("POST", "/v1/auth/login", data=dict(tenant_id="smoke-fictional", username=name, password=passwords[name])).json()["access_token"]
                job = request("POST", "/v1/jobs", "manager", dict(asset_id="PUMP-042", contractor_id=ids["contractor"], engineer_id=ids["engineer"], service_agent_id=ids["agent"]), 201).json()
                case = request("POST", "/v1/cases", "manager", dict(job_id=job["id"], invoice_amount_paise=500000), 201).json()
                challenge = request("POST", f"/v1/jobs/{job['id']}/challenges", "contractor", dict(case_id=case["id"], expected_case_version=case["version"])).json()
                provider.reply = dict(asset_id_observed="PUMP-042", challenge_text_observed=challenge["token"], pressure_value=35.0,
                    pressure_unit="PSI", equipment_status="RUNNING", calibration_expiry_date="2099-12-31", uncertain_fields=[], conflicting_fields=[])
                image = Image.new("RGB", (700, 260), "white")
                drawing = ImageDraw.Draw(image)
                drawing.multiline_text((15, 15), "FICTIONAL TEST CARD - NO INDUSTRIAL SAFETY CLAIM\nPUMP-042\n35 PSI\nRUNNING\nCalibration: 2099-12-31\nChallenge: " + challenge["token"], fill="black", spacing=10)
                buffer = BytesIO()
                image.save(buffer, "JPEG", quality=95)
                image_data = buffer.getvalue()
                headers = {"Authorization": "Bearer " + tokens["contractor"], "Content-Type": "image/jpeg",
                    "X-Expected-Case-Version": str(challenge["case_version"]), "X-Challenge-ID": challenge["id"], "X-Evidence-Session-ID": challenge["evidence_session_id"]}
                response = client.post(f"/v1/cases/{case['id']}/evidence", headers=headers, content=image_data)
                assert response.status_code == 200
                value = response.json()
                assert value["max_permission"] == 2 and value["provider_mode"] == "MOCK_AI"
                print("HTTP health/docs 200; authenticated JPEG POST 200; actual application factory backend.app.api:create_app")
                print(json.dumps({k: value[k] for k in ("version", "evidence_version", "provider_mode", "model_id", "inspection_status", "max_permission", "decision", "reason_codes", "observation")}, sort_keys=True))
                completion = request("POST", f"/v1/cases/{case['id']}/actions/evaluate", "agent", dict(expected_case_version=value["version"], action="complete_simulated_action")).json()
                assert completion["decision"] == "DENY"
                request("POST", f"/v1/cases/{case['id']}/approvals", "contractor", dict(expected_case_version=value["version"]), 403)
                content = request("GET", f"/v1/cases/{case['id']}/evidence/{value['evidence_id']}/content", "manager")
                assert content.content == image_data
                headers["X-Expected-Case-Version"] = str(value["version"])
                duplicate = client.post(f"/v1/cases/{case['id']}/evidence", headers=headers, content=image_data)
                assert duplicate.status_code == 409 and duplicate.json()["reason_codes"] == ["EXACT_DUPLICATE"]
                print("L3 DENY without manager approval; contractor approval 403; scoped private read 200; exact duplicate 409")
                print("PASS MOCK_AI: real image bytes and HTTP; mock does not measure visual extraction accuracy. No live Gemini call.")
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            listener.close()
            service.repository.close()
            if thread.is_alive(): raise RuntimeError("Smoke listener failed to stop")


if __name__ == "__main__": main()
