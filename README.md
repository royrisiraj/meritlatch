# SENTINEL//LADDER — Phase 01

Authenticated local maintenance cases, SQLAlchemy/SQLite persistence, backend
tenant/job/role checks, unpredictable bound challenges, deterministic L0–L2
eligibility, and separate manager-approved **simulated** L3 completion.

All 113 Phase 00 tests are preserved unchanged. The complete suite has 266 passing
tests locally. Only Windows/Python 3.14.7 was executed; Python 3.11/3.12 and remote
CI remain unverified. The Master Book PDF in `reference/` controls the product.

## Windows PowerShell startup

No activation, Docker or WSL is required:

```powershell
Set-Location D:\project\sentinel_ladder_v2
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m backend.tools.manage init-demo
.\.venv\Scripts\python.exe -m backend.tools.manage list-users --tenant demo-a
.\.venv\Scripts\python.exe -m uvicorn backend.app.api:create_app --factory --host 127.0.0.1 --port 8000
```

`init-demo` prompts for hidden, independently chosen passwords (12–256 characters)
for `contractor`, `manager`, `engineer`, and `service_agent` in each of `demo-a` and
`demo-b`. It prints IDs, never passwords. Existing accounts are unchanged. No
default credentials or automatic startup seeds exist. Keep this local server on
loopback. Stop it with Ctrl+C.

Browse `http://127.0.0.1:8000/docs`. Use `POST /v1/auth/login` with `tenant_id`,
`username`, and `password`, then paste the returned bearer token into Swagger's
Authorize control. Never put credentials in URLs, shell history or screenshots.
Roles and assignments are loaded from the database on each operation.

From another PowerShell terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/healthz
```

The persistent database defaults to `backend/local.sqlite`, ignored by Git.
Optional process environment settings:

```powershell
$env:SENTINEL_DATABASE_PATH = 'D:\project\sentinel_ladder_v2\backend\local.sqlite'
$env:SENTINEL_ENV = 'development'
```

`.env` is not automatically loaded. No Gemini/cloud key is required. Production
mode and environment-based synthetic enablement are rejected.

## Actual HTTP synthetic smoke

```powershell
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase01
```

This starts a real Uvicorn TCP listener on a temporary loopback port with a
temporary SQLite database and random ephemeral credentials. It demonstrates role
logins, case/challenge creation, missing-evidence denial, synthetic L2 eligibility,
contractor/engineer approval denials, manager L3 approval, idempotent completion,
invoice-change invalidation, audit and logout. It prints no credentials,
challenges or raw observations, then closes its server/database and removes its
temporary artifacts.

**Synthetic evidence uses an internal test factory, never an HTTP endpoint.**
Normal operation can create/review L0 cases and issue challenges. Media submission
and Gemini await Phase 02. Normal settings also refuse to promote saved test
artifacts. No complete media workflow or real-world verification is claimed.

## Permissions

The approved fictional template in `policies/maintenance_v1.json` is cloned per
job. Its inclusive `30–40 PSI` range is **FICTIONAL / NOT INDUSTRIAL SAFETY
GUIDANCE**. INR 5,000 is exactly `500000` integer paise; completion is simulated.

- L0: draft/evidence requests.
- L1: provisional visit with exact asset and active bound challenge.
- L2: prepare an invoice for manager review with complete compliant observations.
- L3: simulated completion after independent authenticated manager approval.

The pure policy remains capped at L2. The case service verifies the persisted
evidence, approval binding, versions and identities before granting L3.
Inspection status and permission remain separate.

See the [endpoint map](docs/api_phase01.md), [architecture](docs/architecture.md),
[security limits](docs/security.md), [decisions](docs/decisions.md), and
[Phase 01 report](tracking/PHASE_01_REPORT.md).
The unchanged `backend.app.main:app` is the Phase 00 health-only bootstrap;
**use the Phase 01 factory startup command above for business APIs**.

No frontend design, live Gemini, payments, cloud deployment or Phase 02 work was
performed. Phase 01 ends at its gate.
