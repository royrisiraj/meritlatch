# Security and workflow test catalog

## Phase 05 executed mapping - 13 November 2026

Baseline: 562 passed; all 36 old backend test files retain their hashes. Current:
572 backend passed (562 + 10), 36 frontend unit/component passed, build and real
Chromium/HTTP workflows passed. [Evidence](PHASE_05_REPORT.md).

| Suite | Tested boundary |
|---|---|
| backend/tests/phase05/test_portal_reads.py (10) | Actual TestClient auth, manager-only assignees/safe projection/tenant/cursor/bounds; assigned job-case paging and cross-job denial; scoped engineer-only candidate history. |
| frontend/src/test/api.test.ts (5) | Mock fetch: bearer header/no storage/cookie/redirect, safe 401, no implicit mutation retry, external/path rejection. |
| frontend/src/test/presentation.test.tsx (23) | Mock component data: exact L-levels and separate statuses, honest source, denominator/N/A/review metrics, public audit, safe errors/reasons, upload type/empty/size. |
| frontend/src/test/session.test.tsx (8) | Mock fetch/jsdom: login/logout, four server-role landings, role guards, loading/failed login and expired session. |
| frontend/e2e/portals.spec.ts | Actual Chromium/React/FastAPI with independent fictional accounts; job creation, decoder denial, unsafe restriction, rejection/correction, private media, exact L3, repeated agent receipt, logout invalidation; real weak/safe runs, finding/triage/proposal/self-review denial/independent gate; direct/SPA role/tenant/assignment denials; stale-state/refetch/network fault; lost-response upload replay; normal UNKNOWN at 375/768/1440; revoked-session mutation and keyboard focus. |

Positive values are acknowledged canned MOCK_AI, not optical extraction. Normal
mock stays UNKNOWN; assurance is SYNTHETIC. Expected denial/network resource errors
are separated from unhandled page/console exceptions. No live AI, publication,
production benchmark, cross-browser or screen-reader certification claimed.

Reference: Master Book chapters 4, 9, 12–15 and Appendix B. Expectations must be independent of Gemini. Historical Phase 04 executed local evidence: `PHASE_04_REPORT.md`, `EXECUTION_LOG.md` and acceptance logs — 562 passed, zero failed (493 unchanged + 69 Phase 04). Historical phase results below remain evidence for their scope. Live Gemini remains unsuccessful/deferred; production/deployment benchmarks unverified.

## Phase 04 executed mapping

| Suite | Cases | Assertions audited |
|---|---:|---|
| `phase04/test_oracle.py` | 18 | Independent labels never query SUT, deterministic ordering, conflicts/orphans/invalid input/pending review rejection, exact status/permission/reasons and review scoring; weak real policy reproduction. |
| `phase04/test_scope.py` | 15 | Every engineering route requires bearer/ENGINEER; tenant/cursor and business-role denial, bounds/no arbitrary rule/code, disabled suggestions, engineer denied business approval; current factory OpenAPI versus explicit historical test factory. |
| `phase04/test_transactions.py` | 15 | Single worker for repeated keys, stale candidate run, logout failure, interrupted/forged/missing/unevaluable results, review CAS/rejection, candidate/gate races, transactional proposal rollback. |
| `phase04/test_persistence_and_limits.py` | 15 | Restart, additive/unknown migrations, append-only controls, manifest tampering, run limits, credential-free subprocess/timeout, unexpected failure redaction, changed corpus/disabled reviewer. |
| `phase04/test_workflow.py` | 6 | Real safe/weak subprocess evaluations, false rejections, finding dedup/redaction, independent human-account review, failed weak gate despite sign-off, safe readiness and dismissal preserving failed evidence. |

Fresh real HTTP smoke executes three candidate profiles against 38 fixed synthetic
scenarios each, uses authenticated engineers/reviewer, records a reproduced A02
false approval, triages and verifies safe remediation, blocks unsafe/overly strict
gates, denies business roles and other tenants, and confirms published=false.
Readonly binding snapshots are not a manager sign-off. Cached actually executed
synthetic outputs accelerate parent CRUD/race tests; the smoke uses fresh workers.
No live AI, customer dataset, production accuracy or policy publication claim.

## Phase 03 executed mapping

| Suite | Cases | Security behavior |
|---|---:|---|
| `backend/tests/phase03/test_workflow.py` | 19 | Approved manager job defaults/exact currency, L0/L1/L2/L3 separation, safe enum rejection, fresh correction, stale approval denial, preserved reviews, idempotent completion/reapproval. |
| `backend/tests/phase03/test_queue_and_scope.py` | 16 | Scoped manager queue/filter/paging/details, wrong roles/tenant/cursors, protected endpoints, redacted observations/media/internal secrets. |
| `backend/tests/phase03/test_recovery.py` | 21 | Session-bound upload keys, replay without more inference, failed/stale/pending grace recovery, no reanalysis of success/unsafe/schema-invalid/rejected, three-run limit, restart and billable guard with no network. |
| `backend/tests/phase03/test_transactions.py` | 12 | Approve/reject races, reject during analysis, upload collisions/same-key requests, recovery vs newer evidence/invoice/policy/expiry/assignment, atomic rollback. |
| `backend/tests/phase03/test_audit_and_persistence.py` | 11 | Scoped paged audit/public references/redaction, append-only histories, restart, legacy approval migration and unknown-version denial. |

All 375 prior tests also passed unchanged; hashes are in
`PHASE_03_BASELINE_TEST_HASHES.json`. Real loopback HTTP smoke demonstrates one
completed path, unsafe and wrong-asset denials, and rejection/correction/provider
recovery with labeled canned MOCK_AI. It does not measure optical extraction.

## Core policy (minimum)
- valid asset+current challenge+complete fictional sensor observations: L2 allowed for `prepare_invoice`, but **not** L3.
- no evidence: L0; missing identifier: not L2; mismatched/placeholder ID (`N/A`, `UNKNOWN`): deny.
- expired/wrong/previous session challenge: deny; nonexistent or double-used challenge: deny; incorrect tenant/job binding: deny.
- required pressure missing, NaN/Infinity, negative when invalid, wrong/unknown unit: no L2.
- exact lower/upper boundaries exercise inclusive/exclusive spec; out-of-range or expired required tag => `SAFETY_ALERT`, not L2.
- ambiguous multiple asset IDs or contradictory frames => `REVIEW_REQUIRED`.
- `reading_visible=true` with no typed value is never enough.

## Roles and state
- contractor cannot manager approve; contractor cannot see another contractor's jobs; tenant A cannot see tenant B records by direct API ID.
- manager can't edit policy just by changing frontend tab; engineer cannot approve invoices; service agent action constrained by action scope and state.
- evidence replacement, policy version change, invoice amount change or challenge expiry invalidates approval.
- concurrent approval and evidence replacement cannot resurrect prior approval; stale `expected_case_version` must be rejected.
- repeated action requests are idempotent; double human approval does not create duplicate completion events.

## Media and AI
- malformed JPEG/PNG, false MIME declarations, oversized bytes, huge pixel dimensions, invalid frames and unsupported extensions handled safely.
- exact SHA-256 repeated within policy scope flags or blocks appropriately, without treating all visual similarities as proven fraud.
- prompt injection written inside a synthetic image never directly sets `allowed`, changes policy or grants manager role.
- Gemini timeout, quota error, invalid JSON, semantically uncertain JSON and missing fields => no unintended escalation.
- provider-specific `MOCK_AI`, `LIVE_GEMINI`, `RECORDED_LIVE`, `SYNTHETIC` tags present in UI/logs and can't be forged through user input.

## Red team and benchmark
- fixed independently labeled valid/invalid cases measure TP/FP/TN/FN for decisions; both false approvals and false rejections.
- intentionally weak policy version produces an **actually reproduced** failing case, no static fabricated chart.
- candidate Gemini scenario cannot become regression oracle or patch without human review.
- any version missing regression requirements cannot be released, and tests cannot modify live policy.
- alert contains case ID/test ID, policy version, expectation, observed decision, severity and safe reference, not raw photo or secret.

## User workflow and deployment
- contractor→manager→engineer flow works with mock provider; contractor can't approve even by API call.
- at least one real Gemini media inference with recorded model, elapsed time and evidence type; compare outputs with manually labeled observations.
- valid and two invalid submissions reproduce on desktop and mobile; cloud endpoint if deployed reachable from another device.
- no real payment, no external equipment control, no unverified real-world detection-rate claim.

## Suggested suites
`test_policy.py`, `test_identity.py`, `test_concurrency.py`, `test_media.py`, `test_gemini_provider.py`, `test_redteam.py`, `test_e2e.py`, `test_deployment_smoke.py` (filenames may vary, coverage may not). Each suite should state whether its fixtures are synthetic or recorded real media.
