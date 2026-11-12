# Phase 02 acceptance record — 12 November 2026

**Local tests and MOCK_AI HTTP workflow: PASS. Real Gemini verification: BLOCKED.**
Overall live acceptance remains **BLOCKED**, not declared complete. Stop at this
gate; Phase 03 is not authorized. No billable/model call, cloud resource, real
payment, equipment control, new commit, push, remote creation or deployment occurred.

The user-supplied baseline commit `a7e7156` was verified; commit count remains 1.
The two pre-existing handover Markdown deletions were preserved, not recreated.
The existing factory `backend.app.api:create_app --factory` is extended.

## Implementation

Authenticated raw JPEG/PNG intake verifies current contractor assignment,
tenant/job/asset/case/auth/evidence-session bindings and expected case version.
Actual signatures and full safe decode are checked with byte/pixel/dimension/frame
limits. Server-randomized private filenames, original SHA-256, scoped exact-duplicate
checks, optional untrusted provenance and scoped attachment downloads are implemented.
EXIF/GPS/text metadata is stripped from the normalized RGB PNG sent to a provider;
original and provider-input digests have distinct recorded meanings.

Acceptance appends new evidence and invalidates approval atomically at max 0 /
OBSERVATION_PENDING before inference. Provider work runs outside the DB lock.
Finalization rechecks current case/evidence version, identity, assignment, policy/
invoice revision, active challenge/session and expiry. Stale results cannot grant
authority. Append-only media/analysis records and an additive migration preserve
core version-1 records. The pure authorization engine/models were not changed.

The provider protocol, MockPerceptionProvider and official google-genai adapter
are implemented. No auth tokens, approvals, policy rules or expected answers are
provided to the observer. SDK tools/function calling/continuation/hidden retries
are disabled. Schema plus semantic checks reject invalid numbers, dates,
conflicts and authority-bearing fields. Default mode is DISABLED; modes are
explicit and a live failure never falls back to mock. Model output never grants L3.

## API contract

- `POST /v1/cases/{case_id}/evidence`: raw JPEG/PNG/octet-stream body; assigned
  contractor bearer auth; `X-Expected-Case-Version`, `X-Challenge-ID`,
  `X-Evidence-Session-ID`. Returns current typed observation/state/version and
  provider metadata, without observed token, storage key or path. Provider errors
  return 502/504 with restricted persisted state; obsolete results return scoped
  401/403/404/409 denial. Unconfigured mode returns scoped 404 after authentication.
- `GET /v1/cases/{case_id}/evidence/{evidence_id}/content`: current evidence only;
  assigned contractor or tenant manager; digest-checked attachment, no-store,
  nosniff/CSP. Engineer/agent/public/cross-tenant raw access is denied.
- All existing Phase 01 endpoints/authorization remain. No public observation
  injection, fixture, policy publication, red-team or static-media mount exists.

Defaults: 5 MiB, 4,000,000 pixels, maximum dimension 4096, one frame; JSON routes
stay at 16 KiB. MP4/APNG/video are deferred. Full contracts/configuration/error
semantics: [`docs/media_and_gemini.md`](../docs/media_and_gemini.md).

## Files added and modified

Added:

- `backend/app/gemini_provider.py`, `media.py`, `media_service.py`, `media_state.py`,
  `media_storage.py`, `perception.py`
- `backend/tools/smoke_phase02.py`, `smoke_gemini.py`
- `backend/tests/phase02/__init__.py`, `conftest.py`, `test_analysis_races.py`,
  `test_gemini.py`, `test_media.py`, `test_observations.py`,
  `test_persistence_and_smoke_guards.py`
- `docs/media_and_gemini.md`, `fixtures/live_ground_truth.example.json`
- `tracking/PHASE_02_BASELINE_TEST_HASHES.json`, `tracking/PHASE_02_REPORT.md`

Modified:

- `.env.example`, `.gitignore`, `README.md`, `pyproject.toml`, `backend/requirements.txt`
- `backend/app/api.py`, `case_service.py`, `http_limits.py`, `repository.py`, `settings.py`
- `docs/api_phase01.md`, `architecture.md`, `security.md`, `decisions.md`
- `tracking/STATUS_LEDGER.md`, `REQUIREMENT_MATRIX.md`, `EXECUTION_LOG.md`

All 13 baseline test/conftest files (266 tests) are byte-for-byte unchanged;
SHA-256 verification actually ran. `git diff` for pure `policy.py`/`models.py` was
empty. Existing policies/fixtures and the baseline commit were preserved.
Pre-existing user deletions: `ANTIGRAVITY_WINDOWS_HANDOFF.md`, `CODEX_FIRST_MESSAGE.md`.

## Executed tests and commands

Actual commands/output, failures/recovery and final Git status are appended to
[`EXECUTION_LOG.md`](EXECUTION_LOG.md). Windows/Python 3.14.7 execution only.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Actual final result, process exit 0:

```text
375 passed in 36.74s
```

| Suite | Passed |
|---|---:|
| Unchanged Phase 00/01 tests | 266 |
| Analysis concurrency/stale results | 10 |
| Gemini SDK transport/configuration stubs | 13 |
| Media validation/scope/private storage | 35 |
| Observation semantics/provider failure/authority | 36 |
| Persistence/migration/decoder/live-smoke guards | 15 |
| **Total** | **375** |

Zero final failures/skips/warnings reported. Coverage was not measured. During
development one **new test setup** failed while rendering text after lowering
Pillow's global pixel limit; fixture bytes are now created before lowering the
limit, preserving both decoder rejection assertions. No baseline test was weakened.

Dependency install was initially sandbox-blocked, then completed after approved
network retry. Locked-install verification exited 0; `pip check` returned
`No broken requirements found.` Prior pins remain unchanged. New direct pins:
Pillow 13.0.0, google-genai 3.2.0, python-dotenv 1.2.4, with required transitive
versions pinned. SDK-required httpx2 is installed alongside the original httpx;
Starlette now uses it and the earlier deprecation warning is no longer emitted.
Package metadata permits Python 3.11; actual 3.11/3.12 and remote CI were NOT RUN.

## Actual localhost HTTP smoke — MOCK_AI

```powershell
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase02
```

Exit 0. Actual output:

```text
HTTP health/docs 200; authenticated JPEG POST 200; actual application factory backend.app.api:create_app
{"decision": "ALLOW", "evidence_version": 1, "inspection_status": "EVIDENCE_COMPLETE", "max_permission": 2, "model_id": "mock-observer-v1", "observation": {"artifact_mode": "MOCK_AI", "asset_id_observed": "PUMP-042", "calibration_expiry_date": "2099-12-31", "equipment_status": "RUNNING", "pressure_unit": "PSI", "pressure_value": 35.0, "uncertain_fields": []}, "provider_mode": "MOCK_AI", "reason_codes": ["EVIDENCE_SATISFIES_POLICY"], "version": 4}
L3 DENY without manager approval; contractor approval 403; scoped private read 200; exact duplicate 409
PASS MOCK_AI: real image bytes and HTTP; mock does not measure visual extraction accuracy. No live Gemini call.
```

This uses actual Uvicorn TCP/HTTP through the current factory, actual image
decoding and private temporary SQLite/files. Passwords/tokens are generated
ephemerally and never printed. The image is a generated fictional test card;
observations are canned MOCK_AI, not Gemini or optical extraction. The command
closes its owned listener/database and cleans temporary artifacts.

## Live Gemini evidence — BLOCKED

```powershell
.\.venv\Scripts\python.exe -m backend.tools.smoke_gemini --check
```

Actual tool result was nonzero (reported exit 1), with:

```json
{"status":"BLOCKED","provider_mode":"LIVE_GEMINI","network_called":false,"reason_codes":["LIVE_APPROVAL_AND_FICTIONAL_IMAGE_CONSENT_REQUIRED"]}
```

This preflight does not load credentials or make a network/model call. Its Python
entry function's blocked return 2 is separately tested. No credential was supplied
for an approved run, no billable call was explicitly authorized, and no consented
image with independent human-recorded ground truth was supplied. No live model,
latency, cost or accuracy result exists. **Gemini model actually exercised: none.**
The documentation-verified configurable default is `gemini-3.6-flash`; account
availability remains unverified. Official sources checked 12 November 2026:
[model](https://aistudio.google.com/docs/models/gemini-3.6-flash),
[image input](https://aistudio.google.com/docs/image-understanding),
[structured output](https://aistudio.google.com/docs/structured-output),
[SDK](https://github.com/googleapis/python-genai).

The live runner requires explicit billing/fictional-consent flags, private key,
one attempt, a reviewed ground-truth file and ignored private output. The example
ground truth remains `human_reviewed: false`; it is not evaluation evidence.
The runner records actual fields/comparison/error/elapsed/model if later executed.
Its policy result is an offline fixture comparison, never an API approval or L3.

## Verified security invariants

- Only the authenticated assigned contractor can submit; all role/tenant/job/session checks remain server-side.
- Signatures and decoder format agree; MIME spoofing, malformed/truncated/animated/oversized/bomb images fail closed.
- Original SHA-256 and tenant-scoped uniqueness are enforced without fraud or authenticity claims.
- Private randomized names/paths are not disclosed; scoped current-media reads are digest checked and cross-tenant reads denied.
- EXIF/GPS do not authorize; missing metadata is UNKNOWN and provider metadata is stripped.
- Acceptance atomically advances evidence/case versions and clears old L3 before inference.
- Schema/semantic validation rejects NaN/infinity/negative/numeric strings, invalid dates, unknown authority fields and unchecked model copies.
- Missing/wrong IDs, challenge mismatch, missing measurements, wrong units, uncertainty/conflicts and expired tags remain restricted.
- Unsafe pressure creates SAFETY_ALERT; complete approved observations may earn L2 but never model-derived L3.
- Quota/auth/timeout/unexpected errors remain restricted and do not fall back to mock; error text/keys/payloads are redacted.
- Provider context has no policy, expected answers, role/session secrets or approval capability; SDK tools/automatic calls are disabled.
- Actual concurrent/out-of-order results, logout/expiry/assignment/challenge/invoice/policy changes cannot restore obsolete authority.
- Finalization rollback leaves pending non-authorizing evidence; legacy migration, restart and append-only media history checks pass.
- Existing 266 role/transaction/idempotency/policy tests and 113 original Phase 00 tests are unchanged and passing.

## Remaining risks and limitations

Live extraction/API request acceptance/account availability is unverified; SDK
stubs cannot prove it. Schema-valid but false readings can pass the configured
rules. No general prompt-injection immunity, photo authenticity, physical repair,
industrial safety or model-accuracy claim is supported. The policy bounds remain
fictional, and all completion is simulated.

JPEG/PNG only. No global abuse protection, isolated decoder sandbox, malware
scanning, media retention/recovery/reanalysis endpoint, video, Cloud Storage or
Firestore adapter is implemented. Default byte/pixel limits bound individual
requests, not total multi-client load. Local confidentiality depends on Windows
ACLs; privileged DB/filesystem owners can alter history. File writes and DB are
not crash-atomic together; a crash can leave an orphan file/pending row, which
cannot automatically promote permissions. Exact duplicates can reject legitimate
retries; no perceptual duplicate detector exists. See the media/security docs.

Python 3.11/3.12, remote CI, production load, real-media E2E, cloud and live Gemini
are NOT RUN. No frontend, red-team generator, notification or Phase 03 was built.

## Rollback (documented, not executed)

Stop the server, preserve/back up SQLite and private media, then review/restore
only Phase 02 code/config changes from the baseline. Keep additive media tables
and raw evidence preserved rather than automatically dropping/deleting them.
Old code treats new provider evidence as ineligible; no automatic schema downgrade
is supplied. Do not reset/remove the user's commit or restore their intentionally
deleted handover files. No destructive repository operation was executed.

## Exact Windows PowerShell reproduction

```powershell
Set-Location D:\project\sentinel_ladder_v2
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase02
.\.venv\Scripts\python.exe -m backend.tools.smoke_gemini --check
```

For manual local exploration (default mock returns UNKNOWN, no fabricated L2):

```powershell
.\.venv\Scripts\python.exe -m backend.tools.manage init-demo
$env:SENTINEL_PROVIDER_MODE = 'MOCK_AI'
.\.venv\Scripts\python.exe -m uvicorn backend.app.api:create_app --factory --host 127.0.0.1 --port 8000
```

Hidden provisioning prompts create independent accounts. No key is needed for
mock mode. Live reproduction is documented separately and must not run without
explicit approval, private configuration and reviewed fictional inputs.

Final Git status follows after all report artifacts are written. Gate remains
BLOCKED for live verification; local implementation/tests are verified. Stop here.


## Final Git status — Phase 02

```powershell
git status --short --branch --untracked-files=all
```

Exit 0:

```text
## master
 M .env.example
 M .gitignore
 D ANTIGRAVITY_WINDOWS_HANDOFF.md
 D CODEX_FIRST_MESSAGE.md
 M README.md
 M backend/app/api.py
 M backend/app/case_service.py
 M backend/app/http_limits.py
 M backend/app/repository.py
 M backend/app/settings.py
 M backend/requirements.txt
 M docs/api_phase01.md
 M docs/architecture.md
 M docs/decisions.md
 M docs/security.md
 M pyproject.toml
 M tracking/EXECUTION_LOG.md
 M tracking/REQUIREMENT_MATRIX.md
 M tracking/STATUS_LEDGER.md
?? backend/app/gemini_provider.py
?? backend/app/media.py
?? backend/app/media_service.py
?? backend/app/media_state.py
?? backend/app/media_storage.py
?? backend/app/perception.py
?? backend/tests/phase02/__init__.py
?? backend/tests/phase02/conftest.py
?? backend/tests/phase02/test_analysis_races.py
?? backend/tests/phase02/test_gemini.py
?? backend/tests/phase02/test_media.py
?? backend/tests/phase02/test_observations.py
?? backend/tests/phase02/test_persistence_and_smoke_guards.py
?? backend/tools/smoke_gemini.py
?? backend/tools/smoke_phase02.py
?? docs/media_and_gemini.md
?? fixtures/live_ground_truth.example.json
?? tracking/PHASE_02_BASELINE_TEST_HASHES.json
?? tracking/PHASE_02_REPORT.md
```

The two handover deletions predated Phase 02 and were left unchanged. Existing commit `a7e7156` remains the only commit; no files were staged or committed. `git remote` returned no names. No remote, push, deployment, paid resource or Phase 03 work was performed.
