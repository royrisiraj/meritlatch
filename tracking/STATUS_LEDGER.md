# SENTINEL//LADDER V2 — status ledger

**Updated 12 November 2026 — Phase 01.** Phase 00 accepted; its 113 tests remain byte-for-byte unchanged. Complete local suite: 266 passed, zero failed, one existing dependency deprecation warning. Actual localhost HTTP smoke exercised authenticated case/challenge/approval/completion and invalidation. All observations were SYNTHETIC; no live provider, customer data or deployment. See [execution log](EXECUTION_LOG.md), [Phase 00 record](PHASE_00_REPORT.md), and [Phase 01 report](PHASE_01_REPORT.md).

| Deliverable | Status | Test/evidence link | Owner | Known risks |
|---|---|---|---|---|
| Repository + dependency environment | TESTED | `EXECUTION_LOG.md`: Git status, locked install, pip check; SQLAlchemy==2.1.8 added, prior pins preserved | Codex / Phase 01 | Only Python 3.14.7 executed; no commits/remotes |
| Pure Python policy + Pydantic schema | TESTED | `backend/tests/test_policy.py`, `test_config.py`, `test_security.py`; 85 policy + 19 config + 1 isolation tests passed | Codex / Phase 00 | Evidence eligibility only; fictional policy; no actor auth or L3 |
| FastAPI health and docs | TESTED | Original 8 bootstrap API tests preserved; Phase 01 factory schema/security tests and actual HTTP health/docs 200 | Codex / Phase 01 | Startup must use `backend.app.api:create_app --factory`; legacy main app remains metadata-only |
| CI scaffold | TESTED | `.github/workflows/tests.yml` inspected; invokes locked install, pip check, all tests | Codex / Phase 00 | Remote CI NOT RUN; Python 3.11/3.12 runtime validation unavailable locally |
| Server-side identity and tenant scope | TESTED | `backend/tests/phase01/test_identity.py`, `test_scope.py`: 30 identity and 25 scope tests passed | Codex / Phase 01 | Local bearer/password auth; no production IdP/MFA/TLS |
| Challenge and case API | TESTED | 13 challenge tests; workflow/persistence/API-boundary tests; actual HTTP smoke | Codex / Phase 01 | No real media intake; synthetic factory internal only; challenge text does not prove authenticity |
| Atomic approval and version binding | TESTED | `test_transactions.py`: 9 passed; evidence/amount/policy/assignment/session/expiry invalidation and restart/idempotency tests | Codex / Phase 01 | SQLite only; Firestore and production-load behavior not verified |
| Persistent jobs, cases, migration and logical audit | TESTED | `test_persistence.py`: 18 passed; migration/CAS/FKs/restart and append-only triggers | Codex / Phase 01 | Initial migration only; privileged DB owner can alter history |
| Safe media intake and SHA-256 lookup | PLANNED | | | |
| Mock perception adapter | PLANNED | | | |
| Live Gemini perception adapter | PLANNED | | | |
| Contractor workflow | IN_PROGRESS | Assigned-job/challenge/denied self-approval API paths tested | Codex / Phase 01 | Media and portal remain unimplemented |
| Manager workflow | IN_PROGRESS | Job/case creation, invoice change, independent simulated sign-off tested | Codex / Phase 01 | No portal or actual customer/media flow |
| Engineer workflow | IN_PROGRESS | Assigned/redacted reads, reviewed-version selection, denied business approval tested | Codex / Phase 01 | No red-team/engineering portal or full release gate |
| Red-team regression and alerts | PLANNED | | | |
| Full E2E demo and 3 rehearsals | PLANNED | | | |
| Cloud Run deployment | PLANNED | | | |
| Buyer discovery interviews | PLANNED | | | |

Allowed status values: `PLANNED`, `IN_PROGRESS`, `TESTED`, `DEPLOYED` (DEPLOYED only for running cloud artifacts). For interviews use `COMPLETED` only when actually performed and documented. Track `BLOCKED` in notes; don't silently downgrade tests. Attach actual commands/test stdout in `tracking/EXECUTION_LOG.md` (create as work begins).

Phase 00: **ACCEPTED BY USER**. Phase 01 local gate: **PASS**. No available test is blocked. Python 3.11/3.12 and remote CI remain **NOT RUN**; scaffold status does not mean CI ran. One clock-lock regression failed during development, was fixed without weakening it, and is included in the passing suite. Phase 02: **AWAITING USER APPROVAL**. Risk/rollback details are in the report. No commit, push, remote configuration, cloud resource or deployment occurred.
