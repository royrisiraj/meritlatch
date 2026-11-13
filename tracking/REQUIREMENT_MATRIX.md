# Master Book requirement-to-code traceability

**Current Phase 06 - 13 November 2026: TESTED / LOCAL PASS.** Clean committed
baseline 92bd728; actual baseline 572/36/6, current 616/42/6 passed. All original
tests unchanged. Native package/local rehearsals passed; remote NOT ATTEMPTED,
durable cloud adapters BLOCKED/DEFERRED. [Evidence](PHASE_06_REPORT.md).

| Phase 06 requirement / book alignment | Implementation | Verification | State / limitation |
|---|---|---|---|
| Ch.20-23 credible deployment/persistence | docs/deployment_decision_phase06.md | Actual SQL/filesystem inventory; primary cloud docs; all data categories mapped | TESTED local; external adapters/IAM/recovery deferred |
| Reproducible Windows native operation | scripts/Demo.ps1; backend/tools/local_ops.py | Real clean-shell Start/Status/Stop/Backup; occupied ports, lease/instance mismatch, no secrets inherited | TESTED; existing environment required, HTTP loopback only |
| Honest health vs ready | backend/app/hosting.py | SQLite begin/media probe/asset integrity, status-only readiness, negative storage/asset tests | TESTED; not durability certification |
| Auth/tenant/job and exact bound human approval | Existing unchanged auth/case/policy plus hosting wrapper | All 572 baseline tests; actual native direct denials and invoice invalidation | TESTED; no frontend/launcher authority |
| Isolated acknowledged MOCK_AI | Existing unchanged portal_demo.py via launcher | Fresh UUID roots/accounts, ordinary mock UNKNOWN, unsafe/correction/manager/agent simulation | TESTED; no optical/live perception |
| Native safe build/export | backend/tools/release_package.py | Determinism, canaries, tamper/path/overwrite limits, 52-file final archive and actual HTTP startup | TESTED; no bundled runtime/container/signature |
| Independent findings and manual gate | Existing security worker/API + rehearsal/run.mjs | Three weak/safe full runs each, real finding, denied self-review, distinct reviewer; published=false | TESTED fixed SYNTHETIC only |
| Three timed demonstrations | frontend/rehearsal/run.mjs; tracking/phase06_evidence | Three fresh actual Chromium/native executions and per-step records | TESTED visual; human speech UNVERIFIED |
| Honest source labels | cases.tsx and ui.tsx text only | Actual screenshots/browser inspection and unchanged baseline component tests | TESTED; no UI redesign |
| Loopback dev proxy only | frontend/config/loopback.ts; vite.config.ts | Six new tests reject external/credential/path/query targets | TESTED |
| Buildathon pitch/evidence/risks | docs/pitch_phase06.md; runbook/operations/security review; evidence README | Book-recorded criteria, 180s plan, measured timings/screenshots, explicit gaps | TESTED artifacts; no founder/market/live claims invented |
| Regression/CI/secret exclusion | phase06 tests; two workflows; PHASE_06_SECURITY_CHECKS.json | 616/42/6, pip check, npm audit; 42 old files/15 protected hashes, 28 private exact values absent in packages | TESTED local; remote CI NOT RUN |
| Phase gate/no cloud/no model | Preserved protected hashes; ledger/report | No model/credential/cloud/deploy/commit action; remote NOT ATTEMPTED | TESTED local scope; Phase 07 not authorized |

**Historical Phase 05 - 13 November 2026: TESTED / LOCAL PASS.** Baseline 09bd8d1 verified
clean; 562 baseline passed (84.17s), 572 current backend passed (99.01s), 36 frontend
passed, production build and real Chromium/HTTP journeys passed. All 36 original
backend test files unchanged. Evidence: PHASE_05_REPORT.md and separate execution
logs. MOCK_AI/SYNTHETIC only, Gemini frozen. Stop before Phase 06.

**Phase 04 acceptance — 12 November 2026:** local backend gate PASS/TESTED. Actual
fresh runs: 69 Phase 04 passed (24.93s), 562 complete passed (91.60s), zero failed;
all 493 old tests unchanged. True HTTP smoke passed; safe 38/38, deliberately weak
false approval/review bypass, restrictive false rejections, reviewed readiness
without publication. See PHASE_04_REPORT.md. Gemini/credentials/consumed marker
unchanged; live work remains deferred through 04–07. No Phase 05 authorization.

**Final offline Gemini diagnostic — 12 November 2026:** original live root cause
UNKNOWN; no new Gemini/list-models/network diagnostic. One reproduced information-
loss defect corrected only in validation transport: safe numeric HTTP status/
fixed HTTP/TLS/transport category, original public codes and fail-closed behavior
unchanged. R-008/R-018/R-022 remain IN_PROGRESS with live work DEFERRED until
Phases 04–07 finish. Subsequent phases use explicit MOCK_AI/SYNTHETIC data only
where needed; never fabricated LIVE_GEMINI. Evidence: GEMINI_FINAL_DIAGNOSTIC.md.
No Phase 04 implementation or authorization is implied by this checkpoint.

**Live validation Stage B update — 12 November 2026:** R-008/R-018/R-022 remain
IN_PROGRESS. User confirmed the exact fictional image/ground truth; preflight
READY. The one authorized `gemini-3.8-flash` attempt failed PROVIDER_UNAVAILABLE,
4.6740s, one counted send/zero retries, no fallback. No returned observations,
usage, live perception success or model availability claim. The request budget
is used; marker/result retained and no further request authorized. Existing 478
tests/source remain unchanged; current executed regressions are recorded in
`LIVE_GEMINI_VALIDATION_REPORT.md`. No Phase 04 work.

Updated 12 November 2026 after Phase 03 local execution. TESTED claims cover local SYNTHETIC/MOCK_AI, SDK stubs and SQLite only; no live Gemini result exists. **454 passed** (375 preserved + 79 new), zero failed; 20 baseline test file hashes unchanged. Focused authorization/concurrency: 28 passed; real TCP/HTTP valid, unsafe, wrong-asset and recovery journeys passed. Evidence: `tracking/EXECUTION_LOG.md`, `tracking/PHASE_03_REPORT.md`, `docs/workflow_phase03.md`. LIVE_GEMINI is BLOCKED - AWAITING AUTHORIZATION. Master Book pages are 1-indexed.

| ID | Master Book | Must demonstrate | Phase | Status | Evidence field |
|---|---|---|---|---|---|
| R-001 | pp.1–5,28 | New repository, no pre-existing functionality assumed | 00 | TESTED | Initial Git status: no commits; only supplied files. New `backend/`, fixtures, policies and tests; `EXECUTION_LOG.md`. No commit authorized. |
| R-002 | pp.7–8 | Separate inspection status and L0–L3 | 00–01 | TESTED | Unchanged pure models/policy plus `case_service.py`; `test_complete_authenticated_l0_l1_l2_l3_and_idempotent_simulation` and persisted negative observations passed. L3 is manager-reviewed and simulated only. |
| R-003 | pp.8,13–14 | Human L3 approval bound to evidence/policy/amount | 01–03 | TESTED | Original binding unchanged; new public review snapshots include invoice revision, exact evidence/version/policy/reviewer/case. Every invoice revision advances bound case version and clears approval atomically. Media workflow, rejection races and idempotent reapproval/completion pass. Firestore unimplemented. |
| R-004 | pp.8,13–14,17 | Server-side roles, tenant/job assignment | 01–03 | TESTED | Baseline identity/scope tests preserved; new endpoints reject missing auth, wrong roles, other tenant/cursors and unassigned contractor recovery. No role switcher or provisioning endpoint. |
| R-005 | pp.11–12,18 | Session-bound unpredictable challenge, expiry | 01–02 | TESTED | 13 challenge tests cover secrets-generated tokens, tenant/job/asset/case/auth/evidence-session bindings, expiry, rotation, limits and client override denial. No media-authenticity claim. |
| R-006 | pp.11–12,18 | MIME-independent media validation, limits and private storage | 02 | TESTED | `media.py`, `media_storage.py`, `test_media.py`, decoder-bomb/EXIF/GPS/private-read tests; actual JPEG HTTP smoke. Bounds, format mismatch, truncation, multiframe rejection, random private names and scoped reads verified. JPEG/PNG only. |
| R-007 | pp.11–12 | Exact hash and scoped duplicate lookup | 02 | TESTED | Exact original SHA-256 plus normalized provider-input digest; `test_exact_duplicate_lookup_is_tenant_scoped_and_does_not_prove_fraud`, private read digest validation, tenant/sha uniqueness. Same bytes allowed in a different tenant; duplicate errors reveal no other case reference. |
| R-008 | pp.12–13 | Gemini adapter, schema-valid+semantic uncertainty handling | 02 | IN_PROGRESS | Schema/semantic/SDK tests retained. Stage B human-reviewed exact 3.8 sample, preflight READY; one attempted request failed PROVIDER_UNAVAILABLE, zero retries. No typed live observation or account availability result; no fallback. |
| R-009 | pp.8,13,18 | Numeric+unit+date policy, unsafe readings restrict | 01–03 | TESTED | Original numeric/unit/date tests retained; `test_persisted_invalid_observation_stays_restricted` and typed intake rejection passed. Synthetic metadata only; no numeric vision accuracy tested. |
| R-010 | pp.11,14 | Fully auditable permission evaluation and API | 01–03 | TESTED | Append-only case/job/review/recovery transitions, safe source/actor/version/reason/public review/receipt references; bounded scoped newest-first audit and filters tested. Actual HTTP completion/rejection/recovery audits passed. Logical local history, not tamper-proof. |
| R-011 | pp.13–14,17 | Atomic versioned evidence update and approval invalidation | 01–03 | TESTED | Existing 9 transaction tests plus 10 actual asynchronous intake race/finalization tests. Upload clears L3 before provider I/O; all late results require matching current version/scope. SQLite only; filesystem/DB crash atomicity is not claimed. |
| R-012 | pp.6-7,27 | Contractor+manager user flow and error feedback | 03,05 | TESTED | React portals and actual Chromium/HTTP create/assign/challenge/upload, decoder denial, unsafe restriction, rejection/correction, private media, current L2/L3 review and restricted agent receipts/audit. UNKNOWN normal mock, stale/network/session/role/tenant denials tested. |
| R-013 | pp.6,16 | Security engineer view separate from business approval | 04-05 | TESTED | Real authenticated portal uses actual backend corpus/results/metrics/findings/review/gate. Direct engineer invoice approval and manager engineering access denied. No role impersonation. |
| R-014 | pp.16,20 | Red-team runner; human-labeled oracle, both error rates | 04 | TESTED | Independent fixed specification-reference SYNTHETIC oracle, 38 scenarios; labels separate from generation/execution; no additional human dataset review claimed. Safe/weak/strict real SUT execution measures binary FA/FR plus separate review/abstentions. |
| R-015 | pp.16,19 | Reproducible redacted finding and review loop | 04-05 | TESTED | React feed/filter/detail/triage/proposal/history; actual A02 false approval, independent safe review and readiness. No raw media/secret or external mail; publication remains false. |
| R-016 | pp.16,20 | Pre-release regression gate; no auto policy mutation | 04 | TESTED | Exact current artifact/source/corpus/run/review bindings; mandatory failure/false approval/valid-case gates; source/change/rejection invalidates readiness. Unsafe BLOCKED, reviewed safe READY_FOR_MANUAL_RELEASE; no auto publication/deployment pipeline. |
| R-017 | pp.19–20 | Privacy minimization, audit events, no immutability claim | All | IN_PROGRESS | Private raw media, stripped provider metadata, minimal untrusted EXIF/GPS flags, scoped attachment reads and append-only logical analyses tested. Local ACLs/retention/orphan recovery remain operator/later-phase work; no immutable ledger claim. |
| R-018 | pp.20,26–27 | Real Gemini demo + failures; separate benchmark types | 02,06 | IN_PROGRESS | HTTP MOCK_AI workflow remains separately tested. User reviewed/authorized the Stage B image; one exact-model request failed in 4.6740s, PROVIDER_UNAVAILABLE, zero retries. No observations/usage/accuracy or successful inference latency/cost result. Private marker/result retained; authorization budget used. |
| R-019 | pp.25,27 | Official five judging criteria; honest application and 3-min pitch | 06 | PLANNED | |
| R-020 | pp.26,28 | Reproducible PowerShell instructions, CI tests, optional Cloud Run | 00–03,06 | IN_PROGRESS | `docs/workflow_phase03.md`, README/report; Windows/Python 3.14.7: 454 passed, pip check clean, actual TCP/HTTP smoke passed. Pins unchanged. Python 3.11/3.12/remote CI/cloud not run; user baseline preserved. |
| R-021 | pp.9,21–24 | Narrow initial buyer; no competitor-free/traction claims | All | PLANNED | |
| R-022 | pp.12,24 | Gemini now; Gemma later, provider swap unverified | 02 | IN_PROGRESS | Existing protocol/Mock/Gemini adapters unchanged. Exact 3.8 live attempt failed safely, no fallback or second call; successful availability/perception unverified. Gemma not implemented. |
| R-023 | pp.17–20 | Replay, injection, race, uploaded content edge tests | 02–04 | TESTED | All prior media/auth/race tests retained; independent corpus adds replay, authority-field text, actor/tenant, stale-binding and concurrent invoice cases. New run/review/gate concurrency tests pass. No universal injection immunity/authenticity claim. |
| R-024 | pp.28–29 | Every milestone diff/test/risks/rollback note | All | IN_PROGRESS | Phase 04 report, preserved initial failures/smoke, fresh acceptance logs, baseline hashes and API/architecture/security/decisions document real evidence, limits, freeze and rollback. Stop at Phase 04; later milestones pending. |
| R-025 | pp.6–7,13–14 | Manager verification queue and detailed review | 03 | TESTED | `workflow_service.py`, typed schemas; bounded filtered tenant queue, deterministic paging, redacted details/private attachment, 16 queue/scope tests and HTTP review passed. |
| R-026 | pp.7–8,13–14 | Durable rejection, separate business/inspection states and correction | 03 | TESTED | Versioned rejection snapshot, approval invalidation, matching-byte L0, fresh challenge/new bytes, preserved review history; 19 workflow and related race/restart tests; actual HTTP recovery passed. |
| R-027 | pp.11–14,18 | Safe submission replay and bounded provider recovery | 03 | TESTED | Session/request-bound hashed operation keys, immutable runs/results, three explicit retries, stale result discard, no mode fallback, no reanalysis of success/rejected/schema-invalid evidence; 21 recovery tests plus races. LIVE billing guard tested with stub only. |
| R-028 | pp.8,13–14,17 | Concurrent workflow cannot restore obsolete authority | 03 | TESTED | 12 new concurrency/rollback tests plus all old races preserved: approve/reject orderings, two uploads, same key, rejection during analysis, recovery vs invoice/policy/expiry/assignment/new evidence. SQLite only. |

Requirements can be refined, but no item may be marked TESTED without a runnable test or inspected artifact. DEPLOYED requires an independently accessed working endpoint. `READY`/`PLANNED` does not mean functioning.
