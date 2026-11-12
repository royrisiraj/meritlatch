# Phase 02 — private image evidence and untrusted perception

Use the existing `backend.app.api:create_app --factory`. No old backend rebuild,
frontend, video, cloud adapter or real financial action is introduced.

Phase 03 extends this retained intake with manager review/rejection, safely bound
upload replay and explicit provider reanalysis. Current recovery/API contracts:
[`workflow_phase03.md`](workflow_phase03.md). Live verification remains separately
BLOCKED - AWAITING AUTHORIZATION.

## Upload contract

`POST /v1/cases/{case_id}/evidence` accepts the raw JPEG/PNG bytes as its body.
It is not a JSON observation or multipart injection endpoint. Required headers:

```text
Authorization: Bearer <authenticated assigned contractor token>
Content-Type: image/jpeg               (or image/png; octet-stream is decoded)
X-Expected-Case-Version: <current case version>
X-Challenge-ID: <server-issued challenge ID>
X-Evidence-Session-ID: <server-issued evidence session>
```

Roles/tenant/job assignments are checked before media processing, and again at
acceptance/finalization. The challenge must be active and belong to this tenant,
job, asset, case, contractor login session and evidence session. Clients cannot
set the challenge token, authoritative asset, expiry, provider label, observations,
model choice, policy or tier through this endpoint. MIME and filenames confer no
trust: actual signatures, decoder format, verification and full decode must agree.

Defaults: 5 MiB original bytes, 4,000,000 decoded pixels, maximum dimension 4096,
one frame. JSON routes remain bounded to 16 KiB. Both streamed/chunked and declared
length bodies are bounded. JPEG and PNG only; GIF/APNG animation/video/MP4 are
deferred. Decompression warnings/errors, truncated files, oversized dimensions
and invalid media fail closed. Configured limits may be lowered; hard upper
bounds prevent accidentally disabling the image resource limits.

The raw original receives an exact SHA-256. Duplicate lookup is tenant-scoped
and transactionally protected, including a unique constraint. Duplicate bytes
return `409 EXACT_DUPLICATE` without revealing another case's IDs or records.
This is a byte-reuse flag, **not a finding of fraud or authenticity**. Edited images
can evade exact matching. No perceptual hashing or anti-deepfake certification exists.

Raw files use randomized server-only names under `backend/private_media/`, excluded
from Git, and are never mounted as static files. The storage protocol can later
be implemented for Cloud Storage; no cloud adapter is implemented or verified.
Local file confidentiality still depends on the operator's Windows ACLs.

EXIF/GPS are optional, untrusted supporting claims. Only presence and a narrowly
formatted claimed capture time are stored as metadata; no coordinates authorize
anything. Missing data is UNKNOWN. The private original preserves original bytes.
Provider input is a fully decoded, oriented, white-composited RGB PNG with EXIF,
GPS and text metadata stripped. Original and normalized provider-input digests are
recorded separately. Pixel text is still untrusted and can contain injection.

## Two-phase state transition

Acceptance inserts a new append-only evidence/version and media record, clears
approval and advances the case version in one SQLite transaction. State is
`OBSERVATION_PENDING`, max permission 0 while the model is running. Private file
creation is cleaned up on a known DB rollback. Filesystem and DB are not one
distributed transaction: a process crash can leave an orphan file or pending
record. Neither state grants a restricted action. Retention/recovery tooling is
not implemented in this phase.

Provider I/O occurs outside the DB lock. Finalization rechecks current identity,
assignment, case/evidence version, active challenge/session, expiry and current
state before appending the validated analysis and advancing the case version.
An intervening evidence/invoice/policy/challenge/assignment/session change makes
the result stale; it is discarded for authorization. Both out-of-order completion
orders are tested with actual concurrent HTTP requests and SQLite connections.

The pure engine remains unchanged and caps observations at L2. IDs, numeric
values, units, fictional policy bounds, dates and uncertainty are independently
evaluated. Unsafe pressure/expired tags produce SAFETY_ALERT, never L2/L3.
Missing/uncertain/conflicting interpretation stays restricted. L3 still requires
the existing independent current-state manager approval. New accepted evidence
invalidates an old L3 immediately, even if perception subsequently fails.

`media_uploads` and `media_analyses` are append-only, with their own additive
`media_schema_migrations` version 1. The accepted core schema version 1 remains
unchanged. Migration tests preserve legacy records and reject unknown versions.
This is logical audit history, not an immutable database.

## Reading private media

`GET /v1/cases/{case_id}/evidence/{evidence_id}/content` requires the current
assigned contractor or a same-tenant manager. Only current evidence is served;
engineers and service agents cannot download raw media. Bytes are checked against
the stored digest before serving. The response is an attachment with no-store,
nosniff and a restrictive CSP. Paths/storage keys are never returned. Cross-tenant
and unassigned reads return scoped errors without hashes or internal references.

Case views expose current evidence ID/hash, provider label, configured/requested
model ID, returned model version when available, analysis status, typed observations
for contractor/manager, and bounded provenance. Observed challenge text is omitted
from case/API/audit views; the backend still independently checks it. Engineers
retain redacted views. Audit/exception output does not contain raw model payloads,
credentials, challenges or file paths.

## Provider modes and configuration

`DISABLED` is the default: no image analysis and no implicit network call.
`MOCK_AI` is explicit local development/test mode. Its default observer returns
UNKNOWN data, never fabricated matching readings. Positive canned responses are
configured in internal tests/smoke, not via HTTP or a public fixture endpoint.
`LIVE_GEMINI` uses the official `google-genai` SDK and requires a key plus explicit
billing approval. No provider failure switches to mock. Saved mock observations
cannot authorize when the application leaves mock mode.

The adapter receives only normalized bytes/MIME and a source evidence ID. It does
not receive login credentials, approval keys, policy rules, expected asset/challenge
values or financial data. It imports no authorization/policy implementation. No
tools or automatic function calling/continuation are enabled. Model JSON contains
observations only; artifact/model/source metadata is attached by backend code.
Strict Pydantic validation and numeric/date/conflict checks are applied again at
the integration boundary, including unchecked model copies.

Current official documentation was checked on 12 November 2026. The configurable
default `gemini-3.6-flash` is listed as stable and supports image input and
structured outputs. Account/region availability has **not** been authenticated
or live-tested. A 404 remains a fail-closed provider-unavailable error; operators
can change `GEMINI_MODEL` without code changes. Sources:
[model capabilities](https://aistudio.google.com/docs/models/gemini-3.6-flash),
[image understanding/inline-size limits](https://aistudio.google.com/docs/image-understanding),
[structured output](https://aistudio.google.com/docs/structured-output),
[official Python SDK](https://github.com/googleapis/python-genai).

Default total provider deadline is 20 seconds, maximum 60; attempts default to 1,
maximum 2. SDK-internal retries are disabled. Optional second attempts retry only
selected transient server statuses; quota/auth errors are not retried. No quota,
latency, cost or extraction-accuracy benchmark is claimed. Unknown SDK errors are
redacted. Failed analysis persists REVIEW_REQUIRED/max 0 and returns 502/504.

There is no automatic reanalysis job. Phase 03 adds an explicitly authorized
reanalysis endpoint for recoverable failed/stale/interrupted attempts and an
optional operation-bound upload idempotency key. Default byte-identical upload
still returns EXACT_DUPLICATE. Successful but insufficient/unsafe observations,
schema-invalid/blocked results and rejected evidence need correction, not repeat
inference. Recovery preserves original bytes/evidence version, records separate
attempts, rechecks current state and is bounded to three explicit retries. See
the Phase 03 contract for session/challenge/version/billing and replay rules.

## Windows commands

```powershell
Set-Location D:\project\sentinel_ladder_v2
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase02
```

For local manually authenticated HTTP exploration, with unknown-only mock output:

```powershell
.\.venv\Scripts\python.exe -m backend.tools.manage init-demo
$env:SENTINEL_PROVIDER_MODE = 'MOCK_AI'
.\.venv\Scripts\python.exe -m uvicorn backend.app.api:create_app --factory --host 127.0.0.1 --port 8000
```

Provisioning uses hidden independent passwords. Swagger `/docs` documents the raw
image body and binding headers. Do not put tokens in shell history or URLs.
The smoke command uses an actual loopback Uvicorn listener and image POST,
ephemeral credentials, private temporary files and a visibly fictional test card.
It uses a canned MOCK_AI observation and does not measure visual extraction.

Optional process variables (see `.env.example`): `SENTINEL_MEDIA_ROOT`,
`SENTINEL_MAX_IMAGE_BYTES`, `SENTINEL_MAX_IMAGE_PIXELS`,
`SENTINEL_MAX_IMAGE_DIMENSION`, `SENTINEL_PROVIDER_TIMEOUT_SECONDS`,
`SENTINEL_PROVIDER_ATTEMPTS`, `GEMINI_MODEL`, `GEMINI_API_KEY` and
`SENTINEL_ALLOW_BILLABLE`. `.env` is loaded only explicitly with Uvicorn
`--env-file .env` or the live smoke's `--env-file .env`; existing environment values
take precedence. Never commit `.env` or actual media/ground truth with private data.

## Separate live verification — currently BLOCKED

No live call is authorized by implementation/testing alone. A consented fictional
image and independent manual ground truth must be supplied. Do not use customer
images. `fixtures/live_ground_truth.example.json` is an unreviewed template,
**not an independently labeled evaluation sample**. Copy/edit it privately under
`fixtures/live_inputs/`, record observed fields without consulting model output,
and have a human review it before setting its review/consent flags.

Safe readiness check (no credentials read, no network):

```powershell
.\.venv\Scripts\python.exe -m backend.tools.smoke_gemini --check
```

The dedicated post-Phase-03 validation checkpoint targets **gemini-3.8-flash**
through a temporary process `GEMINI_MODEL` override; the normal application default
and `.env` are preserved. See
[`LIVE_GEMINI_VALIDATION_REPORT.md`](../tracking/LIVE_GEMINI_VALIDATION_REPORT.md).
The user confirmed the exact image and ground truth after Stage A. Stage B's
**single authorized request failed with PROVIDER_UNAVAILABLE** (one counted send,
zero retries, 4.6740s). No observations or usage were returned; no retry/fallback
was attempted. Keep the private reservation/result. The one-call budget is used;
do not remove the marker, change filenames or repeat inference under this approval.

The existing runner now supports detailed **offline** `--check` with all paths.
This form reads the ignored explicit env file securely, reports only key presence,
validates bytes/schema/model/config/private paths/review binding/request budget,
and never constructs a provider or reserves an attempt. Run in a disposable
PowerShell terminal so the overrides do not affect another server:

```powershell
$env:GEMINI_MODEL = 'gemini-3.8-flash'
$env:SENTINEL_PROVIDER_MODE = 'LIVE_GEMINI'
$env:SENTINEL_ALLOW_BILLABLE = 'true'
$env:SENTINEL_PROVIDER_ATTEMPTS = '1'
$env:SENTINEL_PROVIDER_TIMEOUT_SECONDS = '60'
.\.venv\Scripts\python.exe -m backend.tools.smoke_gemini --check --env-file .env --image fixtures/live_inputs/gemini_3_8_validation/pump_inspection.png --ground-truth fixtures/live_inputs/gemini_3_8_validation/ground_truth.json --output tracking/LIVE_GEMINI_VALIDATION.local.json
```

During Stage A, `human_reviewed` stayed false and this returned BLOCKED,
request_count=0. Never toggle review fields without actual user review. After explicit
confirmation, record the reviewer, `human_reviewed: true` and `human_review_sha256`
from the runner's `review_digest(truth)`, binding the exact expected observations,
policy context, image SHA-256 and model. Changed reviewed inputs block execution.
This local binding detects edits; it is not a signed identity or authenticity proof.
The original expected-observation/policy-context field names are retained;
`validation_model`, `image_sha256` and review digest are additional safety metadata.
The local Pillow preparation tool creates the ignored image/unreviewed draft and
refuses to overwrite existing review artifacts. Its card is not a photograph.

The validation runner reuses `GeminiPerceptionProvider` and its existing prompt/
schema. A tool-only SDK transport permits exactly one attempted HTTPS POST to
the exact 3.8 model endpoint, disables redirects/proxies/transport retries, rejects
synchronous/other-destination/second sends, and records safe usage metadata when
provided. SDK/application attempts are one; tools/function calling/continuation
remain disabled. 3.8 uses documented LOW thinking, no thought summaries, and the
existing 2048-token cap. No generation parameter is tuned against returned output.
Before I/O, an exclusive fsynced `one_live_attempt.local.json` marker under the
private input folder reserves the checkpoint. Preserve it after errors/crashes;
changing output filenames does not authorize another call. Request count means
local attempted sends, not proof of remote delivery/processing or billing.

The older generic live example below requires these reviewed binding fields and
the exact 3.8 override at this checkpoint. Do not execute without human confirmation.

After explicit user approval for one potentially billable call, valid key/model
configuration, reviewed fictional input and consent, the operator can run:

```powershell
.\.venv\Scripts\python.exe -m backend.tools.smoke_gemini --env-file .env --image fixtures/live_inputs/fictional.jpg --ground-truth fixtures/live_inputs/truth.json --output tracking/LIVE_GEMINI_SMOKE.local.json --allow-billable --confirm-fictional-consent
```

That command additionally requires configured LIVE_GEMINI, billing enabled and
one attempt. It records requested model, returned version, original media type,
elapsed time, structured observations, independent field comparison, policy
decision and redacted errors in an ignored `.local.json` output. It performs an
**offline policy comparison with the supplied fixture context**, not an authenticated
API action or approval. It never grants L3. One sample cannot establish accuracy.
No such live call has been executed for this phase.

## Remaining limits

Typed/schema-valid data can be semantically false. Prompts, challenge text, SHA-256,
metadata stripping and a valid model response do not establish authenticity,
completed repair or safe real equipment. Humans remain responsible for review.
The demo policy is fictional. No face recognition, EXIF location authorization,
video parsing, real transfers, cloud storage/deployment or automatic policy
rewriting is present. Local ACLs, global abuse limits, retention/recovery, malware
scanning and production load require further work. SDK/decoder dependencies must
be maintained. Python 3.11/3.12 and remote CI remain unexecuted.
