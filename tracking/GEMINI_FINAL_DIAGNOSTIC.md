# Final offline Gemini diagnostic — 12 November 2026

## 1. Root cause: UNKNOWN

The original live PROVIDER_UNAVAILABLE cause cannot be recovered from the retained
evidence. Historical result has no HTTP status, error body or observations. It
still records one attempted gemini-3.8-flash send, zero retries and DENY. This
session made **zero actual Gemini requests**, zero list-models/credentialed network
diagnostics, and no web requests. No successful inference is claimed.

One separate, defensible diagnostic defect was reproduced and corrected: the
guarded validation transport discarded failed HTTP status/category. Local
MockTransport returned **canned HTTP 400**; the unchanged adapter emitted
PROVIDER_UNAVAILABLE and the original guard retained empty metadata. This proves
information loss, **not** that the historical live request returned HTTP 400.
Investigation stopped after this focused pass; no speculative request/model/
SDK/configuration change was made.

Initial Git status was clean, HEAD **745a8a7** (user's committed failed live trial).
History was preserved. AGENTS and relevant Master Book perception/trust-boundary
sections were consulted. No commit, push, reset, deployment or paid resources.

## 2. Components and verified findings

| Component | Finding / scope |
|---|---|
| backend/app/gemini_provider.py | Read, unchanged. Public error mapping groups request/not-found/server API failures as PROVIDER_UNAVAILABLE. 401/403 group as PROVIDER_AUTH; timeout/schema failures have separate codes. |
| backend/tools/smoke_gemini.py | Read, unchanged. Explicit dotenv override=false, human review/hash/preflight, existing output and consumed marker checks. Already persists guard transport_metadata, so no runner patch needed. |
| backend/tools/live_validation_guard.py | Only changed runtime file: safe failure status/category capture. Endpoint/counter/SDK factory/request behavior unchanged. |
| backend/app/settings.py / perception.py | Read, unchanged. Existing configured model/attempts/deadline validation and typed observation boundary retained. |
| Installed google-genai / httpx2 | 3.2.0 / 2.16.0, unchanged. SDK serializes the request and handles canned responses locally. No installation, downgrade or experimental version. |
| .env / private image, review, reservation and result | Preserved byte-for-byte. Key presence only inspected; no real credential passed to MockTransport SDK client. |

### Exact serialized request inspection

Used the installed SDK and **existing** adapter/guard with an explicit dummy key,
MockTransport, and the existing safely decoded fictional image. External socket
connects were blocked; Windows asyncio's loopback self-pipe was allowed. The
local request profile was captured before the diagnostic patch.

- POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent.
- Actual API version v1beta; exact configured model gemini-3.8-flash; no fallback.
- Inline normalized PNG: 103828 bytes, SHA-256
  7f45c843b4c5fc018580548f447cfb46251fbc4f9b6d564ea50a5f285a946c23.
- Original image remains SHA-256
  1d5cb9324088ec180cd70725f14ac33157f5a77c7a5935bd7ee85cf4c7c6046f.
- Existing observer system instruction plus fixed extraction instruction; no
  independent expected answers, policy, reviewer credential or permission tool.
- generationConfig temperature=0.0, maxOutputTokens=2048,
  responseMimeType=application/json, responseJsonSchema=VisualObservation schema.
- Eight required observation fields, nullable typed measurements/identifiers/date,
  uncertainty/conflict arrays, additionalProperties=false. No role/approval/tier
  authority property. Numeric/semantic checks remain independent Python validation.
- thinkingConfig serializes include_thoughts=false, thinking_level=LOW; inlineData
  uses mime_type=image/png. These are installed SDK serialization choices; no
  evidence from the unavailable historical response supports changing them.
- Tools omitted from wire payload; function calling and automatic continuation
  remain disabled in the provider configuration. No automatic extra invocation.

[GEMINI_FINAL_REQUEST_SNAPSHOT.json](GEMINI_FINAL_REQUEST_SNAPSHOT.json) preserves
all serialized body fields except base64 image bytes, replaced by length/SHA-256.
It is explicitly OFFLINE_MOCK_TRANSPORT_NO_LIVE_REQUEST with simulated status 400;
the historical HTTP status is UNKNOWN. No headers or credentials are included.
Exact body with fictional base64 pixels remains in ignored
fixtures/live_inputs/gemini_3_8_validation/final_diagnostic_request.local.json.
That private body is not published or committed.

Local serialization/schema success cannot prove server acceptance, account/model
availability or correctness of a live reading. No schema stripping, thinking
tuning, alternate API version/model, policy adjustment or request retry followed.

### Credentials, transport, TLS and exception handling

GEMINI_API_KEY_PRESENT=true. Current supported source is .env (no process key in
the diagnostic child). Settings.from_env reads process variables; runner explicitly
loads its ignored env file with override=false, so existing process values win.
A new dummy-only test verifies both process precedence and file loading when
process key is absent. Presence does not prove key validity or API permissions.
Secret contents were never printed; .env hash is unchanged.

Installed SDK source was inspected: HttpRetryOptions(attempts=1) maps to
tenacity stop_after_attempt(1). The custom transport forces httpx2 instead of
optional aiohttp. Guard uses retries=0, trust_env=false, no redirects/proxies,
fixed HTTPS endpoint and one-send counter; synchronous requests are denied.
Inspected local SSL context has CERT_REQUIRED and check_hostname=true. **No real
TLS handshake/DNS/connectivity was tested**; public certificate trust/account/
network conditions cannot be reconstructed from the old generic code.

Source trace supports only a coarse historical API-error path, not an exact
status/cause: old mapping merges multiple API codes. It is not defensible to
declare bad credentials, unsupported thinking/schema, unavailable model, TLS or
server outage as the historical root cause. Error text is not parsed or logged.

## 3. Small correction and compatibility

Only validation-transport observability changed. Before the SDK converts a failed
response to its existing coarse ProviderError, retain numeric http_status plus a
fixed error_category. No raw message/body/header/URL/credential is copied.

| Failure evidence | Safe category |
|---|---|
| HTTP 400 | REQUEST_ERROR |
| HTTP 401 | AUTHENTICATION_FAILURE |
| HTTP 403 | PERMISSION_FAILURE |
| HTTP 404 | MODEL_OR_ENDPOINT_NOT_FOUND |
| HTTP 408 | REQUEST_TIMEOUT |
| HTTP 429 | RATE_LIMIT |
| HTTP 5xx | SERVER_FAILURE |
| HTTP 3xx | REDIRECT_BLOCKED |
| Other error status | HTTP_ERROR |
| Typed SSL error in bounded cause/context chain | TLS_FAILURE |
| httpx2 timeout | TRANSPORT_TIMEOUT |
| Other httpx2 transport error | TRANSPORT_FAILURE |

404 does not prove which model/endpoint/version is unavailable. TLS classification
uses exception types, not potentially secret messages; chain traversal is bounded
and cycle-safe. Transport exceptions are re-raised; denied state is preserved.
Successful usage capture is unchanged. The existing runner already records this
metadata. Public ProviderError codes remain compatible with every baseline test;
authorization, roles, case versioning, approvals, perception schema, SDK retries,
request destination/body, marker semantics and provider selection are unchanged.

This is a verified **information-loss correction**, not a verified fix for the
unknown historical API rejection. No new request has tested it live.

## 4. Offline verification

Added backend/tests/test_gemini_final_diagnostic.py: 15 offline tests covering
ten HTTP status categories, TLS/connect/timeout fixtures, end-to-end failed runner
metadata/budget preservation, and dotenv precedence using dummy values.
Tests inject local MockTransport and block external sockets. Simulated failures
remain DENY, counted once locally, with no second send or secret marker echo.

Focused actual command:

~~~powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_gemini_final_diagnostic.py backend/tests/test_live_validation.py -x
~~~

Actual output: **39 passed in 1.04s**, exit 0 (15 new + 24 retained guard tests).
No baseline assertion or test file changed.

Baseline snapshot captured before edits includes all 28 old Python test files,
policy/models/manager/API/settings/provider/runner/dependency files, .env, image,
review, consumed marker and prior live result. **43 files verified; mismatches=[]**.
Snapshot itself is ignored final_diagnostic_baseline.local.json. The old result
still reports FAILED, request_count=1/retry_count=0; its marker is unchanged.

## 5. Remaining live requirements and Phase 04 handoff

**Gemini troubleshooting is DEFERRED until Phases 04, 05, 06 and 07 are complete.**
This checkpoint does not implement or authorize Phase 04. Subsequent authorized
development must use explicitly labeled MOCK_AI or SYNTHETIC data where needed.
Normal mock returns UNKNOWN; controlled positive fixtures remain clearly labeled.
Never fabricate LIVE_GEMINI observations or silently substitute mock for live.

After those phases, any separate future live validation would require new explicit
authorization, independently reviewed input, exact model/config, unused authorized
budget and safe status evidence. The old marker is consumed evidence and must not
be reset to reuse it. No diagnostic/inference/network call is currently authorized.
Successful account/model availability, real image interpretation, latency/usage/
cost and remote TLS/network conditions remain unverified. Existing local workflow/
security work does not depend on a claim of successful Gemini inference.

## 6. Full regression results and commands

Executed:

~~~powershell
.\.venv\Scripts\python.exe -m pytest | Tee-Object -FilePath tracking/GEMINI_FINAL_PYTEST_OUTPUT.txt
exit $LASTEXITCODE
~~~

Actual final stdout, exit 0:

~~~text
======================= 493 passed in 76.04s (0:01:16) ========================
~~~

All **478 baseline tests preserved and passed**, plus 15 new = 493. Zero failed.
Full stdout is saved in
[GEMINI_FINAL_PYTEST_OUTPUT.txt](GEMINI_FINAL_PYTEST_OUTPUT.txt). No live calls in
the suite. Only installed Windows Python 3.14.7 executed; no coverage measurement,
Python 3.11/3.12, remote CI, deployment or real-world accuracy claim.

~~~powershell
.\.venv\Scripts\python.exe -m pip check
git diff -- backend/app backend/tools/smoke_gemini.py backend/requirements.txt pyproject.toml
~~~

Actual results: No broken requirements found. (exit 0); empty protected-source/
runner/dependency diff (exit 0). No package installation or pin changes. Secure
post-check reported 43 baseline hashes matched; historical live marker/result
unchanged; current-session real request count zero.

## 7. Files, risks, rollback and final Git status

Modified: backend/tools/live_validation_guard.py; docs/media_and_gemini.md;
tracking/STATUS_LEDGER.md; tracking/REQUIREMENT_MATRIX.md; tracking/EXECUTION_LOG.md.

Added: backend/tests/test_gemini_final_diagnostic.py; this report;
tracking/GEMINI_FINAL_REQUEST_SNAPSHOT.json; tracking/GEMINI_FINAL_PYTEST_OUTPUT.txt.

Ignored local additions only: diagnostic baseline hash manifest and exact body
capture under fixtures/live_inputs/gemini_3_8_validation/. Existing private files,
consumed marker, original result, runtime databases/media and credentials preserved.

Risks: historical root remains unknown; classification is limited to observed
status or typed transport causes, not semantic provider truth. Offline SDK tests
do not prove live compatibility. Generic public API codes remain coarse; safe
extra categories apply to the guarded validation runner only. Local file ACLs/
privileged edits are operator concerns. No schema-valid photograph can establish
authenticity, safety or approval. No permission or policy weakening occurred.

Rollback (not performed): review/revert only this checkpoint's listed code/docs
if requested, preserving private diagnostic and original evidence files. Do not
reset Git history, erase the consumed marker or repeat a live request.

Final actual git status --short --untracked-files=all (five modified, four new;
none staged, no deletions):

~~~text
 M backend/tools/live_validation_guard.py
 M docs/media_and_gemini.md
 M tracking/EXECUTION_LOG.md
 M tracking/REQUIREMENT_MATRIX.md
 M tracking/STATUS_LEDGER.md
?? backend/tests/test_gemini_final_diagnostic.py
?? tracking/GEMINI_FINAL_DIAGNOSTIC.md
?? tracking/GEMINI_FINAL_PYTEST_OUTPUT.txt
?? tracking/GEMINI_FINAL_REQUEST_SNAPSHOT.json
~~~

git diff --check exited 0 with only existing Windows LF/CRLF notices. Five current
Markdown files have no missing relative targets; snapshot JSON is valid. Explicit
git check-ignore confirms credential/consumed marker/private request/baseline/
original result stay ignored. No source changed after the 493-test run. No staging,
commit, push, deployment, remote change or Phase 04 implementation.
