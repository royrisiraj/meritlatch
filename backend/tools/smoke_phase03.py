"""True TCP/HTTP workflow scenarios with an internal, labeled mock observer.

Only identity provisioning and fixture configuration are local setup. Every
business transition uses the existing authenticated FastAPI factory over HTTP.
"""

import argparse
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
from backend.app.perception import MockPerceptionProvider, ProviderError
from backend.app.provisioning import provision_user
from backend.app.settings import Settings


class ScenarioObserver(MockPerceptionProvider):
    def __init__(self):
        super().__init__()
        self.fail_next = False

    async def inspect(self, source):
        if self.fail_next:
            self.fail_next = False
            raise ProviderError("PROVIDER_UNAVAILABLE")
        return await super().inspect(source)


class Journey:
    def __init__(self, client, provider, ids, passwords):
        self.client, self.provider, self.ids, self.passwords = client, provider, ids, passwords
        self.tokens = {}

    def login(self, name):
        tenant = "smoke-b" if name == "other_manager" else "smoke-a"
        response = self.client.post("/v1/auth/login", json=dict(tenant_id=tenant, username=name, password=self.passwords[name]))
        assert response.status_code == 200
        self.tokens[name] = response.json()["access_token"]

    def call(self, method, path, name="manager", data=None, status=200):
        response = self.client.request(method, path, headers={"Authorization": "Bearer " + self.tokens[name]}, json=data)
        assert response.status_code == status, f"Unexpected status {response.status_code} for {method}"
        return response

    def new(self):
        selected = self.call("GET", "/v1/policy-templates").json()[0]
        job = self.call("POST", "/v1/jobs", data=dict(asset_id="PUMP-042", contractor_id=self.ids["spare_contractor"],
            engineer_id=self.ids["engineer"], service_agent_id=self.ids["agent"], policy_id=selected["policy_id"],
            policy_version=selected["version"], invoice_amount_paise=500000), status=201).json()
        job = self.call("PATCH", f"/v1/jobs/{job['id']}/assignment", data=dict(expected_job_version=job["version"], contractor_id=self.ids["contractor"])).json()
        case = self.call("POST", "/v1/cases", data={"job_id": job["id"]}, status=201).json()
        assert case["max_permission"] == 0 and case["invoice_amount_paise"] == 500000
        denied = self.action(case, "prepare_invoice")
        assert denied["decision"] == "DENY"
        return job, case

    def challenge(self, job, case):
        return self.call("POST", f"/v1/jobs/{job['id']}/challenges", "contractor",
            dict(case_id=case["id"], expected_case_version=case["version"])).json()

    def image(self, challenge, asset="PUMP-042", pressure=35.0, label="fictional"):
        self.provider.reply = dict(asset_id_observed=asset, challenge_text_observed=challenge["token"], pressure_value=pressure,
            pressure_unit="PSI", equipment_status="RUNNING", calibration_expiry_date="2099-12-31", uncertain_fields=[], conflicting_fields=[])
        image = Image.new("RGB", (800, 300), "white")
        ImageDraw.Draw(image).multiline_text((10, 10), f"FICTIONAL CANNED MOCK TEST CARD - {label}\n{asset}\n{pressure} PSI\nRUNNING\nCalibration 2099-12-31\n" + challenge["token"], fill="black", spacing=12)
        output = BytesIO()
        image.save(output, "JPEG", quality=95)
        return output.getvalue()

    def upload(self, case, challenge, data, status=200, operation=None):
        headers = {"Authorization": "Bearer " + self.tokens["contractor"], "Content-Type": "image/jpeg",
            "X-Expected-Case-Version": str(challenge["case_version"]), "X-Challenge-ID": challenge["id"], "X-Evidence-Session-ID": challenge["evidence_session_id"]}
        if operation: headers["Idempotency-Key"] = operation
        response = self.client.post(f"/v1/cases/{case['id']}/evidence", headers=headers, content=data)
        assert response.status_code == status, f"Unexpected upload status {response.status_code}"
        return response.json()

    def action(self, case, action, execute=False, status=200):
        return self.call("POST", f"/v1/cases/{case['id']}/actions/{'execute' if execute else 'evaluate'}", "agent",
            dict(expected_case_version=case["version"], action=action), status).json()

    def approve_complete(self, case):
        assert self.action(case, "prepare_invoice", True)["decision"] == "ALLOW"
        assert self.action(case, "complete_simulated_action")["decision"] == "DENY"
        self.call("POST", f"/v1/cases/{case['id']}/approvals", "contractor", dict(expected_case_version=case["version"]), 403)
        approved = self.call("POST", f"/v1/cases/{case['id']}/approvals", data=dict(expected_case_version=case["version"])).json()
        assert approved["max_permission"] == 3
        first = self.action(approved, "complete_simulated_action", True)
        second = self.action(approved, "complete_simulated_action", True)
        assert first["receipt_id"] == second["receipt_id"] and second["already_executed"]
        done = self.call("GET", f"/v1/cases/{case['id']}").json()
        assert done["business_status"] == "COMPLETED"
        return done

    def audit(self, case, challenge):
        response = self.call("GET", f"/v1/cases/{case['id']}/audit")
        assert challenge["token"] not in response.text and challenge["evidence_session_id"] not in response.text
        assert "storage_key" not in response.text and "binding_json" not in response.text
        for token in self.tokens.values(): assert token not in response.text
        return response.json()

    @staticmethod
    def record(scenario, case, **extra):
        fields = {key: case[key] for key in ("version", "evidence_version", "provider_mode", "inspection_status", "business_status", "max_permission", "reason_codes")}
        print(json.dumps(dict(scenario=scenario, fixture="CONTROLLED_CANNED_MOCK_AI_NOT_OPTICAL_EXTRACTION", **fields, **extra), sort_keys=True))

    def run(self, scenario):
        job, case = self.new()
        ch = self.challenge(job, case)
        data = self.image(ch, asset="PUMP-999" if scenario == "wrong-asset" else "PUMP-042", pressure=999.0 if scenario == "unsafe" else 35.0, label=scenario)
        uploaded = self.upload(case, ch, data, operation=secrets.token_urlsafe(24))
        if scenario in {"unsafe", "wrong-asset"}:
            assert uploaded["max_permission"] == (1 if scenario == "unsafe" else 0)
            assert self.action(uploaded, "prepare_invoice")["decision"] == "DENY"
            self.call("POST", f"/v1/cases/{case['id']}/approvals", data=dict(expected_case_version=uploaded["version"]), status=409)
            self.record(scenario, uploaded, restricted_action="DENY")
            self.audit(uploaded, ch)
            return
        assert uploaded["max_permission"] == 2
        queue = self.call("GET", "/v1/cases?approval_eligible=true").json()
        assert case["id"] in {item["id"] for item in queue["items"]}
        review = self.call("GET", f"/v1/cases/{case['id']}/review").json()
        assert review["case"]["approval_eligible"]
        assert self.call("GET", review["current_attachment"]).content == data
        if scenario == "complete":
            done = self.approve_complete(uploaded)
            self.action(uploaded, "complete_simulated_action", True, status=409)
            self.record(scenario, done, receipt_idempotent=True, stale_action="VERSION_CONFLICT")
            self.audit(done, ch)
        else:
            rejected = self.call("POST", f"/v1/cases/{case['id']}/rejections", data=dict(expected_case_version=uploaded["version"], reason="CORRECTION_REQUESTED")).json()
            assert rejected["business_status"] == "REJECTED" and rejected["max_permission"] == 0
            self.call("POST", f"/v1/cases/{case['id']}/approvals", data=dict(expected_case_version=rejected["version"]), status=409)
            self.record("recovery_rejected", rejected)
            fresh = self.challenge(job, rejected)
            corrected_data = self.image(fresh, label="corrected evidence")
            self.provider.fail_next = True
            failed = self.upload(case, fresh, corrected_data, 502)
            assert failed["max_permission"] == 0 and failed["reason_codes"] == ["PROVIDER_UNAVAILABLE"]
            operation = secrets.token_urlsafe(24)
            body = dict(expected_case_version=failed["version"], idempotency_key=operation)
            path = f"/v1/cases/{case['id']}/evidence/{failed['evidence_id']}/reanalysis"
            recovered = self.call("POST", path, "contractor", body).json()
            replay = self.call("POST", path, "contractor", body).json()
            assert replay["operation_replayed"] and replay["version"] == recovered["version"]
            assert recovered["evidence_version"] == failed["evidence_version"] == 2
            done = self.approve_complete(recovered)
            details = self.call("GET", f"/v1/cases/{case['id']}/review").json()
            assert [item["decision"] for item in details["reviews"]] == ["APPROVED", "REJECTED"]
            events = self.audit(done, fresh)
            assert any(row["event_type"] == "REANALYSIS_STARTED" for row in events)
            assert any(row["event_type"] == "MANAGER_REJECTED_EVIDENCE" for row in events)
            self.record("recovery_completed", done, rejection_history_preserved=True, explicit_retry_replayed=True)
        assert self.call("GET", "/v1/cases", "other_manager").json()["items"] == []
        self.call("GET", f"/v1/cases/{case['id']}/review", "other_manager", status=404)


def main():
    parser = argparse.ArgumentParser(description="Actual HTTP mock workflow scenarios; no external inference or payments.")
    parser.add_argument("--scenario", choices=["all", "complete", "unsafe", "wrong-asset", "recovery"], default="all")
    args = parser.parse_args()
    with TemporaryDirectory(prefix="sentinel-phase03-smoke-") as folder:
        root = Path(folder)
        observer = ScenarioObserver()
        app = create_app(Settings(database_path=root / "smoke.sqlite", media_root=root / "private", provider_mode="MOCK_AI"), perception_provider=observer)
        ids, passwords = {}, {}
        for name, role in (("manager", "MANAGER"), ("contractor", "CONTRACTOR"), ("engineer", "ENGINEER"), ("agent", "SERVICE_AGENT"),
                           ("spare_contractor", "CONTRACTOR"), ("other_manager", "MANAGER")):
            passwords[name] = secrets.token_urlsafe(24)
            ids[name] = provision_user(app.state.service.repository, "smoke-b" if name == "other_manager" else "smoke-a", name, role, passwords[name])["id"]
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        server = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False))
        thread = Thread(target=lambda: server.run(sockets=[listener]), daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and thread.is_alive() and time.monotonic() < deadline: time.sleep(0.02)
            if not server.started: raise RuntimeError("Local smoke server did not start")
            with httpx.Client(base_url=f"http://127.0.0.1:{listener.getsockname()[1]}", timeout=10) as client:
                assert client.get("/healthz").status_code == client.get("/docs").status_code == 200
                journey = Journey(client, observer, ids, passwords)
                for name in passwords: journey.login(name)
                for scenario in (["complete", "unsafe", "wrong-asset", "recovery"] if args.scenario == "all" else [args.scenario]):
                    journey.run(scenario)
                print("PASS Phase 03 actual TCP/HTTP; backend.app.api:create_app; MOCK_AI only; LIVE_GEMINI BLOCKED - AWAITING AUTHORIZATION")
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            listener.close()
            app.state.service.repository.close()
            if thread.is_alive(): raise RuntimeError("Local smoke server did not stop")


if __name__ == "__main__": main()
