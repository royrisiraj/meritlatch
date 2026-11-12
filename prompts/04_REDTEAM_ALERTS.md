# PHASE 04 — Independent adversarial assurance and engineering alerts

Read Master Book chapter 11 (pp.15–16), chapter 15 (p.20), chapters 12–13 and Appendix B. Ensure the main case workflow still works. No automatic production code mutation.

## Build
1. An isolated engineer-only policy test runner with a fixed, reviewed synthetic dataset containing legitimate and malicious/invalid cases. Record independent expected decision and distinguish baseline intentionally weak rule pack from approved current rules.
2. `POST /v1/redteam/run`: returns versioned test run with dataset size, source, policy version, result matrix (false approvals, false rejections, true approvals/rejections), and actual reproduction references. Avoid bogus security percentages.
3. `POST /v1/redteam/suggest`: Gemini can suggest **candidate** edge cases, not their authoritative labels and not production patches. Deduplicate, schema-validate and place in `PENDING_REVIEW`. No new candidate counted in production benchmark until human-labeled.
4. Generate one **real reproduced** test failure under deliberately weak policy and a sanitized engineering alert with test ID, severity, expected-vs-actual, policy ID/version, owner, link to restricted record. Don't send full customer media or untrusted prompt text in alert.
5. Pre-release gate: a proposed policy version may be marked ready only if human-reviewed and the complete regression suite passes. Do not build an autonomous rule-writing agent. Implement basic release/audit states if feasible without CI complexity.
6. Document three audit triggers: mandatory policy pre-release; periodic scheduled / manual; targeted after suspicious/disputed case. Sampled post-checkout audits are a future practice **not** preventive controls for already completed actions.

## Test
- invalid case accepted by intentionally weak baseline, same case rejected by corrected test policy, legitimate case still accepted.
- false approvals and false rejections computed from independent labels.
- tenant/role restrictions, test runner isolation, alert dedup, redaction, sanitized data references.
- Gemini candidate isn't automatically accepted/released; employee review and CI gate cannot be bypassed.

## Gate
- Reproducible policy failure and proposed corrected outcome, **measured** test matrix, one safe engineering alert. Report run commands and test evidence.
- If Gemini suggestions cannot run, keep labeled suite operational and mark suggestion feature BLOCKED, not TESTED. Stop for approval before Phase 05.
