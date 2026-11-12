"""Opt-in billable perception evaluation on a consented fictional image only.

Never an approval endpoint. --check/omitted approval flags perform no network I/O.
"""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from time import monotonic

from dotenv import load_dotenv

from backend.app.config import load_policy
from backend.app.gemini_provider import GeminiPerceptionProvider
from backend.app.media import validate_image
from backend.app.models import EvaluationContext
from backend.app.perception import PerceptionInput, ProviderError, VisualObservation
from backend.app.policy import authorize
from backend.app.settings import Settings


def main():
    parser = argparse.ArgumentParser(description="One approved live fictional-image evaluation; no business authority.")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--image", type=Path)
    parser.add_argument("--ground-truth", type=Path)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-billable", action="store_true")
    parser.add_argument("--confirm-fictional-consent", action="store_true")
    args = parser.parse_args()
    if args.check or not args.allow_billable or not args.confirm_fictional_consent:
        print(json.dumps(dict(status="BLOCKED", provider_mode="LIVE_GEMINI", network_called=False,
                              reason_codes=["LIVE_APPROVAL_AND_FICTIONAL_IMAGE_CONSENT_REQUIRED"])))
        return 2
    if not args.image or not args.ground_truth or not args.output or not args.output.name.endswith(".local.json"):
        print(json.dumps(dict(status="BLOCKED", network_called=False, reason_codes=["IMAGE_MANUAL_GROUND_TRUTH_AND_PRIVATE_OUTPUT_REQUIRED"])))
        return 2
    network_started = False
    try:
        truth = json.loads(args.ground_truth.read_text(encoding="utf-8"))
        if truth.get("origin") != "CONSENTED_FICTIONAL_NO_CUSTOMER_DATA" or truth.get("human_reviewed") is not True or not truth.get("reviewed_by") or truth["reviewed_by"] == "REPLACE_WITH_HUMAN_REVIEWER":
            raise ValueError("Manual review/consent missing")
        expected = VisualObservation.model_validate(truth["expected_observation"])
        context = EvaluationContext.model_validate(truth["policy_context"])
        if args.output.exists(): raise ValueError("Output exists")
        if args.env_file:
            load_dotenv(args.env_file, override=False)
        settings = Settings.from_env()
        if settings.provider_mode != "LIVE_GEMINI" or settings.provider_attempts != 1:
            raise ValueError("Smoke requires explicit LIVE_GEMINI, key, billing flag and one attempt")
        with args.image.open("rb") as file:
            raw = file.read(settings.max_image_bytes + 1)
        image = validate_image(raw, "application/octet-stream", settings)
        policy = load_policy(Path(__file__).resolve().parents[2] / "policies/maintenance_v1.json")
        provider = GeminiPerceptionProvider(settings)
        started = monotonic()
        network_started = True
        try:
            result = asyncio.run(provider.inspect(PerceptionInput(image.provider_bytes, "image/png", "consented-fictional-live-smoke")))
            elapsed = monotonic() - started
            comparison = {name: getattr(result.fields, name) == getattr(expected, name) for name in VisualObservation.model_fields}
            decision = authorize(result.fields.observation("LIVE_GEMINI"), policy, context)
            report = dict(status="COMPLETED", provider_mode="LIVE_GEMINI", requested_model_id=provider.model_id,
                returned_model_version=result.model_version, input_media_type=image.mime_type, provider_media_type="image/png",
                original_sha256=image.sha256, provider_sha256=image.provider_sha256, elapsed_seconds=elapsed,
                observations=result.fields.model_dump(mode="json"), ground_truth_comparison=comparison,
                authorization_decision=decision.model_dump(mode="json"),
                scope="OFFLINE_GROUND_TRUTH_COMPARISON_NOT_AUTHENTICATED_API_AUTHORIZATION",
                limitation="One fictional sample does not establish model accuracy or media authenticity.")
        except ProviderError as exc:
            report = dict(status="FAILED", provider_mode="LIVE_GEMINI", requested_model_id=provider.model_id,
                input_media_type=image.mime_type, elapsed_seconds=monotonic() - started,
                reason_codes=[exc.code], authorization_decision="DENY")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(report, output, indent=2, allow_nan=False)
        print(json.dumps({key: value for key, value in report.items() if key not in {"observations", "original_sha256", "provider_sha256"}}, default=str))
        return 0 if report["status"] == "COMPLETED" else 1
    except Exception:
        print(json.dumps(dict(status="BLOCKED" if not network_started else "FAILED", provider_mode="LIVE_GEMINI",
            network_called=network_started, reason_codes=["CHECK_APPROVAL_CONFIG_AND_REVIEWED_FICTIONAL_INPUT"], authorization_decision="DENY")))
        return 2 if not network_started else 1


if __name__ == "__main__": raise SystemExit(main())
