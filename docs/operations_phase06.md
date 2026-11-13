# Native local operations

Use an existing Python environment and built frontend. The reviewed script command
uses a per-process execution-policy option; system policy is not changed. No automatic install,
download, cloud CLI, Docker or Administrator requirement. From a clean PowerShell:

```powershell
Set-Location D:\project\sentinel_ladder_v2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Preflight
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Start -AcknowledgeCanned -OpenBrowser
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Backup
```

Without -AcknowledgeCanned, ordinary MOCK_AI remains UNKNOWN. The explicit switch
reuses Phase 05's unsafe-then-valid canned observer, not image interpretation.
Start returns its unique isolated root and loopback URL, with no password/token.
Default port 8018; -Port 0 chooses a free ephemeral loopback port. Occupied ports
fail; no unrelated process is killed. A saved private last-run pointer makes
Status/Stop work in another shell without session variables. Concurrent operators
should pass -RunRoot explicitly rather than rely on the last-run convenience pointer.

New roots are below .venv/phase06-demo-* (packaged copy: .runtime/phase06-demo-*).
Credentials are random in data/credentials.local.json, privately inherited from
the generated owner/SYSTEM-only Windows ACL (POSIX mode 0700). This changes only
the new demo directory, never system permissions. Read locally, never copy into a
report/screenshot/command argument. Demo listening lifetime is at most one hour;
credentials are not production accounts and expired roots cannot be served again.
Shutdown preserves data, logs and evidence. Fresh Start is the supported reset.

Resume an owned non-expired stopped root without provisioning users again:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Start -RunRoot '<exact root printed by Start>' -Resume -AcknowledgeCanned
```

Root identity/lease and private per-instance HTTP control prevent stop-by-stale-PID.
Stop is graceful; if pending it reports failure rather than force-killing. A crash
releases the OS lease; retry Resume only after inspecting status/port and allowing
an interrupted startup grace period. Existing pending/orphan media limitations
remain: do not claim cross-filesystem/SQLite crash atomicity or automatic repair.

Stopped Backup uses SQLite's backup API and copies matching private media/fixture
files to a new private phase06-backup-* root, with integrity_check. It refuses
an active lease or unstopped state. No destructive restore is automatic: preserve
the stopped original and backup, review matching code/schema before a manual restore
into a new isolated root. Never overwrite normal backend/local.sqlite or media.

Readiness /readyz proves a SQLite transaction can start, media probe is writable
and exact compiled assets remain available. /healthz is liveness only. Neither
proves cloud durability, future disk health, backup recoverability or industrial
safety. Public responses contain only readiness status or existing health metadata.
The private operator endpoint returns instance identity only with its separate
operator secret; it grants no business role, policy or payment authority.

Native package commands (output/destination must be fresh):

```powershell
.\.venv\Scripts\python.exe -m backend.tools.release_package build --package .venv\sentinel-phase06.zip
.\.venv\Scripts\python.exe -m backend.tools.release_package verify --package .venv\sentinel-phase06.zip
.\.venv\Scripts\python.exe -m backend.tools.release_package extract --package .venv\sentinel-phase06.zip --destination .venv\phase06-extracted
```

An extracted copy excludes .venv: pass -PythonPath with an existing compatible
environment to its scripts/Demo.ps1. This is a native source+static bundle, not
a self-contained Python runtime/container/cloud image. Source checksums are not
signatures or tamper-proof guarantees. No package auto-installs its requirements.

Failure recovery: dependency/build missing -> build/install explicitly using
frontend README; occupied port -> choose another port, never kill unknown owners;
unready storage -> stop and inspect the isolated root, preserve data; missing media
-> correction/review, no fabricated observation; network ambiguity -> refresh and
explicit exact operation replay; stale version -> reload/re-review; failed security
run -> keep gate BLOCKED. A frozen live provider is never a fallback.
