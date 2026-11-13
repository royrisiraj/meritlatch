# Phase 06 acceptance report — 13 November 2026

**Phase 06: PASS for its authorized local scope. Stop at the Phase 06 gate.**

| Independent verdict | Actual result |
|---|---|
| A. Local demo | **PASS / TESTED**. Real native Windows services, actual authenticated browser/business/engineering operations, three isolated timed visual rehearsals. Human spoken delivery **UNVERIFIED**. |
| B. Native deployment package | **PASS / TESTED**. Reproducible allowlisted source/static ZIP, safe environment, readiness, private runtime, verified extraction and final-archive HTTP smoke. Requires an existing Python environment; not a cloud/container image. |
| C. Remote deployment | **NOT ATTEMPTED**. Durable cloud adapters **BLOCKED/DEFERRED**; no remote endpoint, resource, cloud credential, billing or deployment. |

## Baseline and scope

Actual committed Phase 05 HEAD:
`92bd728fcf38bb59c9a09e633480042bd3dcb86a` (`completion of browser E2E`).
Initial `git status --short` was empty; `git diff --check` exited 0. Verified
`git log --oneline -8`; historical Phase 04 was 09bd8d1. No reset, clean, commit,
push or remote action. Authoritative PDF is 35 pages; relevant deployment/demo
sections were read from searchable text and original PDF pages 25–28. Actual
repository prompt: `prompts/06_CLOUD_AND_THREE_MINUTE_DEMO.md`; current pasted
authorization controls the expanded requirements. Earlier phase evidence remains.

| Executed gate | Before changes | Final | Evidence / exit |
|---|---|---|---|
| Complete backend pytest | 572 passed, 108.88s | **616 passed, 106.29s**, zero failed | PHASE_06_BASELINE_BACKEND_OUTPUT.txt / PHASE_06_BACKEND_TEST_OUTPUT.txt; 0 |
| Frontend Vitest | 36 passed, 18.25s | **42 passed, 6.09s**, zero failed | PHASE_06_BASELINE_FRONTEND_OUTPUT.txt / PHASE_06_FRONTEND_TEST_OUTPUT.txt; 0 |
| Original Chromium E2E | 6 passed, 32.3s | **6 passed, 25.3s**, zero failed | PHASE_06_BASELINE_BROWSER_OUTPUT.txt / PHASE_06_BROWSER_OUTPUT.txt; 0 |
| TypeScript + Vite production | 47 modules, 870ms | 47 modules, 684ms | PHASE_06_BUILD_OUTPUT.txt; 0 |
| Python dependencies | No broken requirements found | No broken requirements found | Baseline stdout and final pip-check output; 0 |
| npm advisories | Zero vulnerabilities | Pinned dependency files unchanged; final audit retained separately | PHASE_06_BASELINE_NPM_AUDIT.json / PHASE_06_FINAL_NPM_AUDIT.json |
| Prior source preservation | Hashes captured | **42 original test files, 15 protected files unchanged** | PHASE_06_BASELINE_TEST_HASHES.json / PHASE_06_SECURITY_CHECKS.json |

Actual full-suite stdout ends:

```text
616 passed in 106.29s (0:01:46)
Test Files  4 passed (4)
Tests  42 passed (42)
6 passed (25.3s)
No broken requirements found.
```

No tests disabled or weakened. Added 44 backend cases in three new Phase 06 files
and six frontend proxy-validation cases. The unchanged six browser tests are
separate from the three standalone demonstrations. Frontend unit/client tests
use mock fetch/jsdom; backend tests use actual SQLite/TestClient/native processes,
with explicitly injected DB/worker error cases. Rehearsals use actual Chromium,
TCP, auth, uploads, SQL and fixed synthetic worker executions, not mocked HTTP
success responses. Coverage was not measured. Remote CI **NOT RUN**; alternate
Python matrix runtimes were not locally executed.

## Architecture and implemented surface

Selected **one loopback Uvicorn process serving built React and existing FastAPI**.
No Vite process or Docker is required to present. SQLite and private media remain
on explicitly owned local disk; the launcher reuses unchanged Phase 05
`portal_demo.prepare` and its acknowledged canned observer.

See [deployment decision](../docs/deployment_decision_phase06.md) for the complete
persistence inventory: identities/password hashes, sessions/revocations/throttles,
tenants/assignments, jobs/cases/invoices, challenges, raw media/normalized transient
input, evidence/analyses/idempotency, approvals/reviews, simulated receipts/audits,
candidate/run/result/finding/proposal/review/gate histories, schema/config and
private historical Gemini files. Each group records ownership, access path,
atomicity/concurrency, confidentiality, retention/recovery and migration difficulty.
No private historical file is a deployment input.

Local Windows is selected; private single-machine staging with durable disk/HTTPS
is a future closest-fit option. Cloud Run needs an **external durable DB and
private object store**. One instance/concurrency=1 does not make ephemeral disk
durable. Firestore cannot execute existing SQL/CAS/constraints automatically;
Cloud SQL PostgreSQL also requires a real driver, schema/locking adapter and parity
tests. No adapter or infrastructure was installed. Migration, object/DB lifecycle
reconciliation, IAM/application-auth integration, retention/backups/recovery,
cost/access review and independent remote verification remain blockers. Gratuitous
Kubernetes/microservices were rejected. No exact price/free-tier assumption.

New endpoints in the **native wrapper only**:

| Route | Behavior |
|---|---|
| GET /readyz | Status-only 200 ready / 503 not_ready; SQLite transaction, media write probe and exact asset availability/integrity. Not future disk/cloud durability. |
| GET /login and known role SPA routes | Allowlisted compiled frontend/deep links; no private-directory fallback. |
| GET /assets/{built-file} | Exact known hash-checked JS/CSS only; changed/missing assets fail closed. |
| GET/POST /_local/control | Loopback-only, separate random operator token **and instance binding**, excluded OpenAPI; status/graceful stop only, no business authorization. |

Existing `/healthz`, `/v1/...` APIs and their authorization semantics stay intact.
The wrapper omits external-CDN Swagger UI, supplies CSP/no-referrer/frame denial
and preserves no-store/nosniff. Host is limited to localhost/127.0.0.1; Uvicorn
binds 127.0.0.1, one worker, proxy headers off, no permissive CORS. Dev proxy now
accepts loopback HTTP origins only. UI changes are two honest source notices;
no Phase 07 styling/polish.

`scripts/Demo.ps1` dispatches Preflight/Start/Status/Stop/Backup with explicit argv,
existing interpreter, no install, no secret in args/output, no unrelated-process
kill, saved last-run pointer and explicit root support. New private UUID roots only;
normal DB/media never overwritten. Windows DACL applies to **new roots only**
(owner rights/SYSTEM), POSIX mode 0700; no administrator or global ACL change.
Child environment drops credentials/proxies/live flags; `.env` is not loaded.
Random fictional credentials and root service expire after one hour. Resume is
explicit, preserves identities/sessions and refuses expired roots. An OS lease
prevents live backup/concurrent resume. Stop preserves evidence and data.

Backup requires stopped owned state, uses read-only SQLite source + backup API and
integrity checks, verifies media digests and copies matching private files to a
fresh private root. Missing source cannot create an empty database. No destructive
restore/reset or power-loss claim. Readiness is public but reveals no paths,
counts, tokens, exception or detailed config.

## Native package evidence

Final artifact (ignored local output): `.venv/phase06-native-final.zip`:

```text
PACKAGE_VERIFIED
52 files; 199828 bytes
SHA-256 24512bc1bc664d68d840b08c512835a6fc7e40942eb2d80842453384c8e5d396
base_commit 92bd728fcf38bb59c9a09e633480042bd3dcb86a
remote_deployment NOT_ATTEMPTED
```

Allowlisted Python/policy/fixed corpus, PowerShell script, built frontend and five
operator/architecture documents only. Fixed ZIP metadata/order and per-file SHA;
two-build equality is tested. Bounded verifier/extractor rejects extra files,
traversal, symlinks, payload changes and overwrite. Manifest records **worktree
packaged**, not a claim that new code is already committed/signed.

Excludes `.env`, credentials, sessions/DBs, raw/private media, historical Gemini
markers/results, screenshots, node_modules, runtime roots and caches. Explicit
fake canaries and strict path allowlist are tested. Exact-value scan of both tested
archives: **28 available private values, zero matches**. Reviewed working-tree
artifacts were also scanned; see security checks for final counts/limits. Exact
matching is not universal secret detection; digests are not signed provenance.

Three rehearsals used `.venv/phase06-native-rehearsal.zip`, 52 files, 198963 bytes,
SHA `596a6ca1400adaeadaba0114a6b1f3abf04afbeedf6edf870dbd2dd6d6c99037`.
The final archive differs only in operator/pitch/runbook documentation; packaged
Python, policies, corpus, scripts and compiled assets match the rehearsed archive.
Final archive separately verified/extracted and actually launched using its own
PowerShell script with the source interpreter: ready in **1.634s**, status READY;
health/ready/login 200, private `/v1/me` 401, `/.env` and unknown API 404, CSP
present. Graceful stop **0.311s**, stopped backup BACKUP_COMPLETE. See final smoke
stdout. No container recipe/image/run is claimed; Python runtime is external.

## Demonstrations and timed evidence

Each round extracted a fresh verified package and generated new isolated accounts
and fixture cards only. All job/case, evidence, rejection/correction, manager
approval, simulated receipt, worker runs, finding and engineering review/gate
transitions were actually executed during that round. Prepared positive perception
is **canned MOCK_AI**, security labels **fixed SYNTHETIC**, never LIVE_GEMINI.

Observed in each:

1. Authenticated manager assigns job/case L0; invoice denied. Actual invalid PNG
   decoder denial, then canned unsafe 999 PSI -> SAFETY_ALERT/L1.
2. Manager rejection -> L0; fresh challenge/different evidence -> L2. Assigned
   agent prepares invoice; separate manager reviews current exact binding -> L3.
   Agent records simulated completion; duplicate returns same simulated receipt.
3. Weak test-only candidate actually executes 38 scenarios: 36 pass, **1/26 false
   approvals**, **0/6 false rejections**, one separate review bypass; genuine A02
   finding and BLOCKED gate. Counts are synthetic, not field accuracy.
4. Safe candidate actually passes **38/38**, 0/26 false approvals, 0/6 false
   rejections. Author self-review denied; distinct authenticated engineer reviews
   exact candidate/run/corpus and yields READY_FOR_MANUAL_RELEASE, published=false.
5. Ordinary stop/resume preserves case/evidence/session/audit/receipt. Invoice
   change removes obsolete approval (L2); stale approval 409, contractor/engineer
   approval 403, other tenant/unassigned access 404. Graceful stop and backup.

| Rehearsal | UTC start -> finish | Total seconds | Pitch visual actions seconds | Result |
|---|---|---:|---:|---|
| 1 | 05:52:17.841 -> 05:52:38.723 | 20.882 | 11.695 | PASSED |
| 2 | 05:52:39.190 -> 05:52:59.540 | 20.350 | 11.756 | PASSED |
| 3 | 05:52:59.933 -> 05:53:19.728 | 19.795 | 11.359 | PASSED |

All on 2026-11-13. Total includes native startup, reliability/denial checks,
ordinary restart, cleanup and backup; pitch action interval excludes startup and
post-pitch reliability checks. No step exceeded its recorded budget; no unexpected
browser/page error; no failed action. No between-round configuration changes were
needed. [Redacted per-step records](phase06_evidence/rehearsals.json),
[actual stdout](PHASE_06_REHEARSAL_OUTPUT.txt). These are standalone Chromium
workflows, **not three reruns of a pytest file**.

Supplementary read-only resume visited the actual persisted weak-run detail:
SYNTHETIC SECURITY EVALUATION, 1/26 and 0/6 visible, source/version bound; screenshot
and load sample recorded. This was not a new regression or fourth complete pitch.

Recommendation: keep the 180-second script plan, role sessions prepared before
the clock, and genuine denial/independent-review/unpublished proof. Human narration
has **not been observed or timed**. If regression is slow, display honest pending
state then explicitly labeled previously executed SYNTHETIC run with stored IDs;
never pretend stored output just ran. See [pitch](../docs/pitch_phase06.md),
[operator runbook](../docs/demo_runbook_phase06.md), and
[compact evidence package](phase06_evidence/README.md). Five screenshots are actual
local app captures, reviewed for secrets. No video, invented biography/traction/
market size/ROI/score. Book-recorded criteria distinguished from unverified current
event rules; live Google AI criterion remains unproven.

## Performance and failure review

Windows 11 build 26300 x64, Python 3.14.7, Node 24.20.0/npm 11.19.0,
Chromium 158.0.8127.18. CPU reports AMD64 Family 25 Model 97 Stepping 2,
32 logical processors. CIM CPU/memory queries were denied; RAM not measured.
Serial local fictional sample only, no stress/load/SLA/cloud-latency claim.

| Measurement | n | Min / median / max |
|---|---:|---|
| Native readiness (includes compiled frontend availability) | 3 | 1.617 / 2.200 / 2.221 s |
| Login browser HTTP | 15 | 88.836 / 99.879 / 141.568 ms |
| Job list browser HTTP | 3 | 3.960 / 4.157 / 4.979 ms |
| Evidence HTTP (six accepted + three decoder denials) | 9 | 11.296 / 27.200 / 42.493 ms |
| Manager review GET | 18 | 5.423 / 10.450 / 13.852 ms |
| Manager approval POST | 3 | 15.260 / 17.820 / 19.734 ms |
| Complete synthetic run HTTP | 6 | 2.246 / 2.361 / 2.662 s |
| Finding retrieval | 12 | 5.245 / 6.368 / 8.958 ms |

Browser request timing includes response transfer, not pure server CPU time.
Single supplementary login screen ready: 73.290ms, DOMContentLoaded 33.4ms, load
33.9ms; n=1 only. Bundle: index 404B, CSS 9224B, JS 312219B (build reports gzip
JS 96.81kB); no cloud performance extrapolation. Full samples in performance.json.

Failure verification: original browser suite injects unavailable backend/network
and lost-response upload, checks UNKNOWN ordinary mock, duplicate replay, invalid
login/revocation, wrong roles/tenants/unassigned access and stale state. Backend
suite covers challenge expiry and evidence/invoice/policy/CAS races; security tests
cover rejected/stale reviews and failed/unfinished runs. New tests add real removed
frontend/changed asset/unwritable media path, occupied port, bad config, native
control mismatch, live backup conflict, restart and missing backup source. Explicit
DB exception and RUN_TIMEOUT injections fail readiness/gate closed. No existing
user data was corrupted. [Test mapping](SECURITY_TEST_CATALOG.md).

Initial new focused execution was **3 failed, 40 passed (13.93s)**. Tests exposed
missing policy module in initial package and stop accepting mismatched instance
before identity validation. Corrected allowlist and verified instance **before**
side effects; focused rerun 43 passed (13.47s), then a further missing-backup-source
test plus full 616 passed. Initial ZIP/logs preserved, not reused as accepted
artifact. Default PowerShell Restricted policy initially blocked the script;
documented per-process `-ExecutionPolicy Bypass` fixed invocation without global
policy changes. Initial Set-Acl approach failed SeSecurityPrivilege; new-root-only
DACL WinAPI correction works without administrator. Supplementary Node file access
needed the sandbox exception; successful actual browser result retained. No
speculative provider change or test weakening.

## Security, limitations and rollback

Preserved server roles, tenant/assignment, pure deterministic policy, separate
inspection/L0–L3, exact evidence/policy/invoice/reviewer/challenge approval binding,
version conflicts/concurrency, current-state action checks, challenge expiry,
safe private media, session revocation and independent engineering release review.
LLM/fixture/CLI/UI never obtains approval/policy authority. No observation-injection
API. One-hour isolated demo credentials are not production identities.
Audit is logically append-only, not tamper-proof. No real payment/equipment control.

Gemini adapter/settings/key files, guarded consumed marker and historical result
hashes unchanged; **zero new inference/list_models/network diagnostic/provider
credential use**. No fabricated LIVE_GEMINI. No model fallback. Freeze continues
through completion of 07 and separate authorization.

Remaining risks: no live perception proof or real equipment/customer validation;
no HTTPS/public hosting/production IdP/MFA/distributed rate limit; local filesystem
retention/backups remain operator responsibility. Media/DB commits are separate;
abrupt crashes can leave pending analyses/orphan bytes, not obsolete authorization.
Ordinary restart tested, not power-loss recovery; backup integrity tested, not a
destructive end-to-end restore. Session token is memory-only; page reload requires
login. Canned optical values are not image interpretation. One-hour fixtures must
be regenerated for a later talk. Cloud migration/production concurrency/load/
independent security review/remote CI and human spoken delivery remain unverified.

Rollback: stop the exact owned demo root gracefully and preserve all isolated DB,
media, backup and rehearsal outputs. No normal schema/data migration was performed.
Review the final file manifest against baseline before selectively reverting only
Phase 06 source/docs; no automatic Git reset/clean/delete or data overwrite. Keep
the private historical marker consumed. Test baseline again after any later
reviewed rollback. No rollback executed.

Full commands/results and final file status: [EXECUTION_LOG](EXECUTION_LOG.md),
[final Git status](PHASE_06_FINAL_GIT_STATUS.txt),
[exact changed-file manifest](PHASE_06_FILE_MANIFEST.json).
Final status: **11 modified tracked files and 51 new files**, all uncommitted;
no staged/deleted files. Reviewed-artifact exact-value scan: 62 files, zero
matches. All 13 changed/new Markdown documents' local links resolved, evidence
checksums matched, and final `git diff --check` exited 0 (only CRLF-conversion
advisories). The three rehearsal roots and the separately owned source/final
smoke roots were confirmed STOPPED. Windows owner ACLs required separate account
contexts for these read-only checks; no permissions were widened to bypass them.
CI files cover locked frontend install/audit/unit/build/Chromium/native package and
original Python matrix; no secret or deployment steps. Local equivalents ran;
remote CI NOT RUN. No paid resource/model, deploy, commit/push or Phase 07 work.

Recommend reviewing and then committing this Phase 06 checkpoint; **no commit was
created**. Separate user authorization remains required for Phase 07 or deployment.

## Exact Windows operator commands

```powershell
Set-Location D:\project\sentinel_ladder_v2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Preflight
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Start -AcknowledgeCanned -OpenBrowser
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Demo.ps1 -Action Backup
```

Use `-Port 0` if 8018 is occupied, or another available loopback port. To target a
specific concurrent/restarted demo, pass `-RunRoot '<exact root printed by Start>'`.
Read generated private credentials locally at that root's `data/credentials.local.json`;
never put them in public logs/screenshots/arguments. Existing .venv and compiled
frontend required; [operations](../docs/operations_phase06.md) covers extraction,
explicit existing `-PythonPath`, resume, one-hour expiry and safe failure recovery.
