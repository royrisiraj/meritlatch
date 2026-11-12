from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import struct
import zlib

import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from backend.app.api import create_app
from backend.app.errors import AppError
from backend.app.media import validate_image
from backend.app.repository import SQLiteRepository, metadata
from backend.tools import smoke_gemini
from .conftest import image_bytes


def test_authenticated_upload_is_required_before_binding_validation(media_world):
    w = media_world
    job, case, ch = w.setup_case()
    for headers in ({}, {"Authorization": "Bearer " + "x" * 43}):
        response = w.client.post(f"/v1/cases/{case['id']}/evidence", headers=headers, content=image_bytes())
        assert response.status_code == 401
    response = w.client.post(f"/v1/cases/{case['id']}/evidence", headers=w.headers("a_contractor"), content=image_bytes())
    assert response.status_code == 422
    assert response.json()["reason_codes"] == ["INVALID_EVIDENCE_BINDING"]


def test_decoder_bomb_header_and_warning_are_rejected(media_world, monkeypatch):
    def chunk(kind, content):
        return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind + content))
    header = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 100000, 100000, 8, 2, 0, 0, 0)) + chunk(b"IDAT", b"broken") + chunk(b"IEND", b"")
    with pytest.raises(AppError) as exc:
        validate_image(header, "image/png", media_world.app.state.settings)
    assert exc.value.status == 413
    warning_image = image_bytes(size=(15, 10))
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 100)
    with pytest.raises(AppError) as exc:
        validate_image(warning_image, "image/png", media_world.app.state.settings)
    assert exc.value.status == 413


def test_gps_is_only_an_untrusted_presence_signal(media_world):
    exif = Image.Exif()
    exif[34853] = {1: "N", 2: (1.0, 2.0, 3.0), 3: "E", 4: (4.0, 5.0, 6.0)}
    checked = validate_image(image_bytes("JPEG", exif=exif), "image/jpeg", media_world.app.state.settings)
    assert checked.provenance["gps_present"] is True
    assert checked.provenance["metadata_trust"] == "UNTRUSTED_SUPPORTING_ONLY"
    assert "latitude" not in checked.provenance


@pytest.mark.parametrize("table", ["media_uploads", "media_analyses"])
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_media_history_is_append_only(media_world, table, operation):
    w = media_world
    job, case, ch = w.setup_case()
    assert w.upload(case, ch).status_code == 200
    query = f"UPDATE {table} SET id = id" if operation == "UPDATE" else f"DELETE FROM {table}"
    with pytest.raises(IntegrityError, match="append-only record"):
        with w.service.repository.engine.begin() as connection:
            connection.exec_driver_sql(query)


def test_media_survives_restart_and_unknown_media_schema_fails_closed(media_world):
    w = media_world
    job, case, ch = w.setup_case()
    uploaded = w.upload(case, ch).json()
    approved = w.approve(uploaded).json()
    w.service.repository.close()
    reopened = create_app(w.app.state.settings, clock=w.clock)
    with TestClient(reopened) as client:
        current = client.get(f"/v1/cases/{case['id']}", headers=w.headers()).json()
        assert current["max_permission"] == 3
        assert current["model_id"] == "mock-observer-v1"
        assert current["observation"]["pressure_value"] == 35
        content = client.get(f"/v1/cases/{case['id']}/evidence/{uploaded['evidence_id']}/content", headers=w.headers())
        assert content.status_code == 200
        with reopened.state.service.repository.transaction() as tx:
            assert tx.find("schema_migrations") == [{"version": 1}]
            assert tx.find("media_schema_migrations") == [{"version": 1}]
            tx.change("media_schema_migrations", {"version": 1}, {"version": 999})
        with pytest.raises(ValueError, match="Unsupported media schema"):
            reopened.state.service.repository.migrate()


def test_additive_media_migration_preserves_legacy_schema_and_records(tmp_path):
    from sqlalchemy import create_engine, insert
    path = tmp_path / "legacy.sqlite"
    engine = create_engine("sqlite:///" + path.as_posix())
    old_tables = [table for name, table in metadata.tables.items() if name not in {"media_schema_migrations", "media_uploads", "media_analyses"}]
    with engine.begin() as connection:
        metadata.create_all(connection, tables=old_tables)
        connection.execute(insert(metadata.tables["schema_migrations"]).values(version=1))
        connection.execute(insert(metadata.tables["tenants"]).values(id="legacy-tenant"))
    engine.dispose()
    repo = SQLiteRepository(path)
    try:
        with repo.transaction() as tx:
            assert tx.get("tenants", id="legacy-tenant")
            assert tx.find("schema_migrations") == [{"version": 1}]
            assert tx.find("media_schema_migrations") == [{"version": 1}]
            assert tx.find("media_uploads") == []
    finally:
        repo.close()


def test_private_read_detects_changed_stored_bytes(media_world):
    w = media_world
    job, case, ch = w.setup_case()
    value = w.upload(case, ch).json()
    # Simulate local operator/file corruption; this is not an HTTP write capability.
    next(w.app.state.settings.media_root.iterdir()).write_bytes(b"corrupted")
    response = w.request("GET", f"/v1/cases/{case['id']}/evidence/{value['evidence_id']}/content")
    assert response.status_code == 503
    assert response.json()["reason_codes"] == ["MEDIA_INTEGRITY_ERROR"]
    assert "corrupted" not in response.text


def test_replaced_media_cannot_be_downloaded_as_current_evidence(media_world):
    w = media_world
    job, case, ch = w.setup_case()
    first = w.upload(case, ch).json()
    second = w.upload(case, ch, image_bytes(text="replacement"), expected=first["version"])
    assert second.status_code == 200
    response = w.request("GET", f"/v1/cases/{case['id']}/evidence/{first['evidence_id']}/content")
    assert response.status_code == 404


@pytest.mark.parametrize("argv", [["smoke", "--check"], ["smoke"], ["smoke", "--allow-billable"]])
def test_live_smoke_without_explicit_approval_never_loads_credentials_or_calls_provider(monkeypatch, capsys, argv):
    monkeypatch.setattr("sys.argv", argv)
    def forbidden(*args, **kwargs): raise AssertionError("Must not read keys or call a model")
    monkeypatch.setattr(smoke_gemini.Settings, "from_env", forbidden)
    monkeypatch.setattr(smoke_gemini, "load_dotenv", forbidden)
    monkeypatch.setattr(smoke_gemini, "GeminiPerceptionProvider", forbidden)
    assert smoke_gemini.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "BLOCKED"
    assert result["network_called"] is False


def test_live_smoke_requires_actual_manually_reviewed_input(monkeypatch, capsys, tmp_path):
    image = tmp_path / "fictional.png"
    image.write_bytes(image_bytes())
    truth = tmp_path / "truth.json"
    truth.write_text('{"human_reviewed": false}', encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["smoke", "--allow-billable", "--confirm-fictional-consent", "--image", str(image),
        "--ground-truth", str(truth), "--output", str(tmp_path / "report.local.json")])
    def forbidden(*args, **kwargs): raise AssertionError("No live call without manual ground truth")
    monkeypatch.setattr(smoke_gemini, "GeminiPerceptionProvider", forbidden)
    assert smoke_gemini.main() == 2
    assert json.loads(capsys.readouterr().out)["network_called"] is False
