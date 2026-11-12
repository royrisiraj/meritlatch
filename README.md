# SENTINEL//LADDER — Phase 02

Phase 02 adds authenticated JPEG/PNG evidence upload, bounded safe decoding,
private local storage, tenant-scoped exact-byte duplicate checks and untrusted
perception adapters. The existing case factory and pure policy remain the
foundation. See [media/Gemini contracts, configuration and commands](docs/media_and_gemini.md)
and [Phase 02 report](tracking/PHASE_02_REPORT.md).

`DISABLED` is the default provider mode. For a reproducible actual HTTP image
workflow without network inference:

```powershell
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase02
```

This uses a real image POST and a clearly labeled canned `MOCK_AI` observation.
The separate live Gemini check is BLOCKED pending explicit billable-call approval,
credentials and independently reviewed fictional input; no live success is claimed.

## Retained Phase 01 foundation

Authenticated local maintenance cases, SQLAlchemy/SQLite persistence, backend
tenant/job/role checks, unpredictable bound challenges, deterministic L0–L2
eligibility, and separate manager-approved **simulated** L3 completion.

All 266 Phase 00/01 tests are preserved unchanged. Current execution evidence is
in the Phase 02 report. Only Windows/Python 3.14.7 was executed; Python 3.11/3.12
and remote CI remain unverified. The Master Book PDF controls the product.

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

**Synthetic observation injection remains internal/test-only.** Phase 02 accepts
actual image bytes when an explicit provider mode is configured; HTTP cannot
inject observations. Normal settings refuse saved SYNTHETIC observations, and
MOCK_AI artifacts cannot masquerade as live results. No real-world verification
or live extraction accuracy is claimed.

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

No frontend design, actual live Gemini call, payment, cloud deployment or Phase 03
work was performed. Phase 02 ends at its gate; live verification remains blocked.
