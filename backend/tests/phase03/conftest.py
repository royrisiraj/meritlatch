import pytest

from backend.tests.phase02.conftest import account_template, media_world, no_external_connections, image_bytes, visual_reply


class WorkflowWorld:
    def __init__(self, world):
        self.world = world

    def __getattr__(self, name):
        return getattr(self.world, name)

    def reject(self, case, reason="CORRECTION_REQUESTED", key="a_manager"):
        return self.request("POST", f"/v1/cases/{case['id']}/rejections", key,
                            dict(expected_case_version=case["version"], reason=reason))

    def review(self, case, key="a_manager"):
        return self.request("GET", f"/v1/cases/{case['id']}/review", key)

    def retry(self, case, key="a_contractor", operation="retry_operation_0001", expected=None, **extra):
        return self.request("POST", f"/v1/cases/{case['id']}/evidence/{case['evidence_id']}/reanalysis", key,
            dict(expected_case_version=case["version"] if expected is None else expected, idempotency_key=operation, **extra))

    def ready(self, **changes):
        job, case, challenge = self.setup_case()
        self.provider.reply = visual_reply(challenge, **changes)
        response = self.upload(case, challenge)
        assert response.status_code == 200, response.text
        return job, response.json(), challenge


@pytest.fixture
def wf(media_world):
    return WorkflowWorld(media_world)
