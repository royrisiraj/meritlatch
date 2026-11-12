# Controlled Gemini 3.8 Flash validation — Stage B

Date: 12 November 2026. Stage B baseline: user commit dff9f41.
Initial git status was clean. Stage A is committed in that baseline.

## A. Executive summary

**FAILED — LIVE API OR SCHEMA ERROR**, reason **PROVIDER_UNAVAILABLE**.
After explicit human review and READY offline preflight, the existing guarded
runner made **one counted gemini-3.8-flash request attempt, zero retries**.
Elapsed: **4.6740026 seconds**. Failure returned **DENY**, with no observations,
returned model version or usage. No retry, model fallback, mock substitution or
additional Gemini request followed. The one-call authorization is used.

Post-request regressions: **478 passed, zero failed, in 58.30s**. Stage B changed
no source, runner, provider, test, dependency, policy, manager logic or credential
file. Stop before Phase 04. No staging, commit, push, deployment or paid resource
provisioning occurred.

## B. Preflight

**GEMINI_API_KEY_PRESENT=true**. Existing explicit --env-file .env loading was
used, with process environment precedence. The credential file is ignored,
untracked and unchanged. No key value, authentication header or secret content
was printed, copied to reports or sent to an external diagnostic service.

After recording review, executed the existing runner's detailed --check mode
with the same environment/paths as E, excluding its live consent flags.
Actual exit 0: READY, reason_codes=[], network_called=false, request_count=0,
retry_count=0. Exact command and full output are in the command evidence.

| Check | Actual offline result |
|---|---|
| Model / provider | Exact gemini-3.8-flash / LIVE_GEMINI |
| Application attempts / SDK retries / transport retries | 1 / 0 / 0 |
| Redirects / proxies / automatic continuation / tools | Disabled |
| Thinking / output cap / temperature | LOW, no thought summaries / 2048 / existing 0 |
| Deadline | 60 seconds, existing validated maximum |
| Image | Safe-decoded single-frame PNG, 1800×1200, private ignored path |
| Schema / expected fixture | Existing typed observations/context; expected fixture max L2 |
| Human review | true; exact image/model/expected/context binding valid |
| Budget before call | Unused; no existing marker/result |
| Output | New ignored private .local.json path |

Only child-process overrides were used. Normal Settings defaults, .env and
dependency pins remained unchanged. Installed official SDK: google-genai 3.2.0,
httpx2 2.16.0. Stage A's references:
[model capabilities](https://aistudio.google.com/docs/models/gemini-3.8-flash),
[thinking configuration](https://ai.google.dev/gemini-api/docs/generate-content/thinking).
Published support does not establish successful availability for this account;
the actual request failed.

## C. Test image

Ignored local file: fixtures/live_inputs/gemini_3_8_validation/pump_inspection.png.

SHA-256: 1d5cb9324088ec180cd70725f14ac33157f5a77c7a5935bd7ee85cf4c7c6046f.

Locally drawn Pillow synthetic inspection card, **not a photograph**. Fictional
pump/motor context; asset/status/challenge/calibration labels; circular 0–60 PSI
gauge with one-unit ticks/five-unit major ticks and needle at 35 PSI (292.5 degrees
on a clockwise 270-degree sweep). The user personally confirmed needle, scale
and labels. Original image/digest and expected values were unchanged. No customer
data, EXIF/GPS or real asset/challenge credential. Existing decoder normalized
the image to PNG before the request.

## D. Human review — CONFIRMED

User explicitly confirmed personal review of the displayed image and all values,
including gauge needle/scale. Private ground truth now records:

- human_reviewed=true.
- reviewed_by=USER_EXPLICIT_CONFIRMATION_IN_CONVERSATION.
- human_reviewed_at_utc=2026-11-12T16:16:45.498201+00:00.
- human_review_sha256 binds unchanged image/model/expected fields/policy context.
- Confirmation permits Stage B subject to preflight, at most one request, no retries.

| Field | Human-confirmed value |
|---|---|
| Asset | PUMP-042 |
| Pressure / unit | 35 PSI |
| Status | RUNNING |
| Calibration expiry | 2099-12-31 |
| Challenge | DEMO-7C4A-9F2B — fictional label, not an application credential |

Review file: fixtures/live_inputs/gemini_3_8_validation/ground_truth.json (ignored).
Review hash detects local edits; it is not signed identity or authenticity proof.

## E. Inference execution — ONE ATTEMPT, FAILED

Executed exactly once after READY preflight, with explicit network permission
for the already-authorized request, using the existing guarded runner:

~~~powershell
$env:GEMINI_MODEL = 'gemini-3.8-flash'
$env:SENTINEL_PROVIDER_MODE = 'LIVE_GEMINI'
$env:SENTINEL_ALLOW_BILLABLE = 'true'
$env:SENTINEL_PROVIDER_ATTEMPTS = '1'
$env:SENTINEL_PROVIDER_TIMEOUT_SECONDS = '60'
.\.venv\Scripts\python.exe -m backend.tools.smoke_gemini --env-file .env --image fixtures/live_inputs/gemini_3_8_validation/pump_inspection.png --ground-truth fixtures/live_inputs/gemini_3_8_validation/ground_truth.json --output tracking/LIVE_GEMINI_VALIDATION.local.json --allow-billable --confirm-fictional-consent
~~~

Actual exit 1, sanitized output:

~~~json
{
  "status": "FAILED",
  "validation_result": "FAILED - LIVE API OR SCHEMA ERROR",
  "requested_model_id": "gemini-3.8-flash",
  "reason_codes": ["PROVIDER_UNAVAILABLE"],
  "authorization_decision": "DENY",
  "provider_mode": "LIVE_GEMINI",
  "network_called": true,
  "request_count": 1,
  "retry_count": 0,
  "elapsed_seconds": 4.6740025999988575,
  "input_media_type": "image/png",
  "provider_media_type": "image/png",
  "transport_metadata": {},
  "scope": "OFFLINE_GROUND_TRUTH_COMPARISON_NOT_AUTHENTICATED_API_AUTHORIZATION",
  "limitation": "One synthetic sample is not real-world accuracy, authenticity, safety or workflow proof."
}
~~~

Actual private result: tracking/LIVE_GEMINI_VALIDATION.local.json (ignored).
Exclusive fsynced reservation:
fixtures/live_inputs/gemini_3_8_validation/one_live_attempt.local.json (ignored),
status ONE_REQUEST_RESERVED_NO_AUTOMATIC_RETRY. Marker preserved unchanged; the
result records the attempted send. Changing output filenames cannot bypass the
reserved per-sample budget. Do not clear it to retry.

Count is local attempted transport sends, not proof of remote processing or
billing. No second call, alternate model, proxy, redirect, tool continuation or
mock fallback. Exact endpoint/one-send transport and SDK/application one-attempt
configuration were retained. No application or adapter code changed.

## F. Gemini results — NO OBSERVATIONS RETURNED

Only safe reason PROVIDER_UNAVAILABLE is available. No structured observations,
model version, missing/uncertain-field set, schema-valid output or actual gauge
interpretation exists. No response is fabricated or replaced with canned fields.

The adapter groups multiple API failures under this code; specific HTTP status/
raw provider response was not retained. This evidence cannot distinguish a 400,
404 or server error, identify its exact cause, or establish model availability
for this key. No diagnostic request followed failure.

## G. Ground-truth comparison — NOT EVALUABLE

| Field | Human-confirmed expected | Gemini observed | Result |
|---|---|---|---|
| Asset ID | PUMP-042 | Unavailable — provider failure | NOT EVALUABLE |
| Challenge | DEMO-7C4A-9F2B | Unavailable — provider failure | NOT EVALUABLE |
| Pressure | 35 | Unavailable — provider failure | NOT EVALUABLE |
| Unit | PSI | Unavailable — provider failure | NOT EVALUABLE |
| Status | RUNNING | Unavailable — provider failure | NOT EVALUABLE |
| Calibration expiry | 2099-12-31 | Unavailable — provider failure | NOT EVALUABLE |

Gemini needle/scale interpretation remains unverified. A failed API attempt does
not establish successful perception.

## H. Independent policy evaluation

No typed live observation was returned, so actual Gemini observations could not
be evaluated by the pure Python policy. Failure branch returned DENY, with no
persisted case permission, manager approval or business action. The preflight
separately evaluates the unchanged **expected-value fixture**, producing max L2
under its independent fictional policy/time/context. That is not live perception
or an authenticated HTTP workflow result. Thresholds were not changed.

Existing offline regression independently verifies the false-observation risk:
wrong but compliant 36 PSI can earn L2 while comparison against expected 35 marks
PARTIAL. This remains a limitation, not a measured live finding here. Schema and
policy compliance cannot prove visual truth. Gemini cannot create L3, change
roles/policies, approve money or execute maintenance.

## I. Performance and usage

Failed-attempt elapsed: **4.6740025999988575 seconds**, measured by the runner.
This is not successful-inference latency. Provider usage metadata was empty;
token counts, returned model/version, costs, billing total and remote processing
are **unavailable**, not assumed zero. No extra request was made to obtain them.

## J. Security review

- User review was recorded only after explicit confirmation; exact reviewed
  image/expected fields/model/context remain bound.
- Existing guard allows one exact-model HTTPS POST, no retries/redirects/proxies,
  synchronous network operations or second send. Function calling, continuation
  and tools remain disabled.
- Prompt/schema receive only pixels and fixed extraction instructions, not
  independent expected answers, policies, approval credentials or authority.
- No raw errors, API key, auth header, secret configuration, reasoning trace or
  customer evidence was printed/logged. Credential reporting is presence only.
- Provider failure restricted to DENY. No policy/role/payment/approval tool or L3,
  money movement, equipment control or real maintenance action.
- No production tenant/case, SQLite database or private runtime media changed.
- 37 baseline test/source/policy/manager/dependency/config hashes match; backend
  Git diff is empty. All 478 prior tests retained with no weakened assertion.
- Marker/result ignored/private; not a tamper-proof ledger. ACLs/privileged file
  access remain operator responsibilities.
- After failure, only local tests/hash checks/documentation. No further API,
  availability probe, inference or fallback.

## K. Executed regression and command evidence

| Actual command/check | Actual result |
|---|---|
| Detailed offline preflight | READY, zero calls/reasons; exit 0 |
| .\.venv\Scripts\python.exe -m pytest backend/tests/test_live_validation.py before request | 24 passed in 3.09s; exit 0 |
| Single guarded live command in E | PROVIDER_UNAVAILABLE, one attempt, zero retries; exit 1 |
| .\.venv\Scripts\python.exe -m pytest after request | **478 passed in 58.30s**; exit 0 |
| .\.venv\Scripts\python.exe -m pip check | No broken requirements found.; exit 0 |
| SHA-256 post-request check | 37 baseline files verified; mismatches=[]; exit 0 |
| git diff -- backend | Empty output; exit 0 |
| Explicit git check-ignore | .env, truth, marker, snapshot/private result ignored; exit 0 |

Actual final stdout:

~~~text
============================ 478 passed in 58.30s =============================
~~~

Exact commands/stdout/stderr appended to
[command evidence](LIVE_GEMINI_VALIDATION_COMMAND_OUTPUT.txt). Stage A's successful
offline preparation/tests remain historical evidence there. Stage B added or
changed no source, test or package. Coverage not measured. Actual installed
runtime: Windows Python 3.14.7. Python 3.11/3.12 and remote CI remain unverified.

## L. Limitations

Failed one-image synthetic integration attempt, not successful live extraction
or real-world accuracy. Image labels/needle, hashes/challenges/schema do not prove
physical presence, authenticity, calibration, completed repair, industrial safety,
fraud detection or prompt-injection immunity. No production benchmark exists.
Specific API failure cause/status and billing impact unavailable because safe
error mapping did not retain them. More inference needs new explicit authorization;
none is requested or exercised here. Phase 04 remains unauthorized.

## M. Files and Git status

Stage B modifies tracked documentation/evidence only:

- tracking/LIVE_GEMINI_VALIDATION_REPORT.md
- tracking/LIVE_GEMINI_VALIDATION_COMMAND_OUTPUT.txt
- tracking/STATUS_LEDGER.md
- tracking/REQUIREMENT_MATRIX.md
- tracking/EXECUTION_LOG.md
- docs/media_and_gemini.md

Ignored local additions/changes: review in ground_truth.json, new
stage_b_baseline_hashes.local.json and preserved one_live_attempt.local.json under
the sample folder; tracking/LIVE_GEMINI_VALIDATION.local.json. Image/.env unchanged.
No new tracked source, deleted file, staging/commit/push/deploy/remote/Phase 04.
Final actual git status --short --untracked-files=all (six documentation/evidence
files modified, none staged, no new tracked/untracked files or deletions):

~~~text
 M docs/media_and_gemini.md
 M tracking/EXECUTION_LOG.md
 M tracking/LIVE_GEMINI_VALIDATION_COMMAND_OUTPUT.txt
 M tracking/LIVE_GEMINI_VALIDATION_REPORT.md
 M tracking/REQUIREMENT_MATRIX.md
 M tracking/STATUS_LEDGER.md
~~~

git diff --check passed with only existing Windows LF/CRLF notices. Five current
Markdown documents have no missing relative links. No runtime code changed after
the post-request 478-test run. Final checks are in the command evidence.

## N. Recommendation / stop

Preserve the attempt result/reservation. Do not retry, switch models, reset the
marker or call again under the used authorization. Live validation FAILED;
successful interpretation/model availability remain unverified. Before any
separately authorized future request, review request/configuration/API compatibility
and consider retaining safe HTTP status classification without raw secrets.
No diagnostic inference is authorized now. Do not retune policy or synthesize
observations to manufacture a pass. Stop here, before Phase 04.

Rollback (not performed): keep review/result/reservation and runtime data.
Tracked edits are documentation only; review against baseline if needed. Do not
delete the marker, reset Git or discard evidence to repeat an inference.
