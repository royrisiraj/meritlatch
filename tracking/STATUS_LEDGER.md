# SENTINEL//LADDER V2 — status ledger

**Current checkpoint - Phase 05, 13 November 2026: TESTED / LOCAL PASS.**
Committed Phase 04 baseline verified clean at 09bd8d1. Baseline 562 passed in
84.17s. Backend now 572 passed in 99.01s (562 unchanged + 10 portal-read tests);
frontend 36 passed; production bundle built. Actual Chromium/HTTP contractor,
manager, agent and independent-engineer workflows passed, including unsafe
restriction, correction, version-bound review and readiness without publication.
See [PHASE_05_REPORT.md](PHASE_05_REPORT.md) for final browser stdout, exact commands,
manifest and limits. No Gemini, private-file/marker change, commit, push or deploy.

| Phase 05 deliverable | Status | Evidence and limits |
|---|---|---|
| Three authenticated portals | TESTED | Actual browser/HTTP journeys and 36 mocked component/client tests. Local MVP; full reload requires login. |
| Three scoped portal read views | TESTED | 10 backend tests, real browser integration; safe assignee projection, job-case paging, bounded candidate history. |
| Contractor/manager/agent workflow | TESTED | Invalid media, unsafe L1, rejection L0, fresh canned L2, separate manager L3, idempotent simulated receipt, audit and logout invalidation. Normal mock stays UNKNOWN. |
| Engineer findings/remediation/review/gate | TESTED | Real weak/safe corpus runs, false approval, denied self-review, distinct reviewer and readiness; SYNTHETIC, published=false. |
| Frontend build/lock/security | TESTED | Build, tests, zero known npm audit vulnerabilities and secret scan. Chromium/Windows only, no hosting/certification. |


**Historical checkpoint — Phase 04 acceptance, 12 November 2026: TESTED / LOCAL PASS.**
Fresh acceptance runs: **69 Phase 04 tests passed in 24.93s; 562 total passed in
91.60s**, zero failed. All 493 baseline tests remain unchanged. Actual TCP/HTTP
smoke passed with 38 synthetic scenarios per candidate: safe 38/38, weak candidate
one binary false approval plus one review bypass, restrictive candidate two false
rejections. Unsafe gate BLOCKED; reviewed safe gate READY_FOR_MANUAL_RELEASE;
published=false. See [Phase 04 report](PHASE_04_REPORT.md) and acceptance logs.
Gemini remains frozen; no private credentials, consumed marker or production policy
changed. No commit/push/deploy or Phase 05 work. Awaiting user review of this gate.

**Historical checkpoint — final offline Gemini diagnostic, 12 November 2026.**
Root cause of the historical PROVIDER_UNAVAILABLE: **UNKNOWN**. Local MockTransport
reproduced diagnostic information loss (HTTP 400 became a generic unavailable
error with no status). A small validation-transport change now retains numeric
HTTP status and fixed safe error categories, preserving existing codes/authority/
request behavior. No configuration/model/SDK changes or real network requests.
See [GEMINI_FINAL_DIAGNOSTIC.md](GEMINI_FINAL_DIAGNOSTIC.md) for executed results.

Final offline suite: **493 passed in 76.04s**, zero failed (478 unchanged + 15 new).
Focused diagnostics/guard suite: 39 passed in 1.04s; pip check clean; 43 baseline
test/source/private-file hashes unchanged. Safe metadata correction TESTED locally;
live perception remains unsuccessful/unverified.

**Sequencing:** Gemini troubleshooting is DEFERRED until Phases 04–07 are complete.
Proceeding phases use explicitly labeled MOCK_AI/SYNTHETIC data; no fabricated
LIVE_GEMINI artifacts. The consumed marker/private result are unchanged. Phase 04
is the next separately authorized work, not implemented in this diagnostic.

**Historical checkpoint — 12 November 2026: live validation Stage B.** **FAILED — LIVE API OR SCHEMA ERROR**, reason `PROVIDER_UNAVAILABLE`. User human review recorded, offline preflight READY, then exactly one counted `gemini-3.8-flash` request attempt, zero retries/fallbacks, elapsed 4.6740s. No observations/usage returned; no permission elevation. The one-call budget is used and the private marker/result are preserved. See [validation report](LIVE_GEMINI_VALIDATION_REPORT.md). Subsequent Phase 04 authorization permits no further live calls.

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
| Live Gemini perception adapter | IN_PROGRESS | Historical one-attempt failure unchanged; final offline investigation cannot recover its status. New safe status/transport classification verified with local fixtures only | Codex / final diagnostic | DEFERRED until Phases 04–07 complete; root UNKNOWN, budget used, no more live calls; no verified perception result |
| Asynchronous analysis version safety | TESTED | 10 concurrent/late-result tests: both completion orders, expiry/logout/invoice/policy/assignment/challenge changes, pending L3 invalidation, rollback | Codex / Phase 02 | Process crashes can leave pending records/orphan files, never automatic permission promotion |
| Contractor backend workflow | TESTED | New operation-bound upload replay, fresh-challenge corrected evidence and explicit bounded provider reanalysis; 21 recovery tests plus rejection/race tests and actual HTTP recovery | Codex / Phase 03 | Phase 05 portal tested; mock is not optical extraction; no automatic retries/orphan repair |
| Manager backend workflow | TESTED | Approved job defaults, queue/filter/paging, detailed review, durable rejection, current L2 sign-off and idempotent simulation; 19 workflow + 16 queue/scope tests | Codex / Phase 03 | Phase 05 portal tested; queue scans 500/page, review history caps 100; no real payment |
| Business/inspection/permission separation | TESTED | Typed workflow projection, independent pure ladder, rejection caps matching bytes at L0 while preserving numeric inspection; valid/unsafe/wrong-asset HTTP paths | Codex / Phase 03 | Badges/action hints are informational; current-state API checks always required |
| Workflow concurrency and audit | TESTED | 12 new race/rollback cases, 11 audit/persistence cases; focused scope/concurrency 28 passed; public review/receipt references and newest-first scoped audit pages | Codex / Phase 03 | Local SQLite orderings only, no production load/Firestore evidence |
| Engineer backend workflow | TESTED | Phase 04 authenticated candidate/run/finding/triage/review/gate APIs; 69 phase tests and actual HTTP smoke | Codex / Phase 04 | Phase 05 portal tested; account simulation only, not real multi-human operational approval |
| Independent red-team regression and alerts | TESTED | 38 fixed labeled synthetic scenarios; safe/weak/strict actual evaluations, computed FAR/FRR/review outcomes, deduplicated in-app findings | Codex / Phase 04 | Synthetic benchmark only; no real-world accuracy or live AI generation |
| Candidate correction and release gate | TESTED | Independent active reviewer, exact artifact/source/corpus/run/version binding; CAS, stale invalidation, failure gates and rollback tests | Codex / Phase 04 | Readiness decision only, published=false; no CI/deployment enforcement or automatic operational policy registration |
| Full E2E demo and 3 rehearsals | IN_PROGRESS | Phase 05 six actual browser workflows passed | Phase 05/06 | Three formal demo rehearsals remain deferred; no live perception |
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
