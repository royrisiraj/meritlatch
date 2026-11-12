# Master Book requirement-to-code traceability

Updated 12 November 2026 after Phase 01 local execution. All TESTED claims are local, SYNTHETIC and SQLite only. IN_PROGRESS indicates remaining later-phase scope. Exact commands/output: `tracking/EXECUTION_LOG.md`; acceptance details: `tracking/PHASE_01_REPORT.md`. Master Book pages are 1-indexed.

| ID | Master Book | Must demonstrate | Phase | Status | Evidence field |
|---|---|---|---|---|---|
| R-001 | pp.1–5,28 | New repository, no pre-existing functionality assumed | 00 | TESTED | Initial Git status: no commits; only supplied files. New `backend/`, fixtures, policies and tests; `EXECUTION_LOG.md`. No commit authorized. |
| R-002 | pp.7–8 | Separate inspection status and L0–L3 | 00–01 | TESTED | Unchanged pure models/policy plus `case_service.py`; `test_complete_authenticated_l0_l1_l2_l3_and_idempotent_simulation` and persisted negative observations passed. L3 is manager-reviewed and simulated only. |
| R-003 | pp.8,13–14 | Human L3 approval bound to evidence/policy/amount | 01–03 | TESTED | Local `test_approval_binding_contains_all_required_dimensions_and_is_not_exposed`, nonmanager approval denials and evidence/invoice/policy invalidation tests passed. Real media/Firestore unimplemented. |
| R-004 | pp.8,13–14,17 | Server-side roles, tenant/job assignment | 01 | TESTED | `auth.py`, `case_service.py`, `api.py`; 30 identity + 25 scope tests; all 15 business operation signatures require bearer auth. Two tenants, contractor/engineer/agent assignment, server roles and manager separation verified. |
| R-005 | pp.11–12,18 | Session-bound unpredictable challenge, expiry | 01–02 | TESTED | 13 challenge tests cover secrets-generated tokens, tenant/job/asset/case/auth/evidence-session bindings, expiry, rotation, limits and client override denial. No media-authenticity claim. |
| R-006 | pp.11–12,18 | MIME-independent media validation, limits and private storage | 02 | PLANNED | |
| R-007 | pp.11–12 | Exact hash and scoped duplicate lookup | 02 | PLANNED | |
| R-008 | pp.12–13 | Gemini adapter, schema-valid+semantic uncertainty handling | 02 | PLANNED | |
| R-009 | pp.8,13,18 | Numeric+unit+date policy, unsafe readings restrict | 01–03 | TESTED | Original numeric/unit/date tests retained; `test_persisted_invalid_observation_stays_restricted` and typed intake rejection passed. Synthetic metadata only; no numeric vision accuracy tested. |
| R-010 | pp.11,14 | Fully auditable permission evaluation and API | 01–03 | IN_PROGRESS | Authenticated evaluate/execute/approval/audit API and append-only logical events tested; `test_engineer_gets_redacted_observation_and_audit_has_no_tokens_or_payloads`. Media/Gemini lifecycle still pending. |
| R-011 | pp.13–14,17 | Atomic versioned evidence update and approval invalidation | 01–03 | TESTED | 9 transaction tests: both serialized race orders, simultaneous CAS conflict, concurrent idempotent completion, rollback, post-lock clock sampling. Evidence/amount/policy/reassignment invalidation and stale-pointer rejection passed. SQLite only. |
| R-012 | pp.6–7,27 | Contractor+manager user flow and error feedback | 05 | PLANNED | |
| R-013 | pp.6,16 | Security engineer view separate from business approval | 04–05 | PLANNED | |
| R-014 | pp.16,20 | Red-team runner; human-labeled oracle, both error rates | 04 | PLANNED | |
| R-015 | pp.16,19 | Reproducible, redacted vulnerability alert and review loop | 04–05 | PLANNED | |
| R-016 | pp.16,20 | Pre-release regression gate; no auto policy mutation | 04 | PLANNED | |
| R-017 | pp.19–20 | Privacy minimization, audit events, no immutability claim | All | IN_PROGRESS | Redacted scoped audit, append-only logical events/triggers, redacted error/validation responses and hashed credentials tested. `docs/security.md` describes owner-tampering/retention limitations; no media retention implemented. |
| R-018 | pp.20,26–27 | Real Gemini demo + failures; separate benchmark types | 02,06 | PLANNED | |
| R-019 | pp.25,27 | Official five judging criteria; honest application and 3-min pitch | 06 | PLANNED | |
| R-020 | pp.26,28 | Reproducible PowerShell instructions, CI tests, optional Cloud Run | 00,06 | IN_PROGRESS | `README.md`, locked dependencies plus SQLAlchemy only; Windows/Python 3.14.7: 266 passed; actual authenticated Uvicorn HTTP smoke passed. CI and Python 3.11/3.12 NOT RUN; cloud unimplemented. |
| R-021 | pp.9,21–24 | Narrow initial buyer; no competitor-free/traction claims | All | PLANNED | |
| R-022 | pp.12,24 | Gemini now; Gemma later, provider swap unverified | 02 | PLANNED | |
| R-023 | pp.17–20 | Replay, injection, race, uploaded content edge tests | 02–04 | IN_PROGRESS | Early challenge cross-session/replay and authority-field injection denial, stale-pointer and race tests passed. Uploaded media and adversarial corpus tests remain later phases. |
| R-024 | pp.28–29 | Every milestone diff/test/risks/rollback note | All | IN_PROGRESS | Phase 00/01 reports, execution log, original-test hashes and `docs/decisions.md` record changes, results (including fixed regression), risks and rollback. Future milestones pending. |

Requirements can be refined, but no item may be marked TESTED without a runnable test or inspected artifact. DEPLOYED requires an independently accessed working endpoint. `READY`/`PLANNED` does not mean functioning.
