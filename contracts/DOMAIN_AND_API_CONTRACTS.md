# Proposed domain and API contracts — pre-build design reference

Derived from Master Book pp.7–16 and Appendix A. **Nothing here is an implemented endpoint.** Codex may refine names/types with ADR and tests while preserving the listed invariants. Source of truth remains PDF.

## Domain state: explicitly separated
- `inspection_status`: `EVIDENCE_MISSING`, `OBSERVATION_PENDING`, `EVIDENCE_COMPLETE`, `SAFETY_ALERT`, `REVIEW_REQUIRED`, `APPROVED_BY_HUMAN`.
- `max_permission`: integer `0..3`. `L0` create draft/request evidence; `L1` record provisional visit; `L2` prepare mock invoice FOR review; `L3` simulated completion after authenticated current-state human approval.
- Never derive `L3` directly from visual evidence. `SAFETY_ALERT` and `REVIEW_REQUIRED` **restrict**, never increase permissions.
- `decision`: `ALLOW`, `DENY`, `NEEDS_REVIEW`; include stable `reason_codes`, never just a model-written verdict.

## Typed observation schema (example, not guaranteed Gemini reading)
```json
{
  "asset_id_observed": "PUMP-042",
  "challenge_text_observed": "example-visible-string",
  "pressure_value": 34.5,
  "pressure_unit": "PSI",
  "equipment_status": "RUNNING",
  "calibration_expiry_date": "2026-12-31",
  "observed_at": null,
  "uncertain_fields": [],
  "supporting_frames": [],
  "model_provider": "MOCK_AI",
  "model_version": "mock-v1"
}
```

All uncertain/missing numeric/date fields should be `null` or explicit `UNKNOWN`; never fabricate values. An observed timestamp is NOT an authenticated capture timestamp. Do not ask the model for `authorized`, `tier`, `fraud_proved`, or `payment_approved`.

## Versioned case and action
```json
{
  "tenant_id": "org-demo-a",
  "case_id": "generated-uuid",
  "job_id": "job-001",
  "asset_id_expected": "PUMP-042",
  "invoice_amount_inr": 5000,
  "policy_id": "fictional-pump-inspection",
  "policy_version": "1.0.0",
  "evidence_version": 1,
  "case_version": 4,
  "inspection_status": "EVIDENCE_COMPLETE",
  "max_permission": 2
}
```

All demo thresholds come from a versioned fixture marked **FICTIONAL/NOT INDUSTRIAL SAFETY GUIDANCE**. Normalize units only with explicit conversion; reject unknown units, NaN/Infinity, invalid/negative values as required by case-specific policy. Define inclusive/exclusive boundaries explicitly.

## Approval binding
Bind review to `{tenant_id, case_id, job_id, action, invoice_amount, evidence_sha256, evidence_version, case_version, policy_version, reviewer_id}`. Perform permission evaluation and approval update atomically. Changing evidence/policy/amount/challenge validity or critical job metadata voids current approvals. `expected_case_version` / optimistic concurrency required. Don't turn case version into an immutable claim.

## API: align with Master Book p.14
First implement `/healthz`, `/docs`, and the case/action path. Proposed full MVP routes:
- `POST /v1/cases` — create case, issue fresh session-bound challenge (enforce authenticated manager and tenant scope).
- `GET /v1/cases/{id}` — tenant/role scoped case state and decision.
- `POST /v1/cases/{id}/evidence` — private media intake, eventually Gemini processing.
- `POST /v1/cases/{id}/actions/evaluate` — decision for named action.
- `POST /v1/cases/{id}/approvals` — independent authenticated manager approval.
- `POST /v1/redteam/run` — engineer-only labeled synthetic benchmark, isolated from production.
- `POST /v1/redteam/suggest` — engineer-only Gemini suggestion (not independent label, not live policy edit).
- `POST /v1/cases/{id}/evidence/fixture` — **local test-only and disabled by default** if used; ideally keep fixture injection in tests instead of public API.

Additional necessary supporting routes (document design choices): `/v1/auth/login`, `/v1/auth/logout`, `/v1/me`, `/v1/jobs`, `/v1/jobs/{id}`, `/v1/jobs/{id}/challenges`, `/v1/cases/{id}/audit`, `/v1/alerts`. They must enforce authenticated identity, tenant isolation, assignment and role checks. CORS/cookies/CSRF must be designed together. Manager cannot become engineer through a tab.

## Provider interfaces
```python
class PerceptionProvider(Protocol):
    async def inspect(self, media_ref: str, task_context: dict) -> Observation: ...

class AdversarialProvider(Protocol):
    async def suggest_cases(self, policy: dict, known_failures: list) -> list: ...
```
Implement `MockPerceptionProvider` and `GeminiPerceptionProvider`. Policy module imports neither provider SDK. Provider outputs are validated data only. Future Gemma is an unimplemented adapter option.

## Storage and audit
- SQLite local via SQLAlchemy with safe concurrent transactions, no whole-object lost updates.
- Firestore production behind repository interface where feasible; atomic transaction for approval binding; access authorization in FastAPI, not only Firestore security rules.
- Private Cloud Storage media when deployed; local private folder for development.
- Append-only logical `decision_events` with actor, action, evidence hash/version, policy version, time, decision/reason. Do NOT claim cryptographic immutability.
- Red-team alerts include policy version, expected and actual decision, testcase ID, owner, severity, safe restricted evidence reference; no raw customer media in webhook.

## Security boundary test to illustrate
An attacker can submit a schema-valid model observation with `pressure_value=999.0` and `pressure_unit=PSI`. The backend must use approved, configured case-specific thresholds and return `SAFETY_ALERT` or `NEEDS_REVIEW` rather than promoting to L2. A simple `reading_visible=true` is forbidden as a policy substitute.
