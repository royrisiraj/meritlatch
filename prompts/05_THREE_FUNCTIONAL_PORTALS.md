# PHASE 05 — Three functional portals: workflow UX before design

Read Master Book chapter 3 (pp.6–7), chapters 9–10, chapter 21 and UI policy. Preserve backend tests. Build simple React/Vite/TypeScript/Tailwind frontend with accessible forms. Do not copy code/assets from UI reference sites or spend time on decorative effects.

## Deliver user journeys
- **Contractor**: authenticated session -> assigned job list -> server challenge -> upload -> obvious `LIVE_GEMINI`/`MOCK_AI` label -> observation and inspection status -> request resubmission. Contractor cannot change role by editing a tab or call manager API.
- **Manager**: authenticated case queue -> inspect submitted media and uncertainty -> display permissions L0–L3 and inspection status separately -> request mock invoice preparation at L2 -> independent review and simulated completion at L3. On stale state show refresh/re-review instructions.
- **Engineer**: authenticated tests and alerts -> see run metadata, failing case, expected-vs-actual, policy version, safe evidence ref; no raw PII by default; no edit-while-live button or manager approval access.
- Require reason codes, error/loading states, responsive layout and keyboard-accessible controls, but **no landing page, animations, complex visual charts or full design system**.
- Use typed API client and server-side auth; role-specific components are convenience only, never security enforcement. Use mock provider for deterministic E2E tests and clearly label fixtures.

## End-to-end acceptance
- Valid mock contractor submission -> manager sees correct evidence -> L2 invoice review -> separate manager L3 simulated approval.
- Two distinct invalid cases fail closed; unsafe PSI shows safety alert not permission escalation.
- Contractor direct API approval and cross-tenant read fail even if UI is manipulated.
- Engineer red-team flow reads real test run and real alert from Phase 04; no static decorative metrics.
- Frontend build and tests pass; backend suite stays green. Supply Windows PowerShell instructions for frontend/backend dev servers (no Docker).

## Stop condition
- **Functional** user journeys, screenshot/video after checking actual app, tested role permissions. Stop before Phase 06 and UI polish. Report flaws frankly.
