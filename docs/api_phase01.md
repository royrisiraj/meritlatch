# Phase 01 API contract

Historical Phase 01 endpoint baseline. Phase 02 adds authenticated image upload
and scoped private-content retrieval; current contracts are in
[`media_and_gemini.md`](media_and_gemini.md). Existing endpoints retain their roles.

Run `backend.app.api:create_app --factory`. All business paths use `/v1/...`;
there is no `/api/v1` alias. Use `Authorization: Bearer <opaque token>`.
Health/docs/schema are public. No fixture/upload, account/role provisioning,
policy publishing or red-team HTTP route exists.

| Method | Path | Caller / behavior |
|---|---|---|
| GET | `/healthz` | Public operational metadata |
| GET | `/docs`, `/openapi.json` | Public docs; Swagger redirect helper also public |
| POST | `/v1/auth/login` | Tenant, username, password; expiring opaque token |
| POST | `/v1/auth/logout` | Authenticated role; revokes this session |
| GET | `/v1/me` | Current server-side identity |
| POST | `/v1/jobs` | Manager; asset and same-tenant role assignments |
| GET | `/v1/jobs` | Manager tenant-wide; assigned contractor/engineer; agents denied |
| GET | `/v1/jobs/{job_id}` | Same tenant and role/assignment scope |
| PATCH | `/v1/jobs/{job_id}/assignment` | Manager; versioned contractor reassignment; clears case evidence/challenges/approvals |
| POST | `/v1/jobs/{job_id}/challenges` | Assigned contractor; case and expected version; server creates token |
| POST | `/v1/cases` | Manager; job and integer invoice amount |
| GET | `/v1/cases/{case_id}` | Scoped contractor/manager/engineer; current computed state |
| PATCH | `/v1/cases/{case_id}/invoice` | Manager; amount and expected case version |
| PATCH | `/v1/cases/{case_id}/policy` | Assigned engineer; registered reviewed version and expected case version |
| POST | `/v1/cases/{case_id}/actions/evaluate` | Actor/action/assignment and latest persisted-state checks |
| POST | `/v1/cases/{case_id}/actions/execute` | Same checks plus persistent idempotent simulated receipt |
| POST | `/v1/cases/{case_id}/approvals` | Independent manager; current L2 required; expected version |
| GET | `/v1/cases/{case_id}/audit` | Scoped contractor/manager/engineer; last 100 redacted logical events |

Names retain the Phase 00 enum: `create_draft`, `request_evidence`,
`record_provisional_visit`, `prepare_invoice`, `complete_simulated_action`.
Contractors/managers/agents can draft/request evidence; contractors and agents
record provisional visits; only assigned agents prepare invoices or execute
completion. Managers sign off through approvals. Engineers never approve business
completion. Execution records a simulated local receipt, without external tickets,
notifications, payments or equipment operations.

Create a job as manager using IDs from the offline provisioning CLI:

```json
{"asset_id":"PUMP-042","contractor_id":"<id>","engineer_id":"<id>","service_agent_id":"<id>"}
```

Create a case as manager (INR 5,000 = 500000 paise):

```json
{"job_id":"<job-id>","invoice_amount_paise":500000}
```

It starts at L0. The contractor requests a challenge in their own authenticated
session; case creation does not issue a manager-session challenge for a contractor:

```json
{"case_id":"<case-id>","expected_case_version":1}
```

The response has the server token, scope, evidence session, expiry and new version.
Genuine media intake awaits Phase 02. Tests/smoke use a visibly SYNTHETIC internal
factory, never a route.

Evaluate or execute an action as assigned agent:

```json
{"expected_case_version":3,"action":"prepare_invoice"}
```

Review current complete evidence, then sign off as manager:

```json
{"expected_case_version":3}
```

Approval advances the case version. Use its returned version for completion.
Repeated completion against the same current binding returns the same receipt
with `already_executed: true`. No monetary side effect exists.

Change invoice as manager:

```json
{"expected_case_version":4,"invoice_amount_paise":500001}
```

Select an already reviewed registered version as assigned engineer:

```json
{"expected_case_version":5,"policy_version":"1.0.1"}
```

These version numbers are illustrative; always use the latest returned version.
The policy route cannot accept JSON rule changes. Offline registration requires
independent engineer credentials, review reference and structural regression.

Evidence/invoice/policy changes invalidate approval. Rotation/reassignment also
require new evidence. Time, session and reviewer identity are rechecked against
the server clock inside the transaction.

Failures include `401 AUTHENTICATION_REQUIRED/INVALID_CREDENTIALS`,
`403 ROLE_FORBIDDEN/INDEPENDENT_REVIEW_REQUIRED`, scoped `404 NOT_FOUND`,
`409 VERSION_CONFLICT/L2_REQUIRED/CHALLENGE_INVALID/DATABASE_CONFLICT`,
`422 INVALID_REQUEST/POLICY_NOT_REVIEWED`, and
`429 LOGIN_RATE_LIMITED/CHALLENGE_RATE_LIMITED`. Insufficient ladder permission
returns `decision: DENY` and no execution receipt; inappropriate roles get 403.
Reload current state after a conflict.
