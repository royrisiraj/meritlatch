# PHASE 03 — Complete backend case flow, versioning, human review

Read Master Book chapters 3–4,6,9–10,15. Preserve P0 tests and all previous results. Execute this phase ONLY.

## Build and connect the actual vertical slice
- Manager creates a case and job-specific policy; contractor gets challenge; contractor uploads real or explicitly labeled test media; Gemini/mock extracts observations; backend normalizes and independently evaluates policy; manager can inspect evidence/provenance and prepare/review mock invoice; independent manager review authorizes L3 SIMULATED completion.
- Resolve any transaction/data consistency gaps from Phase 01–02. Case mutation must include `expected_case_version`; evidence and approval state changes atomic. Replay/rate protections must be server-side. No L3 if challenge/evidence expired, mismatched, unsafe, or review not complete.
- Record append-only logical `decision_events` with actor ID, action, source mode, evidence SHA-256/version, policy version and reason codes. Do not claim Firestore/storage is cryptographically immutable.
- Build a CLI or Swagger-driven **repeatable** E2E script using only mock provider/consented test media, with exact expected L0-L3 transitions. Separate scripts for one valid and two invalid submissions.
- If there are two plausible meanings of a policy, choose the conservative interpretation and document an ADR; keep policy fixtures versioned.

## Required tests
- Unauthorized direct API calls never work despite frontend roles.
- Existing approval invalidated by media, policy, job or invoice update; concurrency and idempotency tests.
- Unsafe reading / expired tag -> `SAFETY_ALERT`, missing observations -> `REVIEW_REQUIRED`, no automatic approval.
- Model JSON cannot supply a direct permission; fail closed on unavailable model.
- The complete mock path reaches L3 only after manager approval. No actual payment or physical equipment control.

## Gate
- Three separately runnable API case scenarios, all planned P0 tests executed, stable audited decisions, exact PowerShell launch commands.
- Update requirement matrix/status ledger with links to tests. Stop and ask approval for Phase 04. Don't add landing pages or polishing.
