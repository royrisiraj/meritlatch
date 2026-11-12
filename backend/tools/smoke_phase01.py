"""Actual localhost HTTP smoke with a temporary SYNTHETIC-only database.

No passwords, bearer tokens, challenges or raw observations are printed.
The Uvicorn listener and database are owned and cleaned up by this script.
"""

from pathlib import Path
import secrets
import socket
from tempfile import TemporaryDirectory
from threading import Thread
import time

import httpx
import uvicorn

from backend.app.provisioning import provision_user
from backend.testing import create_test_app


def main():
    with TemporaryDirectory(prefix="sentinel-phase01-smoke-") as folder:
        app = create_test_app(Path(folder) / "smoke.sqlite")
        service = app.state.service
        passwords = {name: secrets.token_urlsafe(24) for name in ("contractor", "manager", "engineer", "agent")}
        ids = {}
        for name, role in (("contractor", "CONTRACTOR"), ("manager", "MANAGER"), ("engineer", "ENGINEER"), ("agent", "SERVICE_AGENT")):
            ids[name] = provision_user(service.repository, "smoke-synthetic", name, role, passwords[name])["id"]
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="critical", access_log=False))
        worker = Thread(target=lambda: server.run(sockets=[listener]), daemon=True)
        worker.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and worker.is_alive() and time.monotonic() < deadline:
                time.sleep(0.02)
            if not server.started:
                raise RuntimeError("Smoke server did not start")
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=10) as client:
                def call(method, path, expected=200, actor=None, data=None):
                    headers = {"Authorization": "Bearer " + tokens[actor]} if actor else {}
                    response = client.request(method, path, headers=headers, json=data)
                    if response.status_code != expected:
                        raise RuntimeError(f"Unexpected status for {method} {path}: {response.status_code}")
                    return response

                call("GET", "/healthz")
                call("GET", "/docs")
                print("HTTP health/docs: 200 / 200")
                call("GET", "/v1/jobs", expected=401)
                tokens = {name: call("POST", "/v1/auth/login", data=dict(tenant_id="smoke-synthetic", username=name, password=passwords[name])).json()["access_token"] for name in passwords}
                print("Authenticated four independent roles; anonymous jobs request: 401")
                job = call("POST", "/v1/jobs", 201, "manager", dict(asset_id="PUMP-042", contractor_id=ids["contractor"], engineer_id=ids["engineer"], service_agent_id=ids["agent"])).json()
                case = call("POST", "/v1/cases", 201, "manager", dict(job_id=job["id"], invoice_amount_paise=500000)).json()
                denied = call("POST", f"/v1/cases/{case['id']}/actions/evaluate", actor="agent", data=dict(expected_case_version=case["version"], action="prepare_invoice")).json()
                assert denied["decision"] == "DENY" and denied["max_permission"] == 0
                print("Missing evidence: L0; prepare_invoice DENY")
                ch = call("POST", f"/v1/jobs/{job['id']}/challenges", actor="contractor", data=dict(case_id=case["id"], expected_case_version=case["version"])).json()
                observation = dict(artifact_mode="SYNTHETIC", asset_id_observed="PUMP-042", challenge_text_observed=ch["token"], pressure_value=35.0,
                    pressure_unit="PSI", equipment_status="RUNNING", calibration_expiry_date="2099-12-31", uncertain_fields=[])
                # Internal test factory only: this is not an HTTP injection endpoint.
                service.inject_synthetic_evidence(tokens["contractor"], case["id"], ch["case_version"], ch["id"], ch["evidence_session_id"], observation)
                current = call("GET", f"/v1/cases/{case['id']}", actor="manager").json()
                assert current["max_permission"] == 2 and current["artifact_mode"] == "SYNTHETIC"
                decision = call("POST", f"/v1/cases/{case['id']}/actions/evaluate", actor="agent", data=dict(expected_case_version=current["version"], action="complete_simulated_action")).json()
                assert decision["decision"] == "DENY"
                print("Internal SYNTHETIC observation: L2; unapproved completion DENY")
                call("POST", f"/v1/cases/{case['id']}/approvals", 403, "contractor", dict(expected_case_version=current["version"]))
                call("POST", f"/v1/cases/{case['id']}/approvals", 403, "engineer", dict(expected_case_version=current["version"]))
                print("Contractor self-approval / engineer approval: 403 / 403")
                approved = call("POST", f"/v1/cases/{case['id']}/approvals", actor="manager", data=dict(expected_case_version=current["version"])).json()
                assert approved["max_permission"] == 3
                one = call("POST", f"/v1/cases/{case['id']}/actions/execute", actor="agent", data=dict(expected_case_version=approved["version"], action="complete_simulated_action")).json()
                two = call("POST", f"/v1/cases/{case['id']}/actions/execute", actor="agent", data=dict(expected_case_version=approved["version"], action="complete_simulated_action")).json()
                assert one["receipt_id"] == two["receipt_id"] and two["already_executed"]
                print("Manager review: L3; repeated simulated completion: one receipt")
                changed = call("PATCH", f"/v1/cases/{case['id']}/invoice", actor="manager", data=dict(expected_case_version=approved["version"], invoice_amount_paise=500001)).json()
                assert changed["max_permission"] == 2
                denied = call("POST", f"/v1/cases/{case['id']}/actions/execute", actor="agent", data=dict(expected_case_version=changed["version"], action="complete_simulated_action")).json()
                assert denied["decision"] == "DENY"
                print("Changed invoice: approval invalidated; completion DENY")
                audit = call("GET", f"/v1/cases/{case['id']}/audit", actor="manager").json()
                assert audit and all("observation_json" not in row for row in audit)
                call("POST", "/v1/auth/logout", actor="manager")
                call("GET", "/v1/me", 401, "manager")
                print("Redacted audit verified; logout revocation: 401")
                print("PASS: actual localhost HTTP workflow, SYNTHETIC only; no Gemini, money movement or cloud")
        finally:
            server.should_exit = True
            worker.join(timeout=10)
            listener.close()
            service.repository.close()
            if worker.is_alive():
                raise RuntimeError("Smoke server failed to stop")


if __name__ == "__main__":
    main()
