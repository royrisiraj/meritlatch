# Codex phase acceptance / review template

Use this report after **each** Phase 00–07. Fill in actual evidence; keep unknown items `NOT TESTED`. A plan or AI-generated answer does not count as execution.

- **Phase:** 00 / 01 / 02 / 03 / 04 / 05 / 06 / 07
- **Branch / commit (if explicitly authorized):**
- **Changed files and why:**
- **Acceptance requirements:** list exact `tracking/REQUIREMENT_MATRIX.md` IDs
- **Commands actually executed:** command + environment (Windows local / CI / Cloud Run)
- **Unit tests:** command, count, pass/fail, exact stdout or file path
- **Integration tests:** command, count, pass/fail, exact stdout or file path
- **Role/tenant/concurrency tests:** outcomes, especially an expected DENY path
- **Model mode:** `MOCK_AI` / `LIVE_GEMINI` / `RECORDED_LIVE` / `SYNTHETIC`; do not merge metrics
- **Actual Gemini smoke result:** exact model ID + media type + latency + schema validation; or `BLOCKED (no credentials)`
- **Real-world benchmark / customer data:** not available until collected with consent
- **Cloud deployment:** not done / approved-and-tested / blocked; if tested, endpoint and second-device check
- **Security invariants checked:**
  - [ ] L2 requires complete approved observation + valid state
  - [ ] `SAFETY_ALERT` never promotes permissions
  - [ ] L3 never follows from model output alone
  - [ ] Wrong-role and cross-tenant requests denied by API
  - [ ] Stale approval cannot survive changed evidence/amount/policy
  - [ ] No unapproved production policy mutations
  - [ ] No secrets/raw media in public logs or alerts
- **Open defects and risk level:**
- **Decisions made / ADR references:**
- **Rollback procedure:**
- **Status ledger / requirement matrix updates:**
- **Final phase gate:** `PASS` / `FAIL` / `BLOCKED`
- **Next-phase authorization:** `AWAITING USER APPROVAL`

## Failure rule

If actual test output is unavailable, do not call the test passing. Do not move on simply because Codex says it implemented the feature. Ask for real command output and repeat failing scenarios.
