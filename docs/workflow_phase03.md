# Phase 03 backend workflow contract

Use `backend.app.api:create_app --factory`. All business endpoints use `/v1/`;
there is no `/api/v1/` alias. This extends the Phase 01 and Phase 02 contracts.
The pure policy, provider interface and original 375 tests are unchanged.
Execution evidence: [Phase 03 report](../tracking/PHASE_03_REPORT.md).

Every operation below requires `Authorization: Bearer <opaque token>`. Server
records determine role, tenant and assignment. Wrong tenant/unassigned IDs return
scoped 404; wrong role 403; absent/expired session 401. Public health/docs/schema
and login are the existing exceptions. No new observation-injection route exists.

## Endpoints and schemas

| Method/path | Caller and request | Response / checks |
|---|---|---|
| GET `/v1/policy-templates` | MANAGER, no body | `PolicyTemplate[]`: approved source template ID/version, classification, unit/bounds/inclusivity/status. No policy publishing. |
| POST `/v1/jobs` | MANAGER; existing asset/contractor/engineer/service-agent IDs, optional `policy_id`, `policy_version`, `invoice_amount_paise` | 201 job, defaults, version, creation time, `business_status: ASSIGNED`, last 20 job events. Every assignment must be active and same tenant. Only an approved template can be selected. |
| GET `/v1/jobs`, `/v1/jobs/{job_id}` | Existing manager/assigned contractor/assigned engineer | Extended job view above; legacy records have null creation time if not recorded. No invented creation events. |
| PATCH `/v1/jobs/{job_id}/assignment` | MANAGER; `expected_job_version`, same-tenant `contractor_id` | Job version advances; all job cases lose current evidence/challenge/approval, preserving history. Job event recorded atomically. |
| POST `/v1/cases` | MANAGER; `job_id`, optional `invoice_amount_paise` and approved per-job `policy_version` | 201 current case. Omitted amount/version inherit job defaults. Only managers set amounts; contractors cannot override asset or policy through evidence. |
| GET `/v1/cases` | MANAGER; filters below | Typed `VerificationQueue`: `items: CaseSummary[]`, `next_cursor`, `scanned`, `snapshot_at`. Current stored state/time evaluated for eligibility. |
| GET `/v1/cases/{case_id}` | Existing scoped manager/contractor/engineer | Existing case view plus business/review/processing status, version, invoice revision, evidence ID, timestamps, reason codes, missing/uncertain fields, role-aware `available_actions`, public last review. Engineer observations/media remain redacted. |
| GET `/v1/cases/{case_id}/review` | MANAGER | Typed `ReviewDetails`: `case: CaseSummary`, redacted structured `observation`, `missing_fields`, `uncertain_fields`, exact `policy_constraints`, media metadata, current authorized attachment URL, last 100 public `ReviewRecord`s, `history_truncated`. |
| POST `/v1/cases/{case_id}/rejections` | MANAGER; `expected_case_version`, `reason` enum below | Typed current case; atomically records immutable review snapshot, clears approval and advances version. Evidence required; completed receipt cannot be rewritten. |
| POST `/v1/cases/{case_id}/evidence` | Assigned CONTRACTOR; raw JPEG/PNG and existing binding headers, optional `Idempotency-Key` | Existing actual-byte intake. New bytes advance evidence and case versions; result finalization advances case version again. Optional key safely replays the same operation, never creates another version/provider call. |
| POST `/v1/cases/{case_id}/evidence/{evidence_id}/reanalysis` | Assigned CONTRACTOR; `expected_case_version`, `idempotency_key`, optional strict bool `allow_billable: false` | Current case with new attempt outcome. Only recoverable failed/stale or interrupted pending analysis; same evidence bytes/version. Live retry additionally requires per-request `allow_billable: true` and existing configured billing gates. No live request was executed. |
| POST `/v1/cases/{case_id}/approvals` | Existing independent MANAGER; `expected_case_version` | Current eligible L2 required; records public review snapshot plus original private approval atomically. Repeating at current version with valid approval returns `already_approved: true`, no new approval/version. |
| POST `/v1/cases/{case_id}/actions/evaluate`, `/actions/execute` | Existing action-specific role; `expected_case_version`, `action` | Reload/evaluate latest persisted state. Assigned SERVICE_AGENT prepares invoice at L2 and completes simulation at L3; repeat current completion returns original receipt. |
| GET `/v1/cases/{case_id}/audit` | Existing scoped MANAGER/CONTRACTOR/ENGINEER; optional `limit` 1..100, `before_event_id`, `event_type` | Existing list body extended with job/business/source/public review/receipt references, **newest first** by transaction event sequence. Header `X-Audit-Next-Cursor` provides last public event UUID when page is full. Final page may require one empty fetch. No global sequence or approval secret exposed. |

`JobCreate` exact amounts are positive strict integer paise, max 100000000:
INR 5,000 is `500000`. Floats, booleans, raw policy rules, client statuses and
authority fields are rejected with 422. Optional fields preserve old callers.
Existing invoice/policy/challenge/private-content contracts are retained.

Queue parameters: `limit` 1..100 (default 25), public case UUID `cursor`,
`business_status`, `inspection_status`, `approval_eligible`, `contractor_id`,
`attention_only` (default true). Default attention states are AWAITING_REVIEW,
CORRECTION_REQUIRED and REJECTED. Set `attention_only=false` for all states.
Ordering is `(created_at, case UUID)` ascending; legacy unknown times sort first.
Each request scans at most 500 scoped candidates using a SQL limit of 501, and
returns a continuation even when sparse filters yield an empty page. Continue
while `next_cursor` is non-null. Cursors must belong to the authenticated tenant.
This is keyset traversal, not a cross-request database snapshot: eligibility can
change between pages. Approval always rechecks current state independently.

`CaseSummary` includes IDs/assignment/asset, case/evidence/policy/invoice versions,
amount, creation/submission time, processing/provider/model labels, inspection
status, permission, reason codes, business/review state, approval eligibility and
role-aware next actions. A badge/action list is informational, never authority.
`ReviewRecord` includes public ID, APPROVED/REJECTED, reviewer/time, reviewed and
effective case versions, exact evidence ID/version/SHA-256, policy version,
amount/revision and safe reason. Internal approval IDs/bindings/challenge tokens
and storage paths are omitted. Challenge text is removed from observations.

## Independent states and transitions

| Business state | Current-state condition / transition |
|---|---|
| AWAITING_EVIDENCE | Case created, or fresh challenge/assignment clears current evidence. |
| PROCESSING_EVIDENCE | Accepted upload or reserved recovery run without final analysis; L0. |
| CORRECTION_REQUIRED | Failed/stale, insufficient, mismatched, expired or unsafe evidence; no invoice/completion authority. |
| AWAITING_REVIEW | Current evidence satisfies policy at L2; prepare invoice, require independent manager approval. |
| REJECTED | Manager rejection matches current evidence digest; L0 even if numeric inspection remains EVIDENCE_COMPLETE. |
| APPROVED | Exact current valid approval plus current compliant L2; L3 simulation only. |
| COMPLETED | Valid current approval binding has an idempotent simulated receipt. Later evidence/amount/policy/expiry changes remove current authority; historical receipt remains. |

Jobs start with a mandatory contractor assignment and report ASSIGNED; multiple
cases have independent business lifecycles. Job status does not aggregate or
authorize completion. Inspection statuses remain EVIDENCE_MISSING,
OBSERVATION_PENDING, EVIDENCE_COMPLETE, SAFETY_ALERT, REVIEW_REQUIRED and
APPROVED_BY_HUMAN. Permissions retain exact L0 draft/request, L1 provisional
visit, L2 invoice preparation, L3 simulated completion semantics. Safety/uncertainty
cannot elevate permission. Contractor cannot approve or execute manager/agent
actions; engineer cannot approve; manager cannot write policies.

## Rejection and corrected evidence

Example request:

```json
{"expected_case_version":4,"reason":"CORRECTION_REQUESTED"}
```

Reasons are INCORRECT_ASSET, INCOMPLETE_EVIDENCE, UNSUPPORTED_UNIT, SAFETY_REVIEW,
EXPIRED_TAG, UNCERTAIN_OBSERVATION, CORRECTION_REQUESTED. No arbitrary customer
notes/raw payload are accepted. Rejection stores authenticated reviewer and the
exact evidence/amount/revision/policy/case/challenge snapshot, invalidates prior
approval, and caps matching current evidence at L0 without falsifying inspection
status. Same-byte evidence remains rejected even across invoice/policy changes.

Correction: reload case; assigned contractor requests a **fresh challenge** in
their own active auth session; capture/submit corrected new bytes with the new
challenge and returned case version. Existing duplicate detection still applies.
New evidence increments evidence version; previous upload/analysis/rejection
remain. Fresh compliant evidence can reach L2 and receive a new independent
review. Manager rejection cannot be undone by same-byte retry or reanalysis.

## Upload idempotency and provider recovery

An optional upload `Idempotency-Key` is 16..128 URL-safe characters. Persist only
its SHA-256, uniquely scoped to tenant+actor. Binding includes auth session, case,
original expected version, challenge, evidence session, original-byte SHA-256
and declared MIME. Reuse exactly that request/header binding after a lost HTTP
response. Recheck session/assignment/current challenge on every replay. Returns
`operation_replayed: true`, current outcome (200 success, 202 pending, 502 failure
or 504 timeout), and no extra evidence/provider request. Newer evidence causes
409 OPERATION_SUPERSEDED; altered request/session causes IDEMPOTENCY_CONFLICT.
Without a key, byte-identical uploads retain 409 EXACT_DUPLICATE. Duplicate bytes
alone do not establish fraud. Rejection/expired challenge still block replay.

Explicit recovery request:

```json
{"expected_case_version":4,"idempotency_key":"fresh_random_operation_key","allow_billable":false}
```

Recover only original current evidence in the original live contractor session,
with original active challenge and same provider mode. SUCCESS (even insufficient
or unsafe), PROVIDER_INVALID_OBSERVATION, PROVIDER_BLOCKED or manager-rejected
evidence requires correction, not repeated inference. A pending run must exceed
its configured deadline plus five-second grace. At most three explicit recovery
runs per evidence, persisted across restarts. Recheck stored-byte digest and safe
decode, reserve new case version/clear approval before I/O, append immutable run
and result. Evidence ID/SHA/version stay unchanged. Each result rechecks current
case/evidence/identity/assignment/challenge after I/O; obsolete results are only
audited, never promoted. Repeat key replays same current attempt; no implicit
background retry, live-to-mock fallback or queue worker exists.

Stable errors include CHALLENGE_INVALID, FRESH_CHALLENGE_REQUIRED,
EVIDENCE_REQUIRED, EVIDENCE_ALREADY_REJECTED, SIMULATION_ALREADY_COMPLETED,
NEW_EVIDENCE_REQUIRED, PROVIDER_MODE_MISMATCH, IDEMPOTENCY_CONFLICT,
OPERATION_SUPERSEDED, ANALYSIS_IN_PROGRESS, BILLABLE_REANALYSIS_NOT_APPROVED,
MEDIA_INTEGRITY_ERROR, REANALYSIS_LIMIT and existing VERSION_CONFLICT/L2_REQUIRED.
Media/observation failures retain distinct existing decoder and policy codes
(asset/challenge mismatch, missing reading, wrong unit, unsafe pressure, expired
tag, uncertainty/conflicts, malformed media, duplicate, timeout/quota/auth/schema).
Responses contain `decision`, `reason_codes`, actionable `guidance`; final failed
analysis also returns the restricted case. Reload state on conflicts; correct
evidence on policy/inspection failures; request explicit recovery only when
`request_reanalysis` is offered and authorized. Never automatically retry a live
request. Exceptions omit SQL/provider messages and secrets.

## Transactions, history and migration

Existing SQLite BEGIN IMMEDIATE and explicit CAS remain the authority boundary.
Sample clock after lock, authorize before writes. Rejection, approval, invoice
revision and audit changes commit together. Original approval binding remains
compatible: invoice revision advances case version and clears approval atomically;
case-version binding prevents change-away-and-back reuse. Public review snapshots
also record explicit invoice revision. No new approval credential is exposed.

Additive workflow migration namespace v1 preserves core/media v1 and every old
record. Case metadata derives known timestamps/revision counts from existing
audit; legacy approvals get public review snapshots without changing binding.
Old audit details are explicitly LEGACY_RECORDED, not invented historical states.
New logical workflow/job/review/operation/run/result histories reject ordinary
UPDATE/DELETE via repository and SQLite triggers. A privileged DB owner can
alter data; this is not a tamper-proof database. Private old media is preserved;
HTTP attachment download intentionally remains current-only. Review history caps
at 100 with a truncation flag; audit is paged. Back up before migration; no
automatic downgrade, retention/delete or orphan-file repair tool is provided.

## Windows execution

From an existing environment (no Docker, WSL, cloud or key required):

```powershell
Set-Location D:\project\sentinel_ladder_v2
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase03 --scenario all
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase03 --scenario complete
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase03 --scenario unsafe
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase03 --scenario wrong-asset
```

For first setup: `py -3.12 -m venv .venv`, then
`.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt`.
Python 3.11/3.12 are intended targets; only installed Windows Python 3.14.7 was
executed here. Exact local verification commands/results are in the execution log.

Interactive backend with default DISABLED provider:

```powershell
.\.venv\Scripts\python.exe -m backend.tools.manage init-demo
.\.venv\Scripts\python.exe -m backend.tools.manage list-users --tenant demo-a
$env:SENTINEL_PROVIDER_MODE = 'DISABLED'
.\.venv\Scripts\python.exe -m uvicorn backend.app.api:create_app --factory --host 127.0.0.1 --port 8000
```

Provisioning prompts for independent hidden passwords; startup never seeds
accounts. Use Swagger at http://127.0.0.1:8000/docs to log in/authorize. For actual
image intake without network, set `$env:SENTINEL_PROVIDER_MODE = 'MOCK_AI'` before
startup; its normal observer returns UNKNOWN and cannot demonstrate optical
extraction. Only the isolated smoke/test factory injects labeled canned fields.
It creates temporary data, starts a real TCP listener and uses HTTP for all
business transitions, then cleans up only its own temporary resources.

LIVE_GEMINI is **BLOCKED - AWAITING AUTHORIZATION**. Neither mocked success nor
this phase authorizes a billable call or proves visual accuracy. No frontend,
Phase 04, deployment, real payment or equipment control is implemented here.
