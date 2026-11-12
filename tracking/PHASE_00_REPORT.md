# Phase 00 acceptance record — 12 November 2026

Local gate: **PASS** on Windows / Python 3.14.7. **Phase 01 awaits user approval.**
All available Phase 00 tests executed: **113 passed, 0 failed, 0 skipped**, one
Starlette deprecation warning, 0.70 seconds reported by pytest. Coverage was not
measured. CI has not executed. Python 3.11/3.12 validation is unavailable locally.

Branch: `master`, no commits. Repository was already initialized; no git init,
staging, commit, push, remote configuration or deployment was performed.

## Files created

- `.gitignore`, `.env.example`, `pyproject.toml`, `README.md`
- `.github/workflows/tests.yml`
- `backend/__init__.py`, `backend/requirements.txt`
- `backend/app/__init__.py`, `models.py`, `policy.py`, `config.py`, `main.py`
- `backend/tests/conftest.py`, `test_policy.py`, `test_config.py`, `test_api.py`, `test_security.py`
- `policies/maintenance_v1.json`, `fixtures/synthetic_cases.json`
- `frontend/README.md` (placeholder only)
- `docs/architecture.md`, `docs/security.md`, `docs/decisions.md`
- `tracking/EXECUTION_LOG.md`, `tracking/PHASE_00_REPORT.md`
- Local ignored `.venv/` with installed dependencies

Modified existing files: `tracking/STATUS_LEDGER.md`,
`tracking/REQUIREMENT_MATRIX.md`. Original instructions, contracts and references
were preserved. Git began with every supplied file untracked, so Git cannot
distinguish these modifications from additions relative to a baseline commit.

## Acceptance evidence

Requirement mapping: R-001 completed; R-002, R-009, R-017, R-020, R-024 have
Phase 00 evidence and remain IN_PROGRESS where later phases are necessary.
The execution log contains actual commands and test stdout, including failures
of setup/inspection commands and their recovery. No test failures occurred.

| Suite | Result | Meaning |
|---|---|---|
| Pure policy | 85 passed | Positive L2 path plus negative/edge/action checks |
| Configuration | 19 passed | Invalid config/context denied, file errors explicit |
| API | 8 passed | Health/docs/schema, absent business routes, read-only health |
| Isolation | 1 passed | Separate interpreter evaluates ALLOW L2 with network/API/provider imports blocked |
| Localhost Uvicorn smoke | health 200, docs 200 | Actual running HTTP server; schema lists only `/healthz` |
| Dependency consistency | passed | `pip check`: No broken requirements found |
| Remote CI / Python 3.11,3.12 | NOT RUN | No remote push; interpreters not installed |
| Gemini / E2E / concurrency / cloud | NOT IMPLEMENTED | Outside Phase 00, no results claimed |

All policy inputs were **SYNTHETIC**. Tests exercise source-label values including
MOCK_AI/LIVE_GEMINI/RECORDED_LIVE to verify they do not grant authority; they do
not represent actual provider runs. No model adapter or benchmark was built.

## Verified security invariants

- Valid fixture earns L2 invoice preparation for review; engine does not deny all inputs.
- Matching asset and active challenge permit L1 with incomplete measurement; L0 cannot record visits or prepare invoices.
- Unsafe pressure or expired tag creates SAFETY_ALERT, at most L1; stale challenge keeps it L0.
- NaN/infinity/negative/non-numeric values fail closed; unknown units never convert implicitly.
- Missing/uncertain/conflicting fields cannot earn L2; bounds and date/expiry semantics are explicit.
- Observation authority fields are rejected; source labels cannot confer L3. Simulated completion is always denied.
- Tenant/job/asset/policy-version context mismatch fails closed; this is consistency checking, not authenticated tenant isolation.
- Policy evaluation works without FastAPI, network, provider SDKs or database and has no hidden clock.
- Unexpected exceptions return generic DENY/L0; no payload or exception text is exposed.
- Business and fixture injection routes are absent; only public operational/documentation routes exist.

## Risks and limitations

High: authenticated RBAC/assignment, unpredictable bound server challenges,
versioned cases/evidence, atomic human approval and concurrency controls are not
built. The pure engine must not be exposed as sufficient actor authorization.
Media authenticity, independent sensor truth and Gemini semantic correctness are
not tested; no photos or real observations were processed. The pump range is
invented, not safety guidance. No database, persistence, private media or audit
trail exists. No real-world detection metric is supported by this test count.

Medium: only Python 3.14.7 and the current local environment were executed.
3.11/3.12 CI is scaffolded but unverified. Starlette emits a deprecation warning
for the installed HTTPX TestClient; tests pass and the warning is retained in the
log. A future dependency update should migrate the test client deliberately.
The supplied PDF and reference differ in extraction reading order; relevant
original PDF sections were consulted directly.

Changes and rollback: new foundation files only plus two tracking updates.
Stop the server, review this manifest, restore tracking docs from a saved copy,
and remove only the created files if rollback is requested. No baseline commit
exists, so avoid destructive Git cleanup. No rollback was executed. The temporary
smoke server was stopped after identity inspection because terminal Ctrl+C did
not terminate the tool-owned Windows process.

Exact Windows setup/start/test commands are in `README.md`; no activation,
credentials, Docker, UI or cloud resource is needed. This record ends at Phase 00.
