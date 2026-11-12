# PHASE 01 — Verified cases, identity, challenges, atomic state

Read Master Book chapters 3–4,6,9–10,12 and chapter 23. Preserve all Phase 00 tests. **Execute and test this phase only.**

## Build
- SQLite + SQLAlchemy persistence (local), repository interface capable of later Firestore adaptation. Tables: tenants, users/roles, jobs, cases, challenges, evidence metadata, policy versions, approval events, append-only logical decision events. Include schema migration mechanism if possible; don't introduce a distributed architecture.
- Local demo authentication with independently identifiable contractor/manager/engineer accounts, safely hashed passwords and session/token handling. All server endpoints check tenant ID, job assignment and role. Test two separate fictional tenants. No shared admin password as a pseudo-role.
- Manager creates job/case with authoritative expected asset ID, explicitly fictional versioned policy, assigned contractor, mock INR 5000 invoice. Contractor sees assigned jobs, requests a time-limited server-generated cryptographically unpredictable challenge bound to job, asset, session and tenant; attempt limits and expiry use server clock.
- Implement case retrieval and named action evaluations, with **independent** `inspection_status` and `max_permission`. Build minimal actions: `CREATE_DRAFT`, `RECORD_PROVISIONAL_VISIT`, `PREPARE_INVOICE`, `COMPLETE_SIMULATION`.
- Manager-only mock sign-off, allowed only when current case is L2-eligible, bound to reviewer identity, evidence digest+version, amount, approved policy version and expected case version. Use actual atomic transaction / optimistic compare-and-swap; cases with stale version fail and approvals never resurrect.
- Add internal-only fake observations in tests via dependency injection/factory. DO NOT create a production-accessible endpoint that directly lets a contractor invent accepted observations.
- Health, identity/login/logout, jobs/cases/challenges, action and approval APIs with stable reason codes; document route map. Prefer chapter 10 `/v1/...` naming.

## Must-run tests
- Valid fictional observations -> L0/L1/L2 progression (using test-only injection), but L3 ONLY via authorized manager review.
- Wrong asset, placeholder `N/A`, expired challenge, missing/wrong unit and unsafe reading stay restricted with clear reason.
- Contractor direct API POST to manager approval denied; engineer approval denied; cross-tenant read/write denied; contractor cannot view unassigned job.
- Change amount/evidence/policy version invalidates approval; simultaneous approval/evidence replacement demonstrates no lost update; stale `expected_case_version` rejected; idempotent mock completion.
- Evidence-derived fake `permission_level=3` ignored and never persisted as authority.

## Completion gate
- Report running backend and accessible `/docs`, list real endpoints with examples, pytest output and simulated flow.
- Mark status only for actually verified auth/transaction work, not evidence upload or Gemini.
- No UI polish, red-team feature, cloud, or payment API. Stop and wait for approval to proceed to Phase 02.
