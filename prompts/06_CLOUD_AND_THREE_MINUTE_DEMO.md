# PHASE 06 — Deployment, reliability and judge-ready demonstration

Read Master Book chapters 20–23 and docs security/scale sections. Preserve all tests. **Do not provision paid cloud, grant public access, create secrets or deploy without explicit user approval and actual credentials.**

## Build/document
- Create a Cloud Run source-deploy plan (no local Docker). Backend FastAPI and built frontend can share one Cloud Run deployment to simplify demo; if using separate services, document CORS/auth ramifications and why it helps. Cloud Storage private media + Firestore case/event persistence only when actual resources/permissions available. SQLite cannot be trusted as durable production storage on Cloud Run.
- Secret Manager configuration, scoped service account, IAM plan; no keys in repo, screenshots or frontend. Lock down engineer/admin routes and fixtures. No publicly available synthetic evidence injection route.
- Add `/healthz` and smoke tests for auth, valid/invalid case, mock human approval and alert. Log request errors and model latency without raw client secrets or evidence.
- Account for Gemini quota/latency, API failures and local fallback **explicitly labeled**: `LIVE_GEMINI` vs `RECORDED_LIVE` vs `SYNTHETIC`. Never disguise prerecorded or mock as live.
- Repeat full demo three times, capturing actual evidence, errors and duration. Document measured latencies and limits or explicitly say they are not measured.
- Final 3-minute script follows chapter 22 timing: 0:00 problem, 0:25 L0, 0:50 incomplete, 1:20 valid to L2 + human gate, 1:50 red-team, 2:20 buyer, 2:45 close. Keep presentation consistent with what code actually does.
- Publish accurate status: `TESTED` only if executed locally, `DEPLOYED` only after external verification from a second device, no invented URL or Google model version.

## Gate
- All existing backend/frontend tests still pass.
- Deployment either genuinely verified **with permission** or honestly marked BLOCKED; never falsely treat Cloud Run examples as deployment.
- At least one real Gemini call, one valid plus two invalid submissions, separate human approval, a real generated test report and alert, if credentials/services permit; if not, record exact missing prerequisites.
- Report achieved demo evidence vs planned pitch; stop for approval before appearance improvements.
