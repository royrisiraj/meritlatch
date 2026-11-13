"""Explicit isolated browser demo. Canned observations are NOT image extraction.

No fixture HTTP route. Normal factory / normal MOCK_AI remains UNKNOWN. This
standalone loopback harness never loads .env and uses a NEW operator-named root.
"""
import argparse
import json
from pathlib import Path
import secrets

from PIL import Image, ImageDraw
import uvicorn
from backend.app.api import create_app
from backend.app.perception import MockPerceptionProvider, PerceptionResult, VisualObservation
from backend.app.provisioning import provision_user
from backend.app.settings import Settings


class CannedDemoObserver(MockPerceptionProvider):
    model_id = "CANNED_DEMO_NOT_IMAGE_EXTRACTION"

    def __init__(self):
        super().__init__()
        self.repository = None

    async def inspect(self, source):
        # Bind a fixed test reply to the actual reserved upload. No image parsing,
        # client observation input, manager review or permission injection.
        with self.repository.transaction() as tx:
            ev = tx.get("evidence", id=source.evidence_id)
            ch = tx.get("challenges", id=ev["challenge_id"])
            fields = dict(asset_id_observed=ch["asset_id"], challenge_text_observed=ch["token"],
                          pressure_value=999 if ev["version"] == 1 else 35,
                          pressure_unit="PSI", equipment_status="RUNNING",
                          calibration_expiry_date="2099-12-31", uncertain_fields=[], conflicting_fields=[])
        return PerceptionResult(VisualObservation.model_validate(fields), self.model_id, "canned-unsafe-then-valid-v1")


def prepare(root: Path, fixture: str):
    root = root.resolve()
    if root.exists():
        raise ValueError("Use a new isolated demo directory; existing data is never overwritten.")
    root.mkdir(parents=True)
    provider = CannedDemoObserver() if fixture == "unsafe-then-valid" else MockPerceptionProvider()
    app = create_app(Settings(database_path=root / "demo.sqlite", environment="test", provider_mode="MOCK_AI",
                              media_root=root / "media", challenge_seconds=600), perception_provider=provider)
    if isinstance(provider, CannedDemoObserver):
        provider.repository = app.state.service.repository
    users = {}
    for tenant, username, role in [("portal-a", "manager", "MANAGER"), ("portal-a", "contractor", "CONTRACTOR"),
        ("portal-a", "unassigned", "CONTRACTOR"), ("portal-a", "engineer", "ENGINEER"),
        ("portal-a", "reviewer", "ENGINEER"), ("portal-a", "agent", "SERVICE_AGENT"),
        ("portal-b", "other_manager", "MANAGER"), ("portal-b", "other_engineer", "ENGINEER")]:
        password = secrets.token_urlsafe(24)
        user = provision_user(app.state.service.repository, tenant, username, role, password)
        users[username] = {**user, "password": password}
    (root / "credentials.local.json").write_text(json.dumps(users), encoding="utf-8")
    for n in (1, 2, 3):
        image = Image.new("RGB", (750, 240), "white")
        ImageDraw.Draw(image).text((20, 40), f"SYNTHETIC DEMO CARD {n}\nCANNED MOCK_AI - NOT IMAGE EXTRACTION\nNo actual equipment certification", fill="black")
        image.save(root / f"evidence-{n}.png")
    (root / "invalid.png").write_bytes(b"not an image")
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8015)
    parser.add_argument("--fixture", choices=["normal-unknown", "unsafe-then-valid"], default="normal-unknown")
    parser.add_argument("--acknowledge-canned", action="store_true")
    args = parser.parse_args()
    if args.fixture != "normal-unknown" and not args.acknowledge_canned:
        parser.error("Canned positive fixtures require --acknowledge-canned; not real perception.")
    app = prepare(args.root, args.fixture)
    print("Isolated loopback MOCK_AI demo; fixture=" + args.fixture + "; no live inference", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False, log_level="warning")


if __name__ == "__main__":
    main()
