"""Guarded one-request fictional-image validation; never business authority.

--check with paths performs an offline preflight. --check alone or omitted live
approval flags never loads credentials or constructs a provider.
"""

import argparse
import asyncio
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from time import monotonic

from dotenv import load_dotenv

from backend.app.config import load_policy
from backend.app.gemini_provider import GeminiPerceptionProvider
from backend.app.media import validate_image
from backend.app.models import EvaluationContext
from backend.app.perception import PerceptionInput, ProviderError, VisualObservation
from backend.app.policy import authorize
from backend.app.settings import Settings
from backend.tools.live_validation_guard import SingleRequestGuard

MODEL = "gemini-3.8-flash"
ROOT = Path(__file__).resolve().parents[2]


def review_digest(truth):
    """Bind human confirmation to exact image/model/expected fields/context."""
    content = {name: truth[name] for name in ("image_sha256", "validation_model", "expected_observation", "policy_context")}
    return sha256(json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def ignored(path):
    return subprocess.run(["git", "check-ignore", "-q", "--", str(path)], cwd=ROOT,
                          capture_output=True).returncode == 0


def preflight(args):
    """No inference, SDK client or artifact write; bool-only key reporting."""
    checks, reasons, payload = {}, [], None
    try:
        if args.env_file:
            if not args.env_file.is_file() or not ignored(args.env_file):
                raise ValueError("Private environment file required")
            tracked = subprocess.run(["git", "ls-files", "--", str(args.env_file)], cwd=ROOT,
                                     capture_output=True, text=True).stdout.strip()
            if tracked:
                raise ValueError("Secret configuration must not be tracked")
            load_dotenv(args.env_file, override=False)
        checks["GEMINI_API_KEY_PRESENT"] = bool(os.getenv("GEMINI_API_KEY", "").strip())
        settings = Settings.from_env()
        checks.update(requested_model_id=settings.gemini_model, provider_mode=settings.provider_mode,
            model_exact=settings.gemini_model == MODEL, one_attempt=settings.provider_attempts == 1,
            billing_scope_configured=settings.allow_billable,
            timeout_seconds=settings.provider_timeout_seconds, max_output_tokens=2048,
            thinking_level="LOW", sdk_retries=0, redirects=False, automatic_continuation=False,
            tools_enabled=False, request_budget=1)
        if settings.provider_mode != "LIVE_GEMINI" or settings.gemini_model != MODEL or settings.provider_attempts != 1:
            reasons.append("EXACT_MODEL_LIVE_MODE_AND_ONE_ATTEMPT_REQUIRED")
        private_inputs = ROOT / "fixtures/live_inputs"
        for path in (args.image, args.ground_truth):
            if not path.is_file() or not path.resolve().is_relative_to(private_inputs.resolve()) or not ignored(path):
                raise ValueError("Input must exist under ignored private live_inputs")
        if not args.output.name.endswith(".local.json") or not ignored(args.output) or args.output.exists():
            reasons.append("NEW_IGNORED_PRIVATE_OUTPUT_REQUIRED")
        truth = json.loads(args.ground_truth.read_text(encoding="utf-8"))
        expected = VisualObservation.model_validate(truth["expected_observation"])
        context = EvaluationContext.model_validate(truth["policy_context"])
        with args.image.open("rb") as file:
            raw = file.read(settings.max_image_bytes + 1)
        image = validate_image(raw, "application/octet-stream", settings)
        checks.update(image_valid=True, image_sha256=image.sha256, width=image.width, height=image.height,
                      private_inputs=True, structured_schema_available=bool(VisualObservation.model_json_schema()))
        if truth.get("image_sha256") != image.sha256 or truth.get("validation_model") != MODEL:
            reasons.append("IMAGE_DIGEST_AND_MODEL_BINDING_REQUIRED")
        checks["human_reviewed"] = truth.get("human_reviewed") is True
        if truth.get("origin") != "CONSENTED_FICTIONAL_NO_CUSTOMER_DATA" or not checks["human_reviewed"] or not truth.get("reviewed_by") or truth["reviewed_by"] == "REPLACE_WITH_HUMAN_REVIEWER":
            reasons.append("HUMAN_IMAGE_AND_GROUND_TRUTH_REVIEW_REQUIRED")
        elif truth.get("human_review_sha256") != review_digest(truth):
            reasons.append("HUMAN_REVIEW_BINDING_MISSING_OR_CHANGED")
        policy = load_policy(ROOT / "policies/maintenance_v1.json")
        expected_decision = authorize(expected.observation("LIVE_GEMINI"), policy, context)
        checks["expected_fixture_policy_max_permission"] = expected_decision.max_permission
        if expected_decision.max_permission != 2 or expected.uncertain_fields or expected.conflicting_fields:
            reasons.append("REVIEW_EXPECTED_VALUES_AND_FICTIONAL_POLICY_CONTEXT")
        marker = args.ground_truth.parent / "one_live_attempt.local.json"
        checks["request_budget_unused"] = not marker.exists()
        if marker.exists():
            reasons.append("ONE_REQUEST_ALREADY_RESERVED_NO_RETRY_AUTHORIZED")
        payload = (settings, truth, expected, context, image, policy, marker)
    except Exception:
        reasons.append("CHECK_PRIVATE_CONFIG_IMAGE_AND_GROUND_TRUTH")
    report = dict(status="BLOCKED" if reasons else "READY", provider_mode="LIVE_GEMINI",
                  network_called=False, request_count=0, retry_count=0, checks=checks, reason_codes=reasons)
    return report, payload


def write_private(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        json.dump(report, output, indent=2, allow_nan=False)
        output.flush()
        os.fsync(output.fileno())


def main():
    parser = argparse.ArgumentParser(description="One approved gemini-3.8-flash fictional-image evaluation; no business authority.")
    parser.add_argument("--check", action="store_true", help="Offline detailed preflight with all input/output paths.")
    parser.add_argument("--image", type=Path)
    parser.add_argument("--ground-truth", type=Path)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-billable", action="store_true")
    parser.add_argument("--confirm-fictional-consent", action="store_true")
    args = parser.parse_args()
    inputs = args.image and args.ground_truth and args.output
    if (args.check and not inputs) or (not args.check and (not args.allow_billable or not args.confirm_fictional_consent)):
        print(json.dumps(dict(status="BLOCKED", provider_mode="LIVE_GEMINI", network_called=False,
                              reason_codes=["LIVE_APPROVAL_AND_FICTIONAL_IMAGE_CONSENT_REQUIRED"])))
        return 2
    if not inputs:
        print(json.dumps(dict(status="BLOCKED", network_called=False,
                              reason_codes=["IMAGE_MANUAL_GROUND_TRUTH_AND_PRIVATE_OUTPUT_REQUIRED"])))
        return 2
    check, payload = preflight(args)
    if args.check or check["status"] != "READY":
        print(json.dumps(check))
        return 0 if check["status"] == "READY" else 2

    settings, truth, expected, context, image, policy, marker = payload
    guard = SingleRequestGuard(MODEL)
    started = monotonic()
    reserved = False
    try:
        # Durable reservation before any possible I/O. Never auto-remove/retry it,
        # including after a crash before output is saved.
        write_private(marker, dict(status="ONE_REQUEST_RESERVED_NO_AUTOMATIC_RETRY",
            requested_model_id=MODEL, original_sha256=image.sha256, request_count=None,
            limitation="Reservation is not delivery or billing proof; preserve after interruption."))
        reserved = True
        provider = GeminiPerceptionProvider(settings, client_factory=guard.client_factory)
        try:
            result = asyncio.run(provider.inspect(PerceptionInput(image.provider_bytes, "image/png", "consented-fictional-live-smoke")))
            comparison = {name: getattr(result.fields, name) == getattr(expected, name) for name in VisualObservation.model_fields}
            matched = all(comparison.values())
            decision = authorize(result.fields.observation("LIVE_GEMINI"), policy, context)
            report = dict(status="COMPLETED", validation_result="PASS - FIRST LIVE SAMPLE MATCHED GROUND TRUTH" if matched else "PARTIAL - LIVE REQUEST SUCCEEDED WITH OBSERVATION ERRORS",
                requested_model_id=MODEL, returned_model_version=result.model_version,
                observations=result.fields.model_dump(mode="json"), ground_truth_comparison=comparison,
                authorization_decision=decision.model_dump(mode="json"))
        except ProviderError as exc:
            report = dict(status="FAILED", validation_result="FAILED - LIVE API OR SCHEMA ERROR",
                          requested_model_id=MODEL, reason_codes=[exc.code], authorization_decision="DENY")
        report.update(provider_mode="LIVE_GEMINI", network_called=guard.request_count > 0,
            request_count=guard.request_count, retry_count=0, elapsed_seconds=monotonic()-started,
            input_media_type=image.mime_type, provider_media_type="image/png", original_sha256=image.sha256,
            provider_sha256=image.provider_sha256, transport_metadata=guard.response_metadata,
            scope="OFFLINE_GROUND_TRUTH_COMPARISON_NOT_AUTHENTICATED_API_AUTHORIZATION",
            limitation="One synthetic sample is not real-world accuracy, authenticity, safety or workflow proof.")
        write_private(args.output, report)
        print(json.dumps({key: value for key, value in report.items() if key not in {"observations", "original_sha256", "provider_sha256"}}, default=str))
        return 0 if report.get("validation_result", "").startswith("PASS") else 1
    except Exception:
        print(json.dumps(dict(status="FAILED" if reserved else "BLOCKED", provider_mode="LIVE_GEMINI",
            network_called=guard.request_count > 0, request_count=guard.request_count, retry_count=0,
            reason_codes=["VALIDATION_FAILED_DO_NOT_RETRY"], authorization_decision="DENY")))
        return 1 if reserved else 2


if __name__ == "__main__":
    raise SystemExit(main())
