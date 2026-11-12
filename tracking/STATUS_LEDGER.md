# SENTINEL//LADDER V2 — status ledger

**Current checkpoint — 12 November 2026: live validation Stage B.** **FAILED — LIVE API OR SCHEMA ERROR**, reason `PROVIDER_UNAVAILABLE`. User human review recorded, offline preflight READY, then exactly one counted `gemini-3.8-flash` request attempt, zero retries/fallbacks, elapsed 4.6740s. No observations/usage returned; no permission elevation. The one-call budget is used and the private marker/result are preserved. See [validation report](LIVE_GEMINI_VALIDATION_REPORT.md) for current regressions and [execution log](EXECUTION_LOG.md). Stop here; no Phase 04 authorization.

Phase 03 historical local gate: 454 passed, zero failed (375 preserved + 79 new), 67.99s; actual authenticated TCP/HTTP completion, unsafe/wrong-asset denials and rejection/correction/recovery passed using labeled canned MOCK_AI. [Phase 03 report](PHASE_03_REPORT.md) remains its evidence; these were not live vision results. No customer image, paid resource or deployment occurred.

| Deliverable | Status | Test/evidence link | Owner | Known risks |
|---|---|---|---|---|
| Repository + dependency environment | TESTED | Baseline `0727e05`, initially clean; Phase 03 pip check passes, dependency files unchanged | Codex / Phase 03 | Python 3.14.7 only; no commit/push/reset/remote or recreated handovers |
| Pure Python policy + Pydantic schema | TESTED | `backend/tests/test_policy.py`, `test_config.py`, `test_security.py`; 85 policy + 19 config + 1 isolation tests passed | Codex / Phase 00 | Evidence eligibility only; fictional policy; no actor auth or L3 |
| FastAPI health and docs | TESTED | Original 8 bootstrap API tests preserved; Phase 01 factory schema/security tests and actual HTTP health/docs 200 | Codex / Phase 01 | Startup must use `backend.app.api:create_app --factory`; legacy main app remains metadata-only |
| CI scaffold | TESTED | `.github/workflows/tests.yml` inspected; invokes locked install, pip check, all tests | Codex / Phase 00 | Remote CI NOT RUN; Python 3.11/3.12 runtime validation unavailable locally |
| Server-side identity and tenant scope | TESTED | `backend/tests/phase01/test_identity.py`, `test_scope.py`: 30 identity and 25 scope tests passed | Codex / Phase 01 | Local bearer/password auth; no production IdP/MFA/TLS |
| Challenge and case API | TESTED | All Phase 01 tests preserved; Phase 02 actual image POST checks role/tenant/job/auth/evidence-session before and after analysis | Codex / Phase 02 | Visible challenge is supporting evidence, not authenticity proof |
| Atomic approval and version binding | TESTED | `test_transactions.py`: 9 passed; evidence/amount/policy/assignment/session/expiry invalidation and restart/idempotency tests | Codex / Phase 01 | SQLite only; Firestore and production-load behavior not verified |
| Persistent jobs, cases, migration and logical audit | TESTED | Workflow namespace v1 added; core/media v1 unchanged; legacy approval/history migration, restart/rejection/operation persistence and append-only tests passed | Codex / Phase 03 | Privileged DB owner can alter history; no downgrade/retention/orphan repair; old media current-only |
| Safe media intake and SHA-256 lookup | TESTED | 35 media tests plus resource/provenance/persistence checks; JPEG/PNG HTTP smoke, scoped duplicates/private reads | Codex / Phase 02 | JPEG/PNG only; local ACLs/operator security; no authenticity/perceptual-hash claim |
| Mock perception adapter | TESTED | Typed default UNKNOWN observer and internal positive fixtures, failure/schema/semantic tests; actual HTTP MOCK_AI L2 path | Codex / Phase 02 | Mock is not optical extraction or a real-world benchmark |
| Live Gemini perception adapter | IN_PROGRESS | Human-reviewed exact 3.8 sample; preflight READY; one attempted request failed PROVIDER_UNAVAILABLE; 24 guard tests pass | Codex / controlled validation | Live success/perception remains unverified; budget used, no retry/fallback authorized; no specific HTTP status retained |
| Asynchronous analysis version safety | TESTED | 10 concurrent/late-result tests: both completion orders, expiry/logout/invoice/policy/assignment/challenge changes, pending L3 invalidation, rollback | Codex / Phase 02 | Process crashes can leave pending records/orphan files, never automatic permission promotion |
| Contractor backend workflow | TESTED | New operation-bound upload replay, fresh-challenge corrected evidence and explicit bounded provider reanalysis; 21 recovery tests plus rejection/race tests and actual HTTP recovery | Codex / Phase 03 | No portal; mock is not optical extraction; no automatic retries/orphan repair |
| Manager backend workflow | TESTED | Approved job defaults, queue/filter/paging, detailed review, durable rejection, current L2 sign-off and idempotent simulation; 19 workflow + 16 queue/scope tests | Codex / Phase 03 | No portal; queue scans 500/page, review history caps 100; no real payment |
| Business/inspection/permission separation | TESTED | Typed workflow projection, independent pure ladder, rejection caps matching bytes at L0 while preserving numeric inspection; valid/unsafe/wrong-asset HTTP paths | Codex / Phase 03 | Badges/action hints are informational; current-state API checks always required |
| Workflow concurrency and audit | TESTED | 12 new race/rollback cases, 11 audit/persistence cases; focused scope/concurrency 28 passed; public review/receipt references and newest-first scoped audit pages | Codex / Phase 03 | Local SQLite orderings only, no production load/Firestore evidence |
| Engineer workflow | IN_PROGRESS | Assigned/redacted reads, reviewed-version selection, denied business approval tested | Codex / Phase 01 | No red-team/engineering portal or full release gate |
| Red-team regression and alerts | PLANNED | | | |
| Full E2E demo and 3 rehearsals | PLANNED | | | |
| Cloud Run deployment | PLANNED | | | |
| Buyer discovery interviews | PLANNED | | | |

Allowed status values: `PLANNED`, `IN_PROGRESS`, `TESTED`, `DEPLOYED` (DEPLOYED only for running cloud artifacts). For interviews use `COMPLETED` only when actually performed and documented. Track `BLOCKED` in notes; don't silently downgrade tests. Attach actual commands/test stdout in `tracking/EXECUTION_LOG.md` (create as work begins).

Phase 00/01: **ACCEPTED foundation**. User committed Phase 02 as `0727e05` and authorized Phase 03. Phase 03 local backend gate: **PASS / TESTED**; subsequently user committed it as `562e5eb`. Historical Phase 03 live status was BLOCKED - AWAITING AUTHORIZATION. The new controlled live-validation checkpoint below records current authorization separately. Python 3.11/3.12, remote CI, cloud and real image interpretation remain NOT RUN. No tests were weakened; no test failures occurred in recorded Phase 03 runs. No agent commit, push, reset, remote, paid resource, real transfer, deployment, frontend or Phase 04 work occurred.

## Controlled live validation — Stage A history, 12 November 2026

Status: **IN_PROGRESS / BLOCKED — HUMAN IMAGE AND GROUND-TRUTH REVIEW REQUIRED**.
User authorized at most one `gemini-3.8-flash` inference; the billing scope does
not need renewed approval. Key presence=true, ignored/untracked `.env` verified
without disclosure or edits. Local Pillow synthetic card and original-schema
expected fields are prepared in ignored `fixtures/live_inputs/gemini_3_8_validation/`.
`human_reviewed=false`. Detailed offline preflight reports only that review block;
request_count=0, retry_count=0, budget unused. No live call or model fallback.

Offline one-send/error/redirect/review-binding/runner tests pass. The complete
current regression count and actual stdout are in
[`LIVE_GEMINI_VALIDATION_REPORT.md`](LIVE_GEMINI_VALIDATION_REPORT.md) and its
command evidence. All 454 Phase 03 baseline tests, pure policy, manager logic,
dependency pins and `.env` remain unchanged. No Phase 04 work authorized.

## Controlled live validation — Stage B result, 12 November 2026

**IN_PROGRESS; live outcome FAILED — PROVIDER_UNAVAILABLE.** User confirmed the
exact image and ground truth; human review/binding recorded. Preflight READY,
then one attempted `gemini-3.8-flash` send, zero retries/fallbacks, 4.6740026s,
DENY. No observations/model version/usage or specific HTTP status available.
The marker/result are preserved; one-call budget used and no further request
authorized. Live perception/availability remain unverified, not a local gate pass.

Post-request local regressions: **478 passed in 58.30s**, zero failed; guard suite
24 passed in 3.09s before request; pip check clean. All 37 captured baseline file
hashes match, including tests/provider/runner/policy/manager logic/pins/.env.
Stage B tracked changes are reports/docs only; private review/result/reservation
remain ignored. No commit, push, deployment or Phase 04 work.
