# Phase 05 functional portals

Phase 06 native demo alternative (existing dependencies and production build):

```powershell
Set-Location D:\project\sentinel_ladder_v2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Start -AcknowledgeCanned -OpenBrowser
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Stop
```

One loopback process serves compiled React and FastAPI. The isolated private root
is printed; credentials are never printed or embedded in the package. It does not
provision normal users. [Full operations](../docs/operations_phase06.md),
[runbook](../docs/demo_runbook_phase06.md), [Phase 06 report](../tracking/PHASE_06_REPORT.md).
The development-server workflow below remains available. Its proxy target now
accepts loopback HTTP origins only; native hosting needs no Vite proxy.

React/TypeScript/Vite/Tailwind, React Router, typed same-origin API client,
Vitest/Testing Library and Playwright. No role switcher, payment, live inference
or policy publication. [Architecture/API mapping](../docs/portals_phase05.md),
[execution report](../tracking/PHASE_05_REPORT.md).

Install the committed lockfile in Windows PowerShell:

```powershell
Set-Location D:\project\sentinel_ladder_v2\frontend
npm.cmd ci --cache ..\.venv\phase05-npm-cache
```

Backend terminal (ordinary MOCK_AI deliberately returns UNKNOWN):

```powershell
Set-Location D:\project\sentinel_ladder_v2
$env:SENTINEL_PROVIDER_MODE = 'MOCK_AI'
$env:SENTINEL_ALLOW_BILLABLE = 'false'
.\.venv\Scripts\python.exe -m backend.tools.manage init-demo
.\.venv\Scripts\python.exe -m backend.tools.manage create-user --tenant demo-a --username engineering_reviewer --role ENGINEER
.\.venv\Scripts\python.exe -m uvicorn backend.app.api:create_app --factory --host 127.0.0.1 --port 8000
```

Provisioning prompts for independent hidden passwords; existing accounts stay
unchanged. Login with demo-a/demo-b and a provisioned account. Managers select
real active assignees. SERVICE_AGENT has a restricted simulation form, not another
role's portal.

Frontend terminal:

```powershell
Set-Location D:\project\sentinel_ladder_v2\frontend
npm.cmd run dev
```

Open http://127.0.0.1:5173. Only `/v1` proxies to loopback port 8000. No CORS,
cookies or wildcard permission added. Tokens live only in memory: full reload
or a new tab requires login. SPA links preserve the active session. If logout
loses network connectivity, memory clears but server revocation is unconfirmed.
Contractor logout invalidates its challenge and current approval; keep a separate
logged-in contractor browser context while the manager reviews.

Tests and local production bundle (not deployment):

```powershell
Set-Location D:\project\sentinel_ladder_v2\frontend
npm.cmd test
npm.cmd run build
npm.cmd run e2e
```

E2E starts private Vite servers 5175/5176, FastAPI 8015/8016, fictional accounts,
SQLite and media in a new ignored `.venv/phase05-browser-*` root. Free those ports
first; existing servers are never reused. Chromium is required; if absent use
`npx.cmd playwright install chromium`. This session reused installed Chromium.
Screenshots/credentials stay in the ignored root. Traces are off to avoid saving
bearer headers. Never share or commit credentials.local.json.

Separate acknowledged positive demo, never normal application configuration:

```powershell
Set-Location D:\project\sentinel_ladder_v2
$phase05Demo = Join-Path (Resolve-Path .venv).Path ('phase05-demo-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -m backend.tools.portal_demo --root $phase05Demo --port 8015 --fixture unsafe-then-valid --acknowledge-canned
```

New independent random credentials for portal-a/portal-b are in the ignored demo
root for local use. In the frontend terminal set
`$env:SENTINEL_PROXY_TARGET='http://127.0.0.1:8015'` before `npm.cmd run dev`.
Default `--fixture normal-unknown` preserves ordinary mock behavior.

The acknowledged fixture supplies **canned MOCK_AI, not image extraction**: first
accepted evidence per case is unsafe 999 PSI, later evidence is canned 35 PSI.
Trusted test setup binds identifiers/challenge to the reserved upload; all actual
media decoder/hash/storage/session/version/policy checks still run. The UI labels
the canned model explicitly. No observation-injection HTTP route. Harness refuses
an existing root, never loads `.env`, never overwrites user data. Fictional data only.

Backend regression with the Windows writable-temp workaround:

```powershell
Set-Location D:\project\sentinel_ladder_v2
$phase05Temp = Join-Path (Resolve-Path .venv).Path ('phase05-tests-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $phase05Temp | Out-Null
$env:TEMP = $phase05Temp
$env:TMP = $phase05Temp
$env:TMPDIR = $phase05Temp
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp (Join-Path $phase05Temp 'pytest')
.\.venv\Scripts\python.exe -m pip check
```

Fresh GUID per pytest invocation. No ACL change, Docker, WSL, cloud account or
live inference required. Gemini stays deferred through Phases 05–07. Stop at 05.
