# PHASE 00 — From zero: repository, pure policy, failing/negative tests

Read `AGENTS.md`, Master Book PDF/text pp.1–5,7–8,17–20,25–29, and `contracts/DOMAIN_AND_API_CONTRACTS.md`. Treat these as unimplemented requirements. **Implement code now; this is not a planning-only request.**

## Scope — first 0–6h engineering slice (Master Book chapter 21)
1. Initialize the **new** repository tree (`backend/app`, `backend/tests`, `frontend` placeholder, `policies`, `fixtures`, `docs`, `.github/workflows`). If git already initialized, don't reinitialize destructively. Do not commit without authorization.
2. Python 3.11/3.12+ FastAPI, Pydantic v2, Python typing, pytest, reproducible dependencies (`pyproject.toml` or locked requirements), `README.md`, `.gitignore`, `.env.example` without secrets.
3. Implement a pure, network-independent `authorize()` and typed Observation/Policy/Decision classes. Separate `inspection_status` from L0–L3. Use a **clearly fictional** pump policy JSON configured per job; document its invented ranges as demo-only.
4. Implement `GET /healthz`, OpenAPI docs at `/docs`; no other feature need be a fake placeholder route.
5. Create passing pure policy tests covering missing observation, mismatched/placeholder ID, unknown units, invalid/NaN/infinite/negative readings, out-of-range values producing `SAFETY_ALERT`, boundary behavior, L0/L1/L2 separation, and impossible L3 from model output.
6. CI scaffold `.github/workflows/tests.yml` runs policy tests on push/PR; it must not need cloud credentials or Docker.
7. Document exact PowerShell setup, install, server start and pytest invocation. Use virtualenv's Python executable so PowerShell activation policy is not a blocker.

## Security rules
- No `reading_visible` as a substitute for typed pressure value/unit.
- Do not assume a photo proves actual safe equipment operation.
- No L3 without separately authenticated human approval (not built in this phase).
- No user-facing images, animations, React dashboard, Gemini SDK dependency, credentials, Firestore provisioning, cloud deploy.

## Done when (real execution)
- `pytest` passes negative and positive policy fixtures; no all-deny engine.
- `GET /healthz` tested and returns successfully.
- The policy can be imported and evaluated without starting FastAPI or contacting a model.
- Record exact commands and outcomes; update `tracking/STATUS_LEDGER.md` and matrix evidence paths; include diff/rollback note.
- STOP. Ask for user permission before Phase 01. If any test could not run, report BLOCKED rather than success.
