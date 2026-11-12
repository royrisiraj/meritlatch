# Phase 03 local backend gate — 12 November 2026

**Local gate: PASS / TESTED, awaiting user review.** Complete suite: **454 passed,
zero failed**, including all 375 baseline tests and 79 new tests. Real loopback
HTTP completion, unsafe/wrong-asset denials, and rejection/correction/recovery
journeys passed. Stop at Phase 03. **LIVE_GEMINI: BLOCKED - AWAITING AUTHORIZATION**,
tracked separately from local acceptance as required by the current user prompt.

## 1. Implementation and scope

Extended existing user commit `0727e05 feat: addition of evidence processing
pipeline`; initial `git status --short` was empty. `git log -3 --oneline` showed
that commit and `a7e7156`. Did not initialize Git, rebuild the application, restore
deleted handovers, commit, push, reset, connect a remote or deploy.

Read AGENTS, Master Book/relevant extracted sections and original PDF pages
6,7,8,10,11,13,14,20,28, current Phase 03 prompt/contracts, Phase 01/02 reports,
tracking/security catalog, architecture/security/API/media docs and existing
implementation/tests. All requested project documents were available. The supplied
Phase 03 attachment is the current authorization; older phase restrictions remain
historical. No Master Book conflict required weakening its permission model.

| Capability | Status | Executed evidence |
|---|---|---|
| Manager approved job defaults and assignments | IMPLEMENTED AND TESTED | Exact integer amounts, approved template selection, same-tenant assignment; HTTP create and reassign. |
| Manager queue/details/rejection | IMPLEMENTED AND TESTED | Tenant/role/filter/pagination/redaction tests and actual HTTP review/reject. |
| Rejection/correction/resubmission | IMPLEMENTED AND TESTED | Fresh challenge/new bytes, immutable review history, stale approval denials, restart and concurrent tests; HTTP recovery. |
| Upload operation replay and provider recovery | IMPLEMENTED AND TESTED | 21 recovery tests, additional races, pending grace/three-run cap, no extra provider on replay; actual HTTP recovery. |
| L0–L3, independent inspection and business state | IMPLEMENTED AND TESTED | Unchanged pure engine and 375 old tests, new workflow tests, positive and negative HTTP paths. |
| SQLite transactions/migrations/audit | IMPLEMENTED AND TESTED | Legacy approval upgrade, current-version CAS, atomic rejection rollback, append-only histories and scoped audit pagination. |
| Gemini adapter / new live-retry billing guard | IMPLEMENTED BUT NOT VERIFIED | Existing SDK stub tests and new no-network live-mode guard test pass; no actual inference. |
| LIVE_GEMINI interpretation/availability/accuracy | BLOCKED | No separately authorized billable call or consented independently labeled image; readiness check exit 1, network_called=false. |
| Firestore/cloud, production hardening, frontend, Phase 04 | DEFERRED | Not implemented or claimed at this gate. |

## 2. Files added and modified

Added:

- `backend/app/workflow_models.py`
- `backend/app/workflow_service.py`
- `backend/tests/phase03/__init__.py`
- `backend/tests/phase03/conftest.py`
- `backend/tests/phase03/test_workflow.py`
- `backend/tests/phase03/test_queue_and_scope.py`
- `backend/tests/phase03/test_recovery.py`
- `backend/tests/phase03/test_transactions.py`
- `backend/tests/phase03/test_audit_and_persistence.py`
- `backend/tools/smoke_phase03.py`
- `docs/workflow_phase03.md`
- `tracking/PHASE_03_BASELINE_TEST_HASHES.json`
- `tracking/PHASE_03_EXECUTION_EVIDENCE.txt`
- `tracking/PHASE_03_REPORT.md`

Modified:

- `backend/app/api.py`, `api_models.py`, `case_service.py`, `repository.py`,
  `media_service.py`, `media_state.py`
- `README.md`
- `docs/api_phase01.md`, `architecture.md`, `security.md`,
  `media_and_gemini.md`, `decisions.md`
- `tracking/STATUS_LEDGER.md`, `REQUIREMENT_MATRIX.md`, `EXECUTION_LOG.md`,
  `SECURITY_TEST_CATALOG.md`

No existing test file changed. Pre-edit SHA-256 manifest checked all 20 baseline
Python test files after implementation: `mismatches=[]`. `policy.py`, `models.py`,
`perception.py`, `gemini_provider.py`, requirements and pyproject also have empty
Git diffs. No dependency was installed or changed in Phase 03. No private runtime
database/media files are added to Git.

## 3. APIs and compatibility decisions

New protected endpoints:

- GET `/v1/policy-templates` — manager-approved source template list.
- GET `/v1/cases` — manager tenant-scoped bounded verification queue.
- GET `/v1/cases/{case_id}/review` — manager structured evidence/policy/history.
- POST `/v1/cases/{case_id}/rejections` — manager versioned safe enum rejection.
- POST `/v1/cases/{case_id}/evidence/{evidence_id}/reanalysis` — assigned
  contractor's explicit current-evidence recovery.

Extended existing job/case responses/defaults, upload optional `Idempotency-Key`,
idempotent current reapproval and audit filters/cursors. Existing private current
attachment, challenge, invoice/policy selection and action paths remain in use.
No fixture, role provisioning, policy-writing or automatic retry endpoint added.
The factory stays `backend.app.api:create_app --factory`, version 0.3.0; consistent
`/v1/`, no `/api/v1/` alias. Typed public schemas and exact role/request/response/
version/error contracts are in [workflow_phase03.md](../docs/workflow_phase03.md).

Intentional documented audit behavior change: list body retained; newest-first
transaction order, bounded `limit`, scoped public `before_event_id` and
`event_type`; next cursor header when full. Queue is stable creation-time/UUID
keyset order, at most 500 candidates/page. Review history caps 100 with explicit
truncation flag; audit remains pageable. No global event sequence is exposed.

## 4. Business workflow and evidence correction

Manager creates an approved-template job with exact integer paise and same-tenant
assignments, creates a case, and may reassign via existing job-version API.
Contractor issues the challenge in their own authenticated session (issuing it
under a manager session would violate session binding). Actual JPEG/PNG bytes
pass existing safe decoder/private-storage/duplicate controls. Accepted evidence
is PROCESSING_EVIDENCE/L0 until validated provider finalization. Compliant evidence
becomes AWAITING_REVIEW/L2; assigned agent prepares the simulated invoice, manager
approves exact current state, assigned agent completes an idempotent simulation.

Independent case business states: AWAITING_EVIDENCE, PROCESSING_EVIDENCE,
CORRECTION_REQUIRED, AWAITING_REVIEW, REJECTED, APPROVED, COMPLETED. Job ASSIGNED
describes its mandatory assignment; multiple cases have separate lifecycles.
Business state is a projection of authoritative current records, never policy
input. Inspection status and integer permission remain separate. Unsafe evidence
may retain L1 provisional identity only, with SAFETY_ALERT and denied invoice/
completion. Rejected policy-compliant evidence can still say EVIDENCE_COMPLETE
while restricted to L0. State labels cannot authorize an API action.

Manager rejection records a durable safe reason, authenticated reviewer/time,
exact evidence SHA/ID/version, amount/revision, policy, challenge and reviewed/
effective case versions. It clears approval and advances CAS version atomically.
Matching rejected bytes cannot be approved, reanalyzed or un-rejected by invoice/
policy edits. Completed current receipts cannot be rewritten by rejection.
Contractor reloads state, issues fresh challenge and submits corrected new bytes;
new evidence version preserves prior upload/analysis/review records. Only new
eligible evidence can receive a new approval. Historical receipts/rejections are
retained after later cycles. Feedback preserves distinguishable media, provider,
asset/challenge/numeric/unit/safety/expiry/uncertainty/duplicate reason codes.

## 5. Idempotency and explicit provider recovery

Default duplicate behavior is unchanged: same exact bytes in the tenant return
EXACT_DUPLICATE, without calling it fraud. Optional random URL-safe upload key
is persisted only as hash, bound to tenant/actor/auth session/case/original expected
version/challenge/evidence session/bytes/MIME. A matching still-authorized replay
returns current operation outcome and no extra evidence/provider call; pending
returns 202. Changed request/session returns 409; newer evidence supersedes it.
Expired challenges, reassignment and manager rejection still prevent replay.

Recovery endpoint permits at most three explicit runs per evidence for transient
failure/stale results or pending interruption after deadline plus five seconds.
It requires original current challenge/auth session/evidence and same provider
mode, rechecks private-byte digest/decoder, atomically reserves a new case version
and clears approval before provider I/O. Evidence ID/SHA/version stay unchanged;
immutable attempt/result rows distinguish retries. Duplicate recovery keys replay
without inference. Successful insufficient/unsafe output, schema-invalid/blocked
output and rejected evidence require correction. No automatic recovery loop or
live-to-mock fallback. Live retries additionally require per-request billable
consent, atop existing key/config approval guards. Live behavior was stub-tested
only; no billing call was executed.

## 6. Authentication, authorization and concurrency

Existing password/session controls, server roles, tenant/job scope, unpredictably
bound challenges and current-state action checks remain intact. Manager alone
reviews/rejects/approves; contractor cannot self-approve, engineer cannot approve
invoices, service agent cannot create approval. Engineer raw media/observations
remain inaccessible. Manager cannot publish arbitrary policy rules. Provider
modules have no policy/role approval authority and remain byte-for-byte unchanged.

BEGIN IMMEDIATE obtains lock before clock/current-state sampling. Explicit case/
job version checks and approval/review/audit writes share transactions. Original
approval binding remains compatible; every invoice revision advances bound case
version and clears approval, preventing change-away-and-back reuse. Public review
snapshots additionally record explicit invoice revision. Current L3 is recomputed
from exact evidence, policy, amount, reviewer, assignment, challenge/session and
effective case version on every action; no client permission/badge is trusted.

Executed races include both and simultaneous approval/rejection orderings,
rejection during analysis, distinct same-version uploads, concurrent same-key
requests, and reanalysis vs newer evidence/invoice/policy/expiry/reassignment.
Existing upload/approval/replacement, out-of-order analysis, logout and repeated
completion races also pass unchanged. Stale results are only appended/audited,
never current authority. Injected rejection failure rolls back review/case/audit.
SQLite serializes local writers; these are not distributed/load guarantees.

## 7. Audit and persistence

Workflow migration namespace v1 is additive; core/media schema v1 and original
records/approval bindings remain unchanged. Existing timestamps/invoice revision
counts and public legacy approval snapshots are derived from recorded history;
old event business state is LEGACY_RECORDED, never fabricated. Migration is
idempotent and refuses unsupported versions. Restart tests preserve restrictions,
review history and replay keys. Original media/history are not deleted.

New logical histories include job events, manager reviews, workflow event details,
submission operations, recovery runs/results. Repository checks and SQLite
triggers prevent ordinary UPDATE/DELETE. Audit exposes scoped authenticated actor,
tenant/case/job, action/outcome, current versions/policy/time/reasons, source mode/
evidence ID and safe public review/receipt references. Late-result audit identifies
its old source evidence without mislabeling it current. Challenge tokens,
credentials, private paths, raw provider payloads/observations/media and private
approval bindings are excluded. SQLite is not a tamper-proof or immutable ledger.

## 8. Executed verification

Full stdout/stderr and exact commands/chunks are recorded in
[PHASE_03_EXECUTION_EVIDENCE.txt](PHASE_03_EXECUTION_EVIDENCE.txt), linked from
[EXECUTION_LOG.md](EXECUTION_LOG.md). These are executed results, not suggested
commands. Installed runtime: Windows Python 3.14.7, pytest 9.2.0, anyio 4.16.0.

| Actual command | Actual result |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest` before edits | 375 passed in 46.40s; exit 0. |
| `.\.venv\Scripts\python.exe -m compileall -q backend/app` | No output, exit 0. |
| `.\.venv\Scripts\python.exe -m pytest -x` after integration | 375 passed in 47.33s; exit 0. |
| `.\.venv\Scripts\python.exe -m pytest backend/tests/phase03 -x` final focused phase run | 79 passed in 16.84s; exit 0. |
| `.\.venv\Scripts\python.exe -m pytest` final full suite | **454 passed in 67.99s (0:01:07)**; exit 0. |
| `.\.venv\Scripts\python.exe -m pytest backend/tests/phase03/test_transactions.py backend/tests/phase03/test_queue_and_scope.py` | **28 passed in 8.58s**; exit 0. |
| `.\.venv\Scripts\python.exe -m pip check` | `No broken requirements found.`; exit 0. |
| Baseline SHA-256 verification Python command in evidence | `20 baseline test files checked; mismatches=[]`; exit 0. |
| Git diff for pure policy/models/providers/dependency pins/original suites | Empty stdout; exit 0. |
| `git diff --check` | Exit 0, no whitespace errors; Git warns LF will become CRLF under existing Windows Git configuration. |
| `.\.venv\Scripts\python.exe -m backend.tools.smoke_gemini --check` | Exit 1 intentionally BLOCKED; `network_called: false`, LIVE_APPROVAL_AND_FICTIONAL_IMAGE_CONSENT_REQUIRED. |

New test breakdown: workflow 19, queue/scope 16, recovery 21, transactions 12,
audit/persistence 11 = 79. All 375 old tests retained; total 454. No test failures
or xfails in final run; no existing assertion weakened. Intermediate successful
35/53/75-new-test and 450-total runs are also recorded. Coverage was not measured;
no coverage percentage, production load, real-world safety or vision benchmark
is claimed. Live check is an expected blocked dependency, not a pytest failure.

Actual final pytest summary:

```text
======================= 454 passed in 67.99s (0:01:07) ========================
```

## 9. Actual TCP/HTTP smoke

Executed `.\.venv\Scripts\python.exe -m backend.tools.smoke_phase03 --scenario all`
and separately `--scenario complete`, `--scenario unsafe`, `--scenario wrong-asset`.
All exit 0. Uses existing factory/Uvicorn over actual loopback TCP, temporary SQLite/
private files, isolated fictional identities and random ephemeral credentials.
Only provisioning and named mock fixture configuration use Python directly; all
business transitions use authenticated HTTP. No production observation endpoint
or manual database workflow edits exist. Cleanup closes only its own resources.

Provider mode is **MOCK_AI** with explicit fixture label
**CONTROLLED_CANNED_MOCK_AI_NOT_OPTICAL_EXTRACTION**. Normal mock remains UNKNOWN.
Visible JPEG contains fictional input/challenge, but fixture fields are canned;
this does not verify image reading. No secret challenge/password/token is printed.

| Scenario | Observed state/version | Result |
|---|---|---|
| Complete | COMPLETED, case 5, evidence 1, APPROVED_BY_HUMAN, L3 | Manager create/reassign, contractor challenge/image, L0 deny, L2 invoice, queue/review/private image, manager sign-off, same receipt twice, stale VERSION_CONFLICT, scoped audit/tenant checks. |
| Unsafe | CORRECTION_REQUIRED, case 4, evidence 1, SAFETY_ALERT, max L1 | PRESSURE_OUT_OF_RANGE/PERMISSION_INSUFFICIENT; restricted invoice denied, approval 409. |
| Wrong asset | CORRECTION_REQUIRED, case 4, evidence 1, EVIDENCE_MISSING, L0 | ASSET_MISMATCH/PERMISSION_INSUFFICIENT; restricted action denied, approval 409. |
| Recovery rejected | REJECTED, case 5, evidence 1, EVIDENCE_COMPLETE, L0 | MANAGER_REJECTED_EVIDENCE/CORRECTION_REQUESTED; stale approval/execute denied. |
| Recovery completed | COMPLETED, case 11, evidence 2, APPROVED_BY_HUMAN, L3 | Fresh challenge/corrected JPEG; deliberate provider failure remains L0; explicit recovery and replay preserve evidence 2; new sign-off/simulation; rejection history preserved. |

Final line:

```text
PASS Phase 03 actual TCP/HTTP; backend.app.api:create_app; MOCK_AI only; LIVE_GEMINI BLOCKED - AWAITING AUTHORIZATION
```

## 10. Remaining risks and limitations

- LIVE_GEMINI account/model availability, interpretation, accuracy, latency and
  cost are unverified. No approved billable call or consented independently labeled
  image was supplied. Keep live approval/consent guards; do not infer vision success
  from canned mock fields. Adapter/model name unchanged.
- Only installed Windows Python 3.14.7 executed. Intended 3.11/3.12 and remote CI
  remain unverified. Pins unchanged, pip check passes.
- Local development auth lacks production TLS/IdP/MFA/reset, global/IP throttling
  and distributed load validation. Credentials/media/database ACLs are operator
  responsibilities; use fictional data on loopback.
- Challenges, hashes, decoded pixels and schema-valid outputs do not prove media
  authenticity, completed repair or industrial safety. Fictional per-equipment
  policy only; unsafe/unknown states restrict. No fraud-rate or injection-immunity
  claim. A compliant but false observation can still pass deterministic evidence
  eligibility and requires human review.
- Filesystem and DB are not one atomic resource. Crash orphans/pending records
  fail closed; explicit same-session/challenge recovery exists, but automated
  cleanup/retention/deletion/downgrade tooling does not. Expired sessions/challenges
  need fresh evidence. No reanalysis of already interpreted insufficient results.
- Queue scans 500 candidates/page and can return empty filtered continuation pages;
  concurrent pages are not one snapshot. Review history caps 100 with flag, audit
  is paged, old private media remains stored but download is current-only. Existing
  job listing/reassignment paths retain their prior scope/scale limitations.
- SQLite privileged operators can alter history; Firestore/cloud storage adapters,
  distributed transaction guarantees, production load and external retention are
  unimplemented/unverified. No real payment, equipment, notifications, UI or
  Phase 04 release/red-team loop.

## 11. Windows setup and startup (instructions, not claimed executed)

Existing environment:

```powershell
Set-Location D:\project\sentinel_ladder_v2
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase03 --scenario all
.\.venv\Scripts\python.exe -m backend.tools.manage init-demo
.\.venv\Scripts\python.exe -m backend.tools.manage list-users --tenant demo-a
$env:SENTINEL_PROVIDER_MODE = 'DISABLED'
.\.venv\Scripts\python.exe -m uvicorn backend.app.api:create_app --factory --host 127.0.0.1 --port 8000
```

If no environment exists, first run `py -3.12 -m venv .venv`, then
`.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt`.
Installed Python 3.14.7 was used for the actual evidence, not a claimed 3.12 run.
No Docker/WSL. Hidden password provisioning never changes existing accounts or
prints passwords. Swagger: http://127.0.0.1:8000/docs; POST `/v1/auth/login`,
then Swagger Authorize with its bearer token. Stop with Ctrl+C.

For unknown-only non-network image exploration replace DISABLED with MOCK_AI
before server startup. L2 positive fixtures exist only in isolated tests/smoke,
not normal configuration. Default DB is ignored `backend/local.sqlite`, private
media `backend/private_media/`. No key is needed for disabled/mock operation.

From a second PowerShell terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/healthz
```

## 12. Rollback note (not executed)

Stop server and preserve a SQLite backup using SQLite's backup API (include WAL
state correctly), plus matching private media/config and this patch/report. Keep
upgraded database/history **offline**. Restore only reviewed application/docs
files from baseline `0727e05` after explicit user direction; preserve all user
changes. Do not run old Phase 02 business code against Phase 03 data: it does not
know manager rejection/recovery restrictions. Use metadata-only operation or an
isolated new database until a reviewed compatibility plan exists. No automatic
schema downgrade/drop, evidence deletion, git reset/clean, commit or history
rewrite is authorized or performed.

## 13. Final Git evidence

Actual `git status --short --untracked-files=all` (16 modified, 14 new files,
no deletions; all uncommitted):

```text
 M README.md
 M backend/app/api.py
 M backend/app/api_models.py
 M backend/app/case_service.py
 M backend/app/media_service.py
 M backend/app/media_state.py
 M backend/app/repository.py
 M docs/api_phase01.md
 M docs/architecture.md
 M docs/decisions.md
 M docs/media_and_gemini.md
 M docs/security.md
 M tracking/EXECUTION_LOG.md
 M tracking/REQUIREMENT_MATRIX.md
 M tracking/SECURITY_TEST_CATALOG.md
 M tracking/STATUS_LEDGER.md
?? backend/app/workflow_models.py
?? backend/app/workflow_service.py
?? backend/tests/phase03/__init__.py
?? backend/tests/phase03/conftest.py
?? backend/tests/phase03/test_audit_and_persistence.py
?? backend/tests/phase03/test_queue_and_scope.py
?? backend/tests/phase03/test_recovery.py
?? backend/tests/phase03/test_transactions.py
?? backend/tests/phase03/test_workflow.py
?? backend/tools/smoke_phase03.py
?? docs/workflow_phase03.md
?? tracking/PHASE_03_BASELINE_TEST_HASHES.json
?? tracking/PHASE_03_EXECUTION_EVIDENCE.txt
?? tracking/PHASE_03_REPORT.md
```

Documentation check: 12 changed Markdown files, no missing relative link targets.
A final whitespace check found one extra EOF blank line in the newly appended
execution log; it was removed and the check rerun. No runtime/test assertion
changed after the 454-test run. Final check output is in execution evidence.
No Phase 04 work is authorized by this report.
