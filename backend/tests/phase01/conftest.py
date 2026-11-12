from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
import secrets
import shutil

import pytest
from fastapi.testclient import TestClient

from backend.testing import create_test_app
from backend.app.provisioning import provision_user


class Clock:
    def __init__(self):
        self.now = datetime(2026, 11, 12, 10, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


@pytest.fixture(scope="session")
def account_template(tmp_path_factory):
    path = tmp_path_factory.mktemp("phase01-template") / "template.sqlite"
    app = create_test_app(path, Clock())
    service = app.state.service
    ids, passwords, tokens = {}, {}, {}
    for tenant in ("a", "b"):
        roles = {"contractor": "CONTRACTOR", "manager": "MANAGER", "engineer": "ENGINEER", "agent": "SERVICE_AGENT"}
        if tenant == "a":
            roles.update(other_contractor="CONTRACTOR", reviewer="ENGINEER", other_agent="SERVICE_AGENT")
        for name, role in roles.items():
            key = f"{tenant}_{name}"
            passwords[key] = secrets.token_urlsafe(24)
            ids[key] = provision_user(service.repository, tenant, name, role, passwords[key])["id"]
            tokens[key] = service.login(tenant, name, passwords[key])["access_token"]
    service.repository.close()  # Dispose all connections; SQLite checkpoints before copying.
    return path, ids, passwords, tokens


class World:
    def __init__(self, app, client, ids, passwords, tokens, clock):
        self.app, self.client, self.ids = app, client, ids
        self.service = app.state.service
        self.passwords, self.tokens, self.clock = passwords, tokens, clock

    def headers(self, key="a_manager"):
        return {"Authorization": "Bearer " + self.tokens[key]}

    def request(self, method, path, key="a_manager", data=None):
        return self.client.request(method, path, headers=self.headers(key), json=data)

    def new(self, tenant="a", contractor="contractor"):
        job = self.request("POST", "/v1/jobs", f"{tenant}_manager", dict(asset_id="PUMP-042",
            contractor_id=self.ids[f"{tenant}_{contractor}"], engineer_id=self.ids[f"{tenant}_engineer"],
            service_agent_id=self.ids[f"{tenant}_agent"]))
        assert job.status_code == 201, job.text
        case = self.request("POST", "/v1/cases", f"{tenant}_manager", dict(job_id=job.json()["id"], invoice_amount_paise=500000))
        assert case.status_code == 201, case.text
        return job.json(), case.json()

    def challenge(self, job, case, key="a_contractor"):
        response = self.request("POST", f"/v1/jobs/{job['id']}/challenges", key,
                                dict(case_id=case["id"], expected_case_version=case["version"]))
        assert response.status_code == 200, response.text
        return response.json()

    def inject(self, case, ch, changes=None, key="a_contractor", expected=None):
        obs = dict(artifact_mode="SYNTHETIC", asset_id_observed="PUMP-042", challenge_text_observed=ch["token"],
                   pressure_value=35.0, pressure_unit="PSI", equipment_status="RUNNING",
                   calibration_expiry_date="2026-12-31", uncertain_fields=[])
        obs.update(changes or {})
        return self.service.inject_synthetic_evidence(self.tokens[key], case["id"],
            ch["case_version"] if expected is None else expected, ch["id"], ch["evidence_session_id"], obs)

    def ready(self):
        job, case = self.new()
        ch = self.challenge(job, case)
        return job, self.inject(case, ch), ch

    def approve(self, case, key="a_manager"):
        return self.request("POST", f"/v1/cases/{case['id']}/approvals", key,
                            dict(expected_case_version=case["version"]))

    def act(self, case, action, key="a_agent", execute=False):
        return self.request("POST", f"/v1/cases/{case['id']}/actions/{'execute' if execute else 'evaluate'}", key,
                            dict(expected_case_version=case["version"], action=action))


@pytest.fixture
def world(tmp_path, account_template):
    template, ids, passwords, tokens = account_template
    path = tmp_path / "cases.sqlite"
    shutil.copy2(template, path)
    clock = Clock()
    app = create_test_app(path, clock)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield World(app, client, ids, passwords, tokens, clock)
