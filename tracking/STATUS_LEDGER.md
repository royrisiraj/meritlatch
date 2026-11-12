# SENTINEL//LADDER V2 — status ledger

**Updated 12 November 2026 — Phase 02.** Complete local suite: **375 passed, zero failed** (266 baseline + 109 new); baseline tests and pure policy remain unchanged. Actual authenticated localhost JPEG smoke passed using MOCK_AI. No live Gemini request, customer image, cloud resource or deployment was used. Live verification is **BLOCKED** pending explicit billable-call approval and consented fictional input/manual ground truth. See [execution log](EXECUTION_LOG.md) and [Phase 02 report](PHASE_02_REPORT.md). Phase 00/01 records remain historical.

| Deliverable | Status | Test/evidence link | Owner | Known risks |
|---|---|---|---|---|
| Repository + dependency environment | TESTED | Existing user commit `a7e7156`; Phase 02 dependency install/pip check; old pins preserved, media/SDK additions pinned | Codex / Phase 02 | Python 3.14.7 only; no new commit/push/remote; pre-existing handover deletions preserved |
| Pure Python policy + Pydantic schema | TESTED | `backend/tests/test_policy.py`, `test_config.py`, `test_security.py`; 85 policy + 19 config + 1 isolation tests passed | Codex / Phase 00 | Evidence eligibility only; fictional policy; no actor auth or L3 |
| FastAPI health and docs | TESTED | Original 8 bootstrap API tests preserved; Phase 01 factory schema/security tests and actual HTTP health/docs 200 | Codex / Phase 01 | Startup must use `backend.app.api:create_app --factory`; legacy main app remains metadata-only |
| CI scaffold | TESTED | `.github/workflows/tests.yml` inspected; invokes locked install, pip check, all tests | Codex / Phase 00 | Remote CI NOT RUN; Python 3.11/3.12 runtime validation unavailable locally |
| Server-side identity and tenant scope | TESTED | `backend/tests/phase01/test_identity.py`, `test_scope.py`: 30 identity and 25 scope tests passed | Codex / Phase 01 | Local bearer/password auth; no production IdP/MFA/TLS |
| Challenge and case API | TESTED | All Phase 01 tests preserved; Phase 02 actual image POST checks role/tenant/job/auth/evidence-session before and after analysis | Codex / Phase 02 | Visible challenge is supporting evidence, not authenticity proof |
| Atomic approval and version binding | TESTED | `test_transactions.py`: 9 passed; evidence/amount/policy/assignment/session/expiry invalidation and restart/idempotency tests | Codex / Phase 01 | SQLite only; Firestore and production-load behavior not verified |
| Persistent jobs, cases, migration and logical audit | TESTED | Core migration 1 retained; additive media migration 1, restart/history/legacy-record tests passed | Codex / Phase 02 | Privileged DB owner can alter history; no retention/recovery workflow |
| Safe media intake and SHA-256 lookup | TESTED | 35 media tests plus resource/provenance/persistence checks; JPEG/PNG HTTP smoke, scoped duplicates/private reads | Codex / Phase 02 | JPEG/PNG only; local ACLs/operator security; no authenticity/perceptual-hash claim |
| Mock perception adapter | TESTED | Typed default UNKNOWN observer and internal positive fixtures, failure/schema/semantic tests; actual HTTP MOCK_AI L2 path | Codex / Phase 02 | Mock is not optical extraction or a real-world benchmark |
| Live Gemini perception adapter | IN_PROGRESS | Official google-genai adapter; 13 SDK transport/config tests with stubs; docs-verified default `gemini-3.6-flash` | Codex / Phase 02 | **BLOCKED LIVE verification**: no approved call or supplied consented/manual-labeled image; no account availability/accuracy result |
| Asynchronous analysis version safety | TESTED | 10 concurrent/late-result tests: both completion orders, expiry/logout/invoice/policy/assignment/challenge changes, pending L3 invalidation, rollback | Codex / Phase 02 | Process crashes can leave pending records/orphan files, never automatic permission promotion |
| Contractor workflow | IN_PROGRESS | Assigned authenticated image submission and scoped private reads tested | Codex / Phase 02 | No portal; live image interpretation still unverified |
| Manager workflow | IN_PROGRESS | Job/case creation, invoice change, independent simulated sign-off tested | Codex / Phase 01 | No portal or actual customer/media flow |
| Engineer workflow | IN_PROGRESS | Assigned/redacted reads, reviewed-version selection, denied business approval tested | Codex / Phase 01 | No red-team/engineering portal or full release gate |
| Red-team regression and alerts | PLANNED | | | |
| Full E2E demo and 3 rehearsals | PLANNED | | | |
| Cloud Run deployment | PLANNED | | | |
| Buyer discovery interviews | PLANNED | | | |

Allowed status values: `PLANNED`, `IN_PROGRESS`, `TESTED`, `DEPLOYED` (DEPLOYED only for running cloud artifacts). For interviews use `COMPLETED` only when actually performed and documented. Track `BLOCKED` in notes; don't silently downgrade tests. Attach actual commands/test stdout in `tracking/EXECUTION_LOG.md` (create as work begins).

Phase 00/01: **ACCEPTED foundation** (user committed it). Phase 02 local tests/HTTP gate: **PASS**; overall live acceptance: **BLOCKED**, not declared complete. One new test setup failed while rendering a fixture after lowering Pillow's pixel limit; fixture creation order was corrected and the original rejection assertion retained. Python 3.11/3.12, remote CI and live Gemini remain NOT RUN. Phase 03 is not authorized. No new commit, push, remote, cloud resource, real transfer or deployment occurred.
