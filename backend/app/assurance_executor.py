"""SUT adapters only. No oracle imports/labels; all state is disposable fiction."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
import secrets
from threading import Event

from .assurance_models import Observed
from .models import Action
from .policy import authorize


def policy_observation(scenario):
    value = deepcopy(scenario.observation)
    if value is not None and scenario.numeric_variant != "NONE":
        value["pressure_value"] = float("nan" if scenario.numeric_variant == "NAN" else "inf")
    return value


def pure(scenario, policy):
    result = authorize(policy_observation(scenario), policy, scenario.context, scenario.action)
    return Observed(decision=result.decision, inspection_status=result.inspection_status,
                    max_permission=result.max_permission, reason_codes=tuple(result.reason_codes))


def binding(scenario, policy):
    """Exercise the real binding verifier on read-only synthetic snapshot rows.

    No approval API, SQL approval insert, approval credential or business action.
    This is not claimed as an HTTP sign-off or concurrent approval test.
    """
    from .case_service import CaseService, canonical, digest
    service = object.__new__(CaseService)
    job = dict(id="synthetic-job-001", tenant_id="synthetic-org-a", asset_id="PUMP-042", version=1, contractor_id="fixture-contractor")
    case = dict(id="fixture-case", tenant_id="synthetic-org-a", job_id=job["id"], version=4,
                evidence_version=1, invoice_amount_paise=500000, policy_version="1.0.0", approval_id="READ_ONLY_FIXTURE")
    ev = dict(id="fixture-evidence", sha256="a"*64, submitted_by="fixture-contractor", version=1)
    ch = dict(id="fixture-challenge", evidence_session_id="FICTIONAL-EVIDENCE-SESSION",
              auth_session_id="FICTIONAL-AUTH-SESSION", expires_at=1794477900)
    reviewer = dict(id="fixture-reviewer", role="MANAGER", active=True)
    bound = service._binding(case, job, ev, ch, reviewer["id"], 3)
    approval = dict(id=case["approval_id"], reviewer_id=reviewer["id"], reviewed_case_version=3,
                    effective_case_version=4, binding_sha256=digest(bound), binding_json=canonical(bound))
    if scenario.operation == "REPLACED_EVIDENCE":
        ev.update(id="new-fixture-evidence", sha256="b"*64, version=2)
        case["evidence_version"] = 2
    elif scenario.operation == "REVISED_INVOICE":
        case["invoice_amount_paise"] = 500001
    elif scenario.operation == "REVISED_POLICY":
        case["policy_version"] = "changed-version"
    elif scenario.operation == "REVIEWER_DISABLED":
        reviewer["active"] = False
    elif scenario.operation != "CURRENT_BINDING":
        raise ValueError("Unknown binding operation")
    class ReadOnlyFixture:
        def get(self, table, **keys):
            if table == "approvals": return approval
            if table == "users": return reviewer if reviewer["active"] else None
            raise ValueError("Unexpected snapshot access")
    base = authorize(scenario.observation, policy, scenario.context).model_dump(mode="json")
    approved = service._valid_approval(ReadOnlyFixture(), case, job, base, ev, ch) is not None
    return Observed(decision="ALLOW" if approved else "DENY",
        inspection_status="APPROVED_BY_HUMAN" if approved else base["inspection_status"],
        max_permission=3 if approved else base["max_permission"], reason_codes=())


class APIHarness:
    def __init__(self, folder, policy):
        from fastapi.testclient import TestClient
        from .api import create_app
        from .perception import MockPerceptionProvider
        from .provisioning import provision_user
        from .settings import Settings
        self.clock = lambda: datetime(2026, 11, 12, 10, tzinfo=timezone.utc)
        self.provider = MockPerceptionProvider()
        self.app = create_app(Settings(database_path=Path(folder)/"cases.sqlite", media_root=Path(folder)/"media",
            environment="test", allow_synthetic=True, provider_mode="MOCK_AI"), clock=self.clock, perception_provider=self.provider, enable_assurance=False)
        self.service = self.app.state.service
        self.service.template = policy  # Isolated app only; no outer repository/policy reference.
        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.client.__enter__()
        self.ids, self.tokens = {}, {}
        for name, role, tenant in (("manager","MANAGER","lab-a"),("contractor","CONTRACTOR","lab-a"),
            ("engineer","ENGINEER","lab-a"),("agent","SERVICE_AGENT","lab-a"),
            ("other_contractor","CONTRACTOR","lab-a"),("other_engineer","ENGINEER","lab-b")):
            password = secrets.token_urlsafe(24)
            self.ids[name] = provision_user(self.service.repository, tenant, name, role, password)["id"]
            login = self.client.post("/v1/auth/login", json=dict(tenant_id=tenant, username=name, password=password))
            if login.status_code != 200: raise RuntimeError("Isolated authentication failed")
            self.tokens[name] = login.json()["access_token"]

    def call(self, method, path, role="manager", body=None):
        return self.client.request(method, path, headers={"Authorization":"Bearer "+self.tokens[role]}, json=body)

    def ready(self, pressure=35):
        job = self.call("POST","/v1/jobs",body=dict(asset_id="PUMP-042",contractor_id=self.ids["contractor"],
            engineer_id=self.ids["engineer"],service_agent_id=self.ids["agent"])).json()
        case = self.call("POST","/v1/cases",body={"job_id":job["id"]}).json()
        ch = self.call("POST",f"/v1/jobs/{job['id']}/challenges","contractor",
            dict(case_id=case["id"],expected_case_version=case["version"])).json()
        obs = dict(artifact_mode="SYNTHETIC",asset_id_observed="PUMP-042",challenge_text_observed=ch["token"],
            pressure_value=pressure,pressure_unit="PSI",equipment_status="RUNNING",calibration_expiry_date="2099-12-31",uncertain_fields=[])
        return job, self.service.inject_synthetic_evidence(self.tokens["contractor"],case["id"],ch["case_version"],ch["id"],ch["evidence_session_id"],obs), ch, obs

    def evaluate(self, case):
        return self.call("POST",f"/v1/cases/{case['id']}/actions/evaluate","agent",
            dict(expected_case_version=case["version"],action="prepare_invoice"))

    def execute(self, scenario):
        job, case, ch, obs = self.ready(45 if scenario.operation == "PREPARE_UNSAFE" else 35)
        op = scenario.operation
        if op in {"PREPARE_VALID", "PREPARE_UNSAFE"}:
            response = self.evaluate(case)
        elif op in {"APPROVE_CONTRACTOR", "APPROVE_ENGINEER"}:
            response = self.call("POST",f"/v1/cases/{case['id']}/approvals", "contractor" if op == "APPROVE_CONTRACTOR" else "engineer",
                dict(expected_case_version=case["version"]))
        elif op == "CROSS_TENANT":
            response = self.call("GET",f"/v1/cases/{case['id']}","other_engineer")
        elif op == "UNASSIGNED":
            response = self.call("GET",f"/v1/jobs/{job['id']}","other_contractor")
        elif op == "STALE_EVIDENCE":
            self.service.inject_synthetic_evidence(self.tokens["contractor"],case["id"],case["version"],ch["id"],ch["evidence_session_id"],{**obs,"pressure_value":36})
            response = self.evaluate(case)
        elif op == "REPLAY_IMAGE":
            from PIL import Image
            image = BytesIO()
            Image.new("RGB",(48,48),"white").save(image,"PNG")
            self.provider.reply = {key:value for key,value in obs.items() if key != "artifact_mode"} | {"conflicting_fields":[]}
            headers={"Authorization":"Bearer "+self.tokens["contractor"],"Content-Type":"image/png",
                "X-Expected-Case-Version":str(case["version"]),"X-Challenge-ID":ch["id"],"X-Evidence-Session-ID":ch["evidence_session_id"]}
            first = self.client.post(f"/v1/cases/{case['id']}/evidence",headers=headers,content=image.getvalue())
            if first.status_code != 200: raise RuntimeError("Isolated image intake failed")
            headers["X-Expected-Case-Version"] = str(first.json()["version"])
            response = self.client.post(f"/v1/cases/{case['id']}/evidence",headers=headers,content=image.getvalue())
        elif op == "CONCURRENT_INVOICE":
            started, release = Event(), Event()
            original = self.service._event
            def held(tx, actor, state, kind, *args, **kwargs):
                if kind == "INVOICE_CHANGED":
                    started.set()
                    if not release.wait(5): raise RuntimeError("Concurrent fixture timed out")
                return original(tx,actor,state,kind,*args,**kwargs)
            self.service._event = held
            try:
                with ThreadPoolExecutor(max_workers=2) as pool:
                    mutation = pool.submit(self.call,"PATCH",f"/v1/cases/{case['id']}/invoice","manager",
                        dict(expected_case_version=case["version"],invoice_amount_paise=500001))
                    if not started.wait(5): raise RuntimeError("Mutation did not reach protected transaction")
                    action = pool.submit(self.evaluate,case)
                    release.set()
                    if mutation.result(timeout=5).status_code != 200: raise RuntimeError("Mutation failed")
                    response = action.result(timeout=5)
            finally:
                release.set()
                self.service._event = original
        else:
            raise ValueError("Unknown API target")
        data = response.json()
        return Observed(decision=data.get("decision"),http_status=response.status_code,
            inspection_status=data.get("inspection_status"),max_permission=data.get("max_permission"),reason_codes=tuple(data.get("reason_codes",())))

    def close(self):
        try:
            with self.service.repository.transaction() as tx:
                if tx.find("approvals") or tx.find("action_runs"):
                    raise RuntimeError("Assurance must not create approvals or business actions")
        finally:
            self.client.__exit__(None,None,None)
            self.service.repository.close()
