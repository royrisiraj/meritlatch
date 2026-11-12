from dataclasses import replace
from io import BytesIO
import shutil
import socket

import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from backend.tests.phase01.conftest import account_template, Clock, World
from backend.app.api import create_app
from backend.app.settings import Settings
from backend.app.perception import MockPerceptionProvider


def image_bytes(format="PNG", text="FICTIONAL", size=(240, 120), exif=None):
    image = Image.new("RGB", size, "white")
    ImageDraw.Draw(image).text((5, 5), text, fill="black")
    output = BytesIO()
    image.save(output, format=format, **({"exif": exif} if exif is not None else {}))
    return output.getvalue()


def visual_reply(challenge, **changes):
    data = dict(asset_id_observed="PUMP-042", challenge_text_observed=challenge["token"], pressure_value=35.0,
        pressure_unit="PSI", equipment_status="RUNNING", calibration_expiry_date="2026-12-31",
        uncertain_fields=[], conflicting_fields=[])
    return {**data, **changes}


@pytest.fixture(autouse=True)
def no_external_connections(monkeypatch):
    original = socket.socket.connect
    def connect(sock, address):
        if isinstance(address, tuple) and address[0] not in {"127.0.0.1", "::1", "localhost"}:
            raise AssertionError("Unit tests must not contact external providers")
        return original(sock, address)
    monkeypatch.setattr(socket.socket, "connect", connect)


class MediaWorld(World):
    def setup_case(self):
        job, case = self.new()
        challenge = self.challenge(job, case)
        self.provider.reply = visual_reply(challenge)
        return job, case, challenge

    def upload(self, case, challenge, data=None, content_type="image/png", key="a_contractor", expected=None, extra=None):
        headers = {**self.headers(key), "Content-Type": content_type,
            "X-Expected-Case-Version": str(challenge["case_version"] if expected is None else expected),
            "X-Challenge-ID": challenge["id"], "X-Evidence-Session-ID": challenge["evidence_session_id"], **(extra or {})}
        return self.client.post(f"/v1/cases/{case['id']}/evidence", headers=headers,
                                content=data if data is not None else image_bytes(text=challenge["token"]))


@pytest.fixture
def media_world(tmp_path, account_template):
    template, ids, passwords, tokens = account_template
    path = tmp_path / "media.sqlite"
    shutil.copy2(template, path)
    clock = Clock()
    provider = MockPerceptionProvider()
    settings = Settings(database_path=path, environment="test", allow_synthetic=True,
                        provider_mode="MOCK_AI", media_root=tmp_path / "private")
    app = create_app(settings, clock=clock, perception_provider=provider)
    with TestClient(app, raise_server_exceptions=False) as client:
        world = MediaWorld(app, client, ids, passwords, tokens, clock)
        world.provider = provider
        yield world
