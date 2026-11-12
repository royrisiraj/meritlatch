# AGENTS.md — mandatory instructions for Codex

**SENTINEL//LADDER Master Book v2.0 is the controlling specification.** Read `reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt` (all relevant sections) and consult the original PDF if uncertain. Never treat an old starter ZIP, prior pitch deck or previous chat-generated score as implemented evidence. Project begins at zero.

## Non-negotiable behavior
1. Write **working code and runnable tests** for the CURRENT prompt only; stop after its gate. No invented execution, deployment, interview, benchmarks, screenshots, or Gemini results.
2. No real bank transfer, money movement, or equipment control. The INR 5,000 demonstration is **simulated**.
3. Gemini and other LLMs are untrusted observation/test-suggestion providers. Never give an LLM approval keys, agent-authorizing tools, write access to live policies, or authority to set permission levels. Responses matching JSON schema are still untrusted.
4. Pure Python policy decision point must operate without Gemini, network, UI, or Firestore. Model adapter must not import policy internals to escalate privileges.
5. Enforce server-side role/tenant/job authorization on **all** routes. Frontend view switching cannot authorize an action. Contractor cannot approve own work; engineer cannot approve invoice; manager cannot edit policy without engineering controls.
6. Use approval key bound to tenant, case, action, invoice amount, evidence SHA-256, evidence version, approved policy version, and authenticated reviewer identity. Evidence/policy/invoice changes invalidate approval. Prove atomicity with concurrency tests.
7. Separate inspection/evidence status from L0–L3 permissions. An unsafe numeric reading must create `SAFETY_ALERT`, never promote L2/L3. Missing/nonfinite/wrong-unit data fail closed. Avoid hard-coding a universal real-world safety PSI range.
8. Challenges: cryptographically unpredictable, short-lived, server-created, bound to tenant/job/asset/session. Challenge in photo is *supporting evidence*, not proof of media authenticity. Token cannot be set by client.
9. Media: verify content with safe decoder and bounded byte/pixel/frame limits; calculate exact SHA-256 and check duplicates within scoped data; handle EXIF/GPS as spoofable optional metadata; raw media stored privately. Never describe perceptual hash as tamper proof.
10. Local fixture mode is OFF by default and gated to development/test; visibly distinguish `SYNTHETIC`, `MOCK_AI`, `LIVE_GEMINI`, `RECORDED_LIVE` artifacts. Do not offer a public synthetic observation injection endpoint in production.
11. New Gemini-suggested attacks require **independent labels** before counting as failures. Keep isolated red-team runner separate from live policy; versions reviewed and regression-tested before any release. Measure both false approvals AND false rejections.
12. Notifications include redacted summaries/restricted references, not raw evidence, credentials or full untrusted payloads. Firestore is not an immutable ledger; use append-only logical events with accurate claims.
13. No hard-coded secrets. `.env.example` placeholders only; `.gitignore`; show config errors. Never log customer PII or keys.
14. Fail closed on provider errors, missing evidence, stale challenge, conflicts, stale approvals, and unexpected exceptions. Return reason codes and actionable user guidance.
15. No gratuitous microservices, blockchain, LangChain, GPU hosting, model self-training, speculative anti-deepfake certification, gratuitous dashboards, or landing-page work before acceptance gates.

## Source and sequencing
- Source: Master Book chapters 1–24 and Appendices A–E, especially pp.7–20,25–29.
- Use proposed API paths from chapter 10 as base; if choosing `/api/v1/...` rather than `/v1/...`, explicitly document and test a consistency rule or alias. Prefer `/v1/...` for direct alignment.
- Repo structure: `backend/`, `frontend/`, `policies/`, `fixtures/`, `docs/`, `.github/workflows/` as in chapter 23.
- Python 3.11/3.12-compatible FastAPI, Pydantic v2, SQLAlchemy/SQLite local (transactional) -> Firestore adapter at deploy time; Cloud Storage for private media if deployed. `google-genai` through provider protocol.
- UI Phase 05: React+Vite+TS+Tailwind, minimal working forms and accessibility; Phase 07 polish only after demo and tests pass.
- Codex in Antigravity integrated terminal or compatible extension. No unapproved commit, push, deploy, paid-resource provisioning, destructive operations, or credential use. Ask user for explicit permission before deploying or creating paid Google Cloud resources.

## Completion evidence per phase
- Actual command stdout/stderr, test count, failures, coverage if measured; identify **mock vs live**.
- At least one valid path and negative paths; never present a deny-everything model as successful.
- Explicit risk list; changes and rollback note; update `tracking/STATUS_LEDGER.md` with `PLANNED`/`IN_PROGRESS`/`TESTED`/`DEPLOYED` grounded in evidence.
- Stop at phase boundary and wait for user approval.
