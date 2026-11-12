# Phase 01 acceptance record — 12 November 2026

**Local gate: PASS. Phase 02 awaits user approval.**

Final full-suite command: `.\.venv\Scripts\python.exe -m pytest`.
Actual final summary: **266 passed, 1 warning in 22.24s**; process exit 0.
Zero failed/skipped/blocked tests. This includes all **113 original tests** plus
**153 new Phase 01 tests**. Original test/conftest file SHA-256 values were captured
before editing and verified unchanged; see `PHASE_01_BASELINE_TEST_HASHES.json`.
Coverage was not measured. Windows/Python 3.14.7 only; 3.11/3.12 and CI NOT RUN.

Branch `master`, no commits. All original files were already untracked. No staging,
commit, push, remote configuration, deployment, paid resources or Phase 02 work.

## Implemented behavior

Four independently identifiable backend roles; salted password hashes and opaque
hashed bearer sessions; current DB role/tenant/assignment checks; logout/expiry;
persistent login limits; same-tenant job creation and versioned reassignment;
SQLite job/case/policy/evidence/challenge/approval/action/event persistence through
SQLAlchemy; initial schema migration and adapter protocols.

Server-created unpredictable challenges bind tenant/job/asset/case/auth/evidence
sessions and expiry. Internal-only SYNTHETIC observations exercise L0/L1/L2 while
the pure policy remains unchanged. Manager sign-off binds the full reviewed state;
only the assigned service agent can execute simulated completion. Evidence,
amount, policy, assignment, challenge, session or reviewer invalidity prevents
stale L3. Transactions and CAS protect concurrent writes. Receipts are idempotent.

Additional policy versions use trusted offline two-engineer registration and a
structural regression guard; registration does not activate. Engineer HTTP scope
permits selection only of already reviewed versions, never publication or rule
editing. This is not a completed Phase 04 release/adversarial system.

Audit is append-only logical history with ordinary UPDATE/DELETE protection,
scoped/redacted reads and no immutable-ledger claim. Validation/error responses
omit payloads/credentials; bounded JSON intake includes chunked requests.

## Endpoints

Full role map, JSON examples, errors and concurrency semantics:
[`docs/api_phase01.md`](../docs/api_phase01.md).

```text
GET   /healthz
GET   /docs, /openapi.json                  (public documentation)
POST  /v1/auth/login
POST  /v1/auth/logout
GET   /v1/me
POST  /v1/jobs
GET   /v1/jobs
GET   /v1/jobs/{job_id}
PATCH /v1/jobs/{job_id}/assignment
POST  /v1/jobs/{job_id}/challenges
POST  /v1/cases
GET   /v1/cases/{case_id}
PATCH /v1/cases/{case_id}/invoice
PATCH /v1/cases/{case_id}/policy
POST  /v1/cases/{case_id}/actions/evaluate
POST  /v1/cases/{case_id}/actions/execute
POST  /v1/cases/{case_id}/approvals
GET   /v1/cases/{case_id}/audit
```

There is no synthetic/upload, role-provisioning, red-team or policy-publishing
HTTP endpoint. All business routes require bearer auth; only health/docs/schema,
Swagger's redirect helper and login are public. URLs consistently use `/v1`.

## Files

Created:

- `backend/app/api.py`, `api_models.py`, `auth.py`, `case_service.py`, `errors.py`,
  `http_limits.py`, `provisioning.py`, `repository.py`, `settings.py`
- `backend/testing.py`
- `backend/tools/__init__.py`, `manage.py`, `smoke_phase01.py`
- `backend/tests/phase01/conftest.py`, `test_challenges.py`, `test_http_boundary.py`,
  `test_identity.py`, `test_persistence.py`, `test_scope.py`, `test_transactions.py`,
  `test_workflow.py`
- `docs/api_phase01.md`
- `tracking/PHASE_01_BASELINE_TEST_HASHES.json`, `tracking/PHASE_01_REPORT.md`

Modified: `.env.example`, `.gitignore`, `README.md`, `backend/requirements.txt`,
`pyproject.toml`, `docs/architecture.md`, `docs/security.md`, `docs/decisions.md`,
`tracking/STATUS_LEDGER.md`, `tracking/REQUIREMENT_MATRIX.md`, `tracking/EXECUTION_LOG.md`.
The sole dependency addition is SQLAlchemy==2.1.8; prior pins are preserved.
Original tests, pure policy/models, legacy health app, Master Book, contracts,
fixture/policy baseline and phase prompts were not modified.

The unchanged Phase 00 `main.app` remains metadata-only because its accepted tests
explicitly require absent business routes. The actual Phase 01 startup is
`backend.app.api:create_app --factory`; its business endpoints are independently
tested. This composition decision is explicit in `docs/decisions.md`.

## Executed verification

`tracking/EXECUTION_LOG.md` retains Phase 00 evidence and appends exact Phase 01
commands and outputs, including failed attempts, recovery and final Git status.

| Suite | Passed |
|---|---:|
| Original Phase 00 | 113 |
| Challenges | 13 |
| HTTP/schema/input boundary | 10 |
| Identity/session/password/throttling | 30 |
| Persistence/migration/history | 18 |
| Role/tenant/job scope | 25 |
| Transactions/concurrency/rollback/lock clock | 9 |
| Case workflow/binding/invalidation | 48 |
| **Total** | **266** |

During development a new post-lock clock regression failed (265 passed, 1 failed)
because action execution still sampled time before acquiring the lock. The clock
read was moved into the transaction; the test was retained. Later full runs
passed all 266. No original test was weakened. The existing Starlette HTTPX
TestClient deprecation warning remains visible. `pip check` exited 0 with
`No broken requirements found.` The pinned installation check exited 0.

Actual TCP smoke command:

```powershell
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase01
```

Exit 0, actual output:

```text
HTTP health/docs: 200 / 200
Authenticated four independent roles; anonymous jobs request: 401
Missing evidence: L0; prepare_invoice DENY
Internal SYNTHETIC observation: L2; unapproved completion DENY
Contractor self-approval / engineer approval: 403 / 403
Manager review: L3; repeated simulated completion: one receipt
Changed invoice: approval invalidated; completion DENY
Redacted audit verified; logout revocation: 401
PASS: actual localhost HTTP workflow, SYNTHETIC only; no Gemini, money movement or cloud
```

The smoke uses a real Uvicorn loopback listener and HTTP client with ephemeral
credentials and temporary SQLite. Only its evidence injection uses the internal
test factory; it is not an HTTP capability. It cleans up its own server and DB.
Application restart/persistence and both-tenant scope checks ran in automated
tests. No persistent demo accounts were provisioned in the normal default DB.

## Security invariants verified

- Contractor self-approval, engineer/agent approval and wrong-role business actions denied.
- Contractor unassigned-job access and service-agent unassigned action denied.
- Tenant B cannot read/write/evaluate Tenant A cases, jobs or audit.
- No client role header, cookie, permission/approval field or invented token grants authority.
- Missing evidence remains L0; partial valid evidence L1; complete synthetic evidence L2.
- Unsafe numbers/tags produce SAFETY_ALERT without L2/L3; wrong units/IDs/uncertainty restrict.
- L3 needs independent manager sign-off of current evidence/policy/amount; only assigned agent executes.
- Full approval binding includes authenticated reviewer and required case/evidence/amount/policy scope.
- Evidence, invoice, policy, challenge rotation, assignment, expiry, logout and reviewer invalidity prevent stale L3.
- Stale expected versions and resurrected obsolete pointers cannot restore authority.
- Approval vs replacement, approval vs approval, concurrent completion and completion vs replacement use actual SQLite transactions.
- Injected mid-transaction failure leaves no partial case/approval/audit write.
- Clock sampling after lock wait prevents expired challenge use; invalidation commits on conflict denial.
- Repeated/concurrent completion yields one binding-specific receipt; restart preserves idempotency.
- Model-shaped authority fields are rejected before persistence; no model tools, credentials or policy-edit route exist.
- Synthetic injection is internal/test-only; normal operation refuses saved test artifacts too.
- Scoped audit omits tokens/raw observations; append-only history constraints and redacted failures verified.

## Risks, scope and rollback

High: no real media verification, private media storage, duplicate lookup, live
Gemini, retention workflow or physical truth guarantee. Normal Phase 01 operation
has no evidence upload; L2/L3 demonstrations require the explicit test factory.
The fictional pump range is not safety guidance. No actual payment or equipment
action exists. No frontend was built.

Local auth lacks production TLS/MFA/external identity/password reset/global abuse
controls. Account-specific throttling can be abused for denial of login. SQLite
serializes writes; production load and Firestore semantics are unverified. The
database owner can alter history despite application triggers. Only initial
migration version 1 is implemented; future migrations need backup planning.
Python 3.11/3.12, remote CI, live AI, media E2E and cloud are NOT RUN.

Rollback is documented, not executed: stop the server cleanly, preserve/back up
SQLite using its backup API, retain all original files and credentials, restore
Phase 00 docs/dependencies from a saved copy, and use the unchanged metadata-only
entry point if reverting. Review/remove only the new Phase 01 files if requested.
There is no automatic schema downgrade or baseline Git commit; do not use
destructive Git cleanup or delete the DB.

Requirement matrix: local R-002/003/004/005/009/011 now TESTED; broader audit,
privacy, UI, media, provider, cloud and assurance scope remains IN_PROGRESS or
PLANNED. Ledger and matrix link actual test evidence, not speculative completion.

## Exact Windows startup

```powershell
Set-Location D:\project\sentinel_ladder_v2
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m backend.tools.manage init-demo
.\.venv\Scripts\python.exe -m backend.tools.manage list-users --tenant demo-a
.\.venv\Scripts\python.exe -m uvicorn backend.app.api:create_app --factory --host 127.0.0.1 --port 8000
```

Provisioning prompts for hidden independent passwords; none are in source or
command arguments. Startup commands above are reproduction instructions; the
executed smoke used temporary automatically generated test accounts. See the
execution log for the actual commands that ran. Stop here; Phase 02 is not authorized.
