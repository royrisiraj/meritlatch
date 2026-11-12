# Security and workflow test catalog

Reference: Master Book chapters 4, 9, 12–15 and Appendix B. Create test implementation and label expectations independently of Gemini. These are **planned** tests; do not report passing totals until executed.

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
