# Controlled Gemini 3.8 Flash validation — Stage A

Date: 12 November 2026. Baseline commit: `562e5eb feat: implementation of end-to-end workflow`.

## A. Executive summary

**BLOCKED — PREREQUISITES NOT MET: HUMAN IMAGE/GROUND-TRUTH REVIEW PENDING.**
Safe preparation is complete; **zero live Gemini inference requests, zero retries**.
The user authorized at most one potentially billable `gemini-3.8-flash` inference;
that budget has not been consumed and does not need renewed billing approval.
Stage B must wait for the user to confirm this particular displayed image and
its expected observations. No actual Gemini extraction/integration success is
claimed. Do not start Phase 04 or make a second inference after any failure.

## B. Offline preflight and configuration

Initial `git status --short` was empty. `git log --oneline -4` showed `562e5eb`,
`0727e05`, `a7e7156`; latest user commit contains Phase 03. Did not initialize Git,
reset/revert history, recreate deleted handovers, commit/push or modify runtime data.
Read the requested reports/docs, controlling AGENTS and relevant Master Book text,
original PDF pp.11–13,18,20, runner/provider/settings/schema/media/services and
provider/security tests. No missing prerequisite project document blocked preparation.

Credential evidence: **GEMINI_API_KEY_PRESENT=true**. Supported source is the
repository-root `.env` file, loaded explicitly with `--env-file .env` by dotenv;
existing process variables take precedence. `.env` is ignored and untracked.
No key value, authentication header or secret configuration content was printed,
copied into code/reports, transmitted to diagnostics or changed. API key itself
is never included in this report. Before/after file hashes match.

| Check | Actual offline result |
|---|---|
| Model | Exact `gemini-3.8-flash`; no fallback or list-models request |
| Provider | Explicit LIVE_GEMINI for this preflight only |
| SDK | Installed official google-genai 3.2.0; httpx2 2.16.0, no dependency changes |
| Application / SDK / transport | One attempt / zero retries / zero retries |
| Redirects, proxy routing | Disabled by validation-only transport |
| Function calling / continuation / external tools | Disabled; same existing perception prompt/schema |
| Generation settings | Existing temperature 0 and 2048 output-token cap; fixed LOW thinking, include_thoughts=false for exact 3.8 |
| Deadline | 60 seconds total, existing validated maximum; no automatic retry |
| Image | Safe decoder accepts single-frame PNG, 1800×1200 (2,160,000 pixels), within limits |
| Ground truth / schema | Typed existing VisualObservation/EvaluationContext fields valid |
| Human review | **false**, reviewer unset; expected approval checkpoint |
| Offline fixture policy | Expected draft values produce max L2, not an observed Gemini result |
| Request budget | Unused; no local attempt marker or live result artifact |
| Private paths | Image/truth/hash manifest/output path ignored by Git; no public static-media route |

Published model documentation lists image input, structured outputs and
LOW/MEDIUM/HIGH thinking; MINIMAL is unsupported. LOW was selected before any
live response for bounded extraction, not tuned to match expected output.
[Official model capabilities](https://aistudio.google.com/docs/models/gemini-3.8-flash),
[official thinking configuration](https://ai.google.dev/gemini-api/docs/generate-content/thinking).
This is documentation verification, not availability for the user's account.

Settings use existing `GEMINI_MODEL`, `SENTINEL_PROVIDER_MODE`,
`SENTINEL_ALLOW_BILLABLE`, `SENTINEL_PROVIDER_ATTEMPTS` and
`SENTINEL_PROVIDER_TIMEOUT_SECONDS`. Only temporary child PowerShell process
overrides were applied. Normal Settings defaults and production/local `.env`
credentials remain unchanged. General application retry settings were not expanded.

Actual sanitized offline command (executed; **not inference**):

```powershell
$env:GEMINI_MODEL = 'gemini-3.8-flash'
$env:SENTINEL_PROVIDER_MODE = 'LIVE_GEMINI'
$env:SENTINEL_ALLOW_BILLABLE = 'true'
$env:SENTINEL_PROVIDER_ATTEMPTS = '1'
$env:SENTINEL_PROVIDER_TIMEOUT_SECONDS = '60'
.\.venv\Scripts\python.exe -m backend.tools.smoke_gemini --check --env-file .env --image fixtures/live_inputs/gemini_3_8_validation/pump_inspection.png --ground-truth fixtures/live_inputs/gemini_3_8_validation/ground_truth.json --output tracking/LIVE_GEMINI_VALIDATION.local.json
```

Actual output: BLOCKED, network_called=false, request_count=0, retry_count=0,
reason_codes=[HUMAN_IMAGE_AND_GROUND_TRUTH_REVIEW_REQUIRED]. All reported image,
configuration/schema and unused-budget checks pass. Terminal process exit 1 for
the expected blocked native runner (runner guard returns 2). No inference consumed.
Full stdout/commands: `LIVE_GEMINI_VALIDATION_COMMAND_OUTPUT.txt`.

## C. Fictional test image

Created locally with installed Pillow, no external generation service:

- Image: `fixtures/live_inputs/gemini_3_8_validation/pump_inspection.png` (ignored).
- Ground truth: same folder `ground_truth.json` (ignored).
- Image SHA-256: `1d5cb9324088ec180cd70725f14ac33157f5a77c7a5935bd7ee85cf4c7c6046f`.
- Programmatic synthetic inspection card, **not a photograph**. Pump/motor/piping
  context, asset/status/challenge/calibration labels and physical-style circular
  0–60 PSI gauge with five-unit major ticks and one-unit minor ticks.
- Needle is constructed at 292.5 degrees on a clockwise 270-degree scale, exactly
  the 35-PSI position. This construction reference and assistant image inspection
  are not human review or proof of model gauge interpretation.
- No EXIF/GPS/personal/customer records, real challenge credentials or actual asset
  records. Normal safe decoder strips metadata for any later provider input.

Executed `.\.venv\Scripts\python.exe -m backend.tools.prepare_live_sample`;
output origin LOCAL_PILLOW_SYNTHETIC_CARD, human_reviewed=false, network_called=false.
Preparation refuses to overwrite an existing review image or truth file.

## D. Human review — PENDING

The user has **not yet confirmed this image or its ground truth**. Current private
JSON retains `human_reviewed: false`, placeholder reviewer and no approved review
digest. The existing origin enum is a runner convention, not a recorded consent
in the absence of review. No flag was automatically set true.

Draft expected values for the user's inspection:

| Field | Draft expected value |
|---|---|
| Asset ID | PUMP-042 |
| Challenge | DEMO-7C4A-9F2B — fictional visible label, not an application-issued credential |
| Gauge pressure | 35 |
| Unit | PSI |
| Equipment status | RUNNING |
| Calibration expiry | 2099-12-31 |
| Uncertain / conflicting fields | Empty, subject to human confirmation of legibility |

After explicit user confirmation, record the reviewer and true review flag using
the existing runner's ground-truth mechanism. Additional review SHA-256 binds
image digest/model/expected fields/policy context; edits require another review.
Hash is a local change detector, not signed identity or a tamper-proof approval.
The expected-observation and policy-context schemas are retained; added binding
metadata is documented in `docs/media_and_gemini.md`.

## E. Inference execution — NOT RUN

Actual live request count: **0**. Actual retries: **0**. No model availability
probe, billable inference, model fallback, live-to-mock fallback or second call.
No output JSON or reserved-attempt marker has been created for the actual sample.
Transport tests used dummy keys/HTTP MockTransport only, not the user's key.

The existing guarded runner is reused, not a second Gemini integration. Stage B
will use the same reviewed input/output paths and exact process overrides, replace
`--check` with `--allow-billable --confirm-fictional-consent`, **only after review**.
It must pass offline preflight again first. Do not execute that live variant now.

One-request enforcement audited against the installed SDK:

- SDK HttpRetryOptions(attempts=1) maps to tenacity stop_after_attempt(1).
- Application requires provider_attempts=1 for this runner.
- Custom async httpx2 transport forces SDK out of optional aiohttp; underlying
  AsyncHTTPTransport uses retries=0, trust_env=false, no redirect/proxy forwarding.
- Guard permits exactly one POST to the exact Google HTTPS 3.8 generateContent
  path, rejects other paths/models/hosts/query credentials and all synchronous I/O,
  and blocks second sends before the underlying transport.
- Existing provider disables function calls/tools and automatic continuation.
- Before I/O, an exclusive fsynced per-sample marker reserves the budget. Keep it
  after errors/interruption; changing output filename does not allow a second run.
  No automatic marker cleanup or retry exists.

Request count means local attempted transport sends, not proof of Google receipt,
processing or billing. A crash after reservation may leave remote outcome unknown;
conservative behavior is stop without retry. A privileged local operator can alter
files; this is not an adversary-proof financial control or signed ledger.

## F. Gemini results — NOT AVAILABLE

No returned model version, observations, missing/uncertain fields, parser/schema
result or actual needle interpretation is available. No response is fabricated.

## G. Ground-truth comparison — NOT RUN

| Field | Draft expected | Gemini observed | Result |
|---|---|---|---|
| Asset ID | PUMP-042 | Not requested | NOT RUN |
| Challenge | DEMO-7C4A-9F2B | Not requested | NOT RUN |
| Pressure | 35 | Not requested | NOT RUN |
| Unit | PSI | Not requested | NOT RUN |
| Status | RUNNING | Not requested | NOT RUN |
| Calibration expiry | 2099-12-31 | Not requested | NOT RUN |

## H. Independent policy evaluation

No Gemini observation has been evaluated. Offline preflight checks the **draft
expected fixture** only, producing max L2 from unchanged fictional source policy
at its independent fixed fictional time/context. This does not grant a persisted
case permission or prove a live HTTP workflow. No policy thresholds were changed.
No real tenant, database, manager approval, financial action or equipment involved.

New offline regression deliberately supplies a wrong but policy-compliant reading
36 vs independently expected 35: runner labels PARTIAL even though pure Python
could allow L2. This verifies the false-observation limitation; schema/policy-valid
does not mean visually true. Gemini can never create L3 or manager approval.

## I. Performance and usage — NOT MEASURED LIVE

No live latency, usage tokens, cost or billing total available. Token usage is not
claimed zero simply because no response exists. After a later authorized request,
the guard captures only provider-reported numeric usage and safe finish reason;
the runner records elapsed time, exact model/version and counted attempted sends.
No raw headers, reasoning traces or untrusted diagnostic payload is logged.

## J. Security review and narrow changes

- Pure policy/models and manager approval logic unchanged; 33 baseline test/
  policy/manager/dependency/config file hashes match, including all 27 original
  Python test files and `.env`.
- Three-line provider extension fixes LOW thinking only for exact 3.8. Existing
  prompt/schema/output cap/temperature/tools/authority and model fallback behavior
  remain unchanged. Settings/dependency files unchanged; no package installs.
- Extended existing `--check` with paths for meaningful offline preflight; original
  bare-check/no-live-approval guard tests still pass without credential loading.
- Added validation-only send guard, private byte/model/review binding, exclusive
  reservation, usage/counter reporting and truthful PASS/PARTIAL/FAILED distinction.
- Unknown authority fields and nonfinite readings rejected; missing data/wrong
  units/errors restrict as proven by unchanged baseline tests. Models cannot invoke
  roles/policies/payments/approval tools. No public synthetic injection route.
- Real key presence only was inspected; no key copied into tests, logs or reports.
  Local test fixtures explicitly use a dummy credential and block external sockets.
  Windows asyncio loopback self-pipe is allowed, not external Gemini traffic.
- No customer/production image, tenant data exposure, real transfers, equipment,
  infrastructure, cloud resource or external image-generation call. Public Google/
  Protobuf documentation browsing is separate from Gemini API inference.

## K. Actual regressions and commands

| Executed command | Actual result |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest` before edits | 454 passed in 60.34s; exit 0 |
| `.\.venv\Scripts\python.exe -m pytest backend/tests/test_live_validation.py -x` final | 24 passed in 0.92s; exit 0 |
| `.\.venv\Scripts\python.exe -m pytest` final | **478 passed in 66.26s (0:01:06)**; exit 0 |
| `.\.venv\Scripts\python.exe -m pip check` | No broken requirements found.; exit 0 |
| Before/after baseline SHA-256 verification command | 33 baseline test/policy/manager/dependency/config files verified; mismatches=[]; exit 0 |
| `git check-ignore` explicit private paths | `.env`, image, truth, baseline manifest and private result path all ignored; exit 0 |
| `git diff --` policy/models/case_service/requirements/pyproject | No output; exit 0 |
| Detailed offline preflight command in B | Expected BLOCKED only for human review; zero calls/retries |

Two initial **new-test** failures were corrected: blanket socket blocking also
blocked Windows asyncio's loopback self-pipe; then a test assumed camel-case
nested thinking keys while installed SDK serializes original protobuf names.
Allowed only the local event-loop self-pipe and asserted actual supported SDK
serialization with the same LOW/no-thought settings. The official ProtoJSON
spec accepts original and lower-camel field names:
[field name rules](https://protobuf.dev/programming-guides/json/).
No original test or security assertion was weakened. Subsequent 23-test/477-total
runs passed, followed by review-digest protection and the final 24/478 passes.
Coverage not measured. Windows Python 3.14.7 only executed; 3.11/3.12/remote CI
remain unverified. Full actual stdout is retained in the command evidence file.

## L. Limitations

This Stage A is offline preparation, not successful live integration. Even after
one matching synthetic sample, no real-world vision accuracy, gauge reliability,
fraud detection, photographic authenticity, prompt-injection immunity, production
safety or billing total can be inferred. Human labels/calibration tags are only
fictional supporting information. Incorrect but compliant observations can pass
deterministic eligibility. Local file ACLs/backups remain operator-managed;
ignored files are not encrypted. Strict counter bounds attempted sends, not remote
delivery. Old/live runner use now requires exact-model/private input/review binding
metadata; its unreviewed draft example alone is intentionally insufficient.

## M. Git status and manifest

Modified: `backend/app/gemini_provider.py`, `backend/tools/smoke_gemini.py`,
`docs/media_and_gemini.md`, `tracking/STATUS_LEDGER.md`,
`tracking/REQUIREMENT_MATRIX.md`, `tracking/EXECUTION_LOG.md`.

Added: `backend/tools/live_validation_guard.py`,
`backend/tools/prepare_live_sample.py`, `backend/tests/test_live_validation.py`,
this report, `tracking/LIVE_GEMINI_VALIDATION_COMMAND_OUTPUT.txt`.

Ignored local additions: fictional PNG, unreviewed ground truth, baseline hash
manifest under `fixtures/live_inputs/gemini_3_8_validation/`; no actual attempt
marker or live result. Existing `.env`, runtime database and media untouched.
Final actual `git status --short --untracked-files=all` (six modified, five new;
none staged, no deletions):

```text
 M backend/app/gemini_provider.py
 M backend/tools/smoke_gemini.py
 M docs/media_and_gemini.md
 M tracking/EXECUTION_LOG.md
 M tracking/REQUIREMENT_MATRIX.md
 M tracking/STATUS_LEDGER.md
?? backend/tests/test_live_validation.py
?? backend/tools/live_validation_guard.py
?? backend/tools/prepare_live_sample.py
?? tracking/LIVE_GEMINI_VALIDATION_COMMAND_OUTPUT.txt
?? tracking/LIVE_GEMINI_VALIDATION_REPORT.md
```

`git diff --check` passed (only existing Windows LF/CRLF notices); five current
documentation files have no missing relative link targets. Full command evidence
is retained. Private image/truth/config are absent from Git status as intended.
No staging, commit, push, deploy, reset, remote or Phase 04 work.

## N. Recommendation / next gate

Present the exact image and draft values to the user; request **only image and
ground-truth confirmation**, not billing approval again. User request section 8
explicitly says: "STOP AT THIS CHECKPOINT IF HUMAN REVIEW HAS NOT OCCURRED."
Keep review false until confirmation. Then bind the reviewed values, rerun offline
preflight, and make the single authorized exact-model request through this runner.
On any API/schema/provider/configuration failure, stop without retry/fallback.
Compare each actual field, separately report offline policy result and false-
observation risk, record usage/counters/limitations, rerun regressions and stop.
Phase 04 still requires separate user authorization.

Rollback (not performed): preserve the ignored review artifacts, credentials and
all runtime data. Review/revert only this checkpoint's listed code/docs changes
after user direction. Do not erase a later attempt marker or output to repeat a
call; do not delete databases/media or reset Git history.
