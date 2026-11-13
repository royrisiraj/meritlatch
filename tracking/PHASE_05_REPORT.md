# Phase 05 functional product acceptance - 13 November 2026

**Verdict: PASS / TESTED - local functional MVP.** Backend **572 passed in
99.01s**, frontend **36 passed in 6.47s**, actual Chromium/HTTP **6 passed in
24.5s**, zero current failures. TypeScript/production build passed in 755ms.
All **562 earlier backend tests remain unchanged**. No live inference, real
payment, policy publication, commit, push, deployment or Phase 06/07 work.

## Baseline and authoritative inspection

Verified clean Git at **09bd8d1e9f5605d90aadd4a428a71a1587e29a12**, user's committed
Phase 04: independent red-team evaluation, findings and human-controlled gates.
Executed `git log --oneline -6`, `git status --short`, `git diff --check`; initial
status/diff empty. Baseline executed **562 passed in 84.17s**, log
[PHASE_05_BASELINE_OUTPUT.txt](PHASE_05_BASELINE_OUTPUT.txt). Captured all 36 old
Python test file SHA-256 values before source edits in
[baseline hashes](PHASE_05_BASELINE_TEST_HASHES.json).

Read AGENTS, Master Book PDF (35 pages confirmed) and relevant extracted chapters
3/4/9/10/21/23, original `05_THREE_FUNCTIONAL_PORTALS.md`, current attachment,
contracts, Phase 03/04 reports, ledgers/catalog, architecture/security/workflow/
assurance docs and relevant backend models/services/tests/tools. Generated and
inspected the actual initial OpenAPI (36 paths) in ignored local scratch state.
No earlier artifact or synthetic score was treated as a live observation.

## Architecture, installed stack and API integration

React **19.3.1**, React DOM **19.3.1**, React Router **7.18.5**, TypeScript **5.9.3**,
Vite **7.3.8**, React plugin **5.2.0**, Tailwind/Vite plugin **4.3.5**. Vitest
**4.1.12**, Testing Library React **16.3.3**, user-event **14.6.10**, jest-dom
**6.9.1**, jsdom **26.1.0**, Playwright **1.65.0**. Node **24.20.0**, npm **11.19.0**;
Python **3.14.7**/Windows. Exact transitive resolution is package-lock.json.

React components/forms, Router navigation, typed domain/client, reusable states,
responsive CSS/Tailwind, jsdom unit tests and real Chromium browser automation.
No large UI kit, chart/animation framework, SSR server, AI SDK or external asset.
No Python dependency or pinned baseline package changed. Initial Vitest 3 install
had three known vulnerabilities (one moderate, two critical). Inspected advisory
and patched-version compatibility; explicitly selected compatible 4.1.12, without
`audit fix --force`. Final [npm audit](PHASE_05_DEPENDENCY_AUDIT.json): **zero known
vulnerabilities**. This is a point-in-time advisory result, not universal safety.

Frontend structure: `src/{App,auth,api,domain,ui,main}`, `features/{jobs,cases,
engineering}`, styles, `test/`, `e2e/`, Vite/TS/Playwright configuration. The typed
client uses actual documented fields/OpenAPI; types are hand-maintained, not
generated or a complete runtime response-schema validator.

Full [architecture, endpoint map and decisions](../docs/portals_phase05.md).
Three justified small **read-only** additions: manager-only `/v1/assignees`,
assigned/tenant-scoped `/v1/jobs/{id}/cases`, engineer-only
`/v1/redteam/candidates/{id}/history`. Authenticated projections, bounded pages/
history and scope-checked cursors; no new mutation or authority. History honors
the existing assurance-factory flag. Existing mutation/media contracts retained.

Decisions preserving the Master Book: raw JPEG/PNG request bodies follow the
existing tested API rather than inventing multipart; SERVICE_AGENT remains the
only invoice-preparation/completion actor. Its restricted authenticated form does
not grant another portal's rights. Contractor logout invalidates its challenge;
positive review uses separate browser contexts with the contractor still logged
in, rather than weakening that session invariant to match a sequential story.

## Functional inventory and executed user workflows

| Portal | Implemented and actually verified |
|---|---|
| Shared | Real login/me/logout, role-specific navigation, tenant/user display, guarded routes, loading/empty/not-found/unauthorized/stale/network errors, separate inspection/business/L-level/source, public reasons/audit, accessible labels/focus/confirmations. Full reload requires login; no visual role switcher. |
| Contractor | Authorized jobs with actual case summaries/action hints/timestamps, job/case details, server challenge+expiry, real PNG upload/preview, decoder denial, unsafe L1, manager rejection L0, fresh-challenge/new-byte correction to canned L2, private evidence and observations, explicit lost-response replay and server-hinted mock recovery. |
| Manager | Real create/assign/template/amount/job-case operations, filtered cursor queue and loaded-page counts, current private media and observations/uncertainty/policy, invoice revisions, confirmed rejection/correction, exact-binding approval, persisted review/audit. Manager does not execute agent actions or claim payment. |
| SERVICE_AGENT | Restricted form using case ID/version supplied by manager; actual prepare_invoice at L2 and complete_simulated_action at L3, simulated receipt and idempotent replay. No job/manager/engineer portal access. |
| Engineer | Actual candidate create/revise, fixed backend run/results and per-scenario expected/actual, FAR/FRR denominators/N/A/review outcomes, findings filters/detail/reproduction/history, triage/proposal, author self-review denial, distinct reviewer approval, current bound history and gate, published=false. Gemini suggestions visibly unavailable. |

Browser business workflow: manager created PUMP-042 and assigned real fictional
users; contractor submitted invalid bytes (UNSUPPORTED_MEDIA_TYPE), then a safely
decoded fictional image with canned 999 PSI (SAFETY_ALERT/L1). Manager rejected
it (L0); contractor requested a fresh challenge and uploaded different bytes,
obtaining canned 35-PSI L2. Assigned agent prepared the simulated invoice; manager
approved exact current case/evidence/policy/invoice revision (L3); agent completed
simulation and repeated it with the same receipt. Backend GET confirmed COMPLETED;
public audit included actual action events. Contractor logout then invalidated
current L3. Previous rejected/approved history remained visible.

Browser assurance workflow: engineer A created weak and safe isolated profiles,
executed the actual subprocess SUT, inspected an A02 false approval and triaged
it, proposed a safe candidate, then was denied self-review. Separate engineer B
reviewed the exact executed safe run. Backend history confirmed the reviewer,
READY_FOR_MANUAL_RELEASE and published=false. Weak gate remained BLOCKED.
Safe **38/38**, weak **36/38**, one false approval **1/26** and one review bypass;
safe FAR **0/26**, FRR **0/6**. These are synthetic policy-regression measurements,
not image perception or production performance. Existing 562 tests retain the
overrestrictive candidate's false-rejection coverage.

Normal separate MOCK_AI browser server returned actual UNKNOWN/null observations,
REVIEW_REQUIRED and below L2, using mock-observer-v1. Positive observations came
only from acknowledged `portal_demo --fixture unsafe-then-valid`; its UI displays
`CANNED_DEMO_NOT_IMAGE_EXTRACTION` and a canned-data notice. Actual bytes still pass
normal decoder/storage/hash/binding/authorization checks. No fixture HTTP route,
arbitrary observation injection or invented LIVE_GEMINI observation was added.

## Test evidence, security and browser review

| Execution | Actual final result | Evidence |
|---|---|---|
| Pre-change backend baseline | 562 passed, 84.17s | PHASE_05_BASELINE_OUTPUT.txt |
| Complete backend regression | 572 passed, 99.01s, exit 0 | [backend stdout](PHASE_05_BACKEND_TEST_OUTPUT.txt) |
| Frontend mocked component/client/session | 36 passed, 3 files, 6.47s, exit 0 | [frontend stdout](PHASE_05_FRONTEND_TEST_OUTPUT.txt) |
| Real Chromium/React/FastAPI HTTP | 6 passed, 24.5s, exit 0 | [browser stdout](PHASE_05_BROWSER_OUTPUT.txt) |
| TypeScript + Vite production bundle | PASS, 47 modules, 755ms, exit 0 | [build stdout](PHASE_05_BUILD_OUTPUT.txt) |
| Dependency checks | pip check clean; npm audit zero known vulnerabilities | PHASE_05_PIP_CHECK_OUTPUT.txt / PHASE_05_DEPENDENCY_AUDIT.json |
| Preservation/secret/redaction | 36 old test files + 10 protected artifacts unchanged; no matching private secrets in 3 build assets or generated passwords/challenges in logs | [security checks](PHASE_05_SECURITY_CHECKS.json) |

Ten backend tests exercise all new read authorization, tenant/assignment/cursor/
projection/bounds. Existing 562 tests preserve pure policy, L3 binding, concurrency,
media and assurance semantics. Unit/client/component tests mock fetch/jsdom and
are not called full E2E. All six browser tests use actual local FastAPI, SQLite,
media and authenticated fictional accounts; authoritative responses/state are
asserted, rather than trusting UI success text. Test retries are **zero**.

Browser cases: (1) contractor/manager/agent correction-to-simulation; (2) independent
engineering finding/remediation/gate; (3) direct role/tenant/assignment denial,
stale invoice conflict/refetch and explicit failed network request; (4) normal mock
UNKNOWN and responsive widths; (5) actual upload accepted but response deliberately
aborted, explicit same-key replay preserving evidence ID/version/case version;
(6) browser tenant/assignment/finding denial, revoked-session mutation blocked
with no added candidate, keyboard focus and full-page protected login.

Security invariants verified: UI cannot grant L2/L3, manager or engineer authority;
wrong roles/tenant/assignment still fail direct API; original CAS and approval rules
unchanged; model data has no policy/payment/role authority; unknown/unsafe fail
closed; no arbitrary red-team execution/publication; no real transfer/control;
private media only through bearer fetch; tokens never stored in browser storage,
URLs or analytics; same-origin-only client/proxy and no credentialed CORS; `.env`
and `.git/config` denied; no implicit sensitive retries or duplicate receipt.
Unexpected request text/stack is never displayed. Local logout clears memory
even on network failure, but server revocation in that case is unconfirmed.

Actual installed Chromium **158.0.8127.18 / revision 1254**, headless local browser.
No browser download was needed. Windows sandbox initially denied child-process
temp creation; authorized local browser runs outside that sandbox used fresh
ignored `.venv` data, no Administrator/ACL/system-temp change. npm registry access
also required escalation after EACCES. All servers bound 127.0.0.1 and stopped
after tests. No actual inference, external account or paid resource.

Contractor inspected at **375/768/1440px** with no horizontal page overflow;
controls are scrolled into view before reachability assertions. Manager and engineer
desktop screenshots were inspected, including real approval and readiness fields.
Keyboard tab focus, labels, route/skip focus and visible error/status text verified.
Unexpected page/console errors are checked in primary business/engineering flows;
expected HTTP denial/network resource errors are distinguished. No exhaustive
accessibility or screen-reader/cross-browser certification.

Screenshots are actual ignored artifacts in the final `.venv/phase05-browser-*`
run, not invented/tracked customer evidence. Captures cover mobile work/evidence,
manager queue/approval/audit, engineer dashboard/finding/review/gate, login and
unauthorized screens. Final exact run root is recorded below after verification.

## Exact commands and resolved development failures

From repository root, baseline used a new .venv GUID root prefixed
`phase05-baseline-`; final full regression used `phase05-final-`:

```powershell
$phase05Temp = Join-Path (Resolve-Path .venv).Path ('phase05-final-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $phase05Temp | Out-Null
$env:TEMP = $phase05Temp
$env:TMP = $phase05Temp
$env:TMPDIR = $phase05Temp
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp (Join-Path $phase05Temp 'pytest') | Tee-Object -FilePath tracking/PHASE_05_BACKEND_TEST_OUTPUT.txt
exit $LASTEXITCODE
```

Baseline used the same pytest flags, output PHASE_05_BASELINE_OUTPUT.txt.
Focused portal reads: same fresh-temp pattern, `-m pytest backend/tests/phase05
-q -p no:cacheprovider --basetemp ...`: **10 passed in 4.21s** before the full run.
In frontend directory:

```powershell
npm.cmd install --no-fund --cache ..\.venv\phase05-npm-cache
npm.cmd view vitest@4.1.12 dependencies peerDependencies engines --json --cache ..\.venv\phase05-npm-cache
npm.cmd view vitest@5.1.0 dependencies peerDependencies engines --json --cache ..\.venv\phase05-npm-cache
npm.cmd install --save-dev --save-exact vitest@4.1.12 --no-fund --cache ..\.venv\phase05-npm-cache
npm.cmd audit --json --cache ..\.venv\phase05-npm-cache
npm.cmd ls --depth=0
npm.cmd test 2>&1 | Tee-Object -FilePath ..\tracking\PHASE_05_FRONTEND_TEST_OUTPUT.txt
npm.cmd run build 2>&1 | Tee-Object -FilePath ..\tracking\PHASE_05_BUILD_OUTPUT.txt
npm.cmd run e2e 2>&1 | Tee-Object -FilePath ..\tracking\PHASE_05_BROWSER_OUTPUT.txt
```

Each test/build/E2E invocation was followed by `exit $LASTEXITCODE` in its own
PowerShell process. Actual installation/advisory outputs are preserved. Also ran
pip check, portal_demo --help, baseline/frozen-file hashes, built-secret/log scans,
source/dependency Git diff, diff --check and final status. Windows test temp roots
were fresh/ignored; no unrelated temp deletion or system permission change.

Preserved development failures: initial TypeScript unknown-to-ReactNode conditional
fixed; one UTF-8 display/selector unit failure fixed; initial full suite **570
passed / 2 failed** because the new history route ignored the legacy assurance
flag, corrected in source without baseline assertion changes. Initial browser
failures exposed discarded challenges on refresh (fixed retained same-entity
state), select locators corrected to accessible roles, existing raw-media reason
code matched, in-memory-session navigation corrected, stale-case test synchronized
to visibly loaded old version, and responsive test corrected to scroll a long form.
Failed outputs are retained under INITIAL/SECOND/THIRD/PRE_ACCEPTANCE/RESPONSIVE
names; earlier successful four/six-browser runs also retained. Final current logs
above supersede these for acceptance. No failure was hidden by weakening old tests.

## Remaining limits, rollback and sequencing

Local functional MVP only. Full reload requires login; no refresh token/IdP/MFA or
account recovery. Views use explicit refresh, not real-time subscriptions. Existing
job list is unbounded and UI pages it locally; per-job card summarizes first five
case IDs. Other queue/run/finding lists use actual cursors. Candidate history/runs
and selectors disclose bounded latest subsets; explicit IDs may be needed for old
records. No backend global aggregate, external notification or automatic scheduler.
No production hosting/TLS/CSP/load, Firestore, physical authenticity, live vision,
customer/production detection rate, screen-reader or other-browser verification.
Synthetic fixtures and independent fictional accounts are not actual staff review.
Phase 04's manual readiness gate remains unpublished and separate from deployment.

Gemini freeze complied with: no inference/list_models/availability/billing probe,
key/model/provider change, marker reset or LIVE_GEMINI fabrication. Ten protected
artifacts match captured hashes, including .env, consumed marker, failed live result,
provider, settings, pure policy, manager/case service and Python dependency pins.
Historical root cause remains UNKNOWN; troubleshooting stays deferred through 07.

Exact [Windows install/startup/provisioning/test/demo instructions](../frontend/README.md).
Use backend.app.api:create_app --factory, loopback, provider MOCK_AI or DISABLED,
allow_billable=false. Normal mocks do not demonstrate L2; acknowledged separate
fixture does. Existing credentials/data are preserved.

Rollback (not executed): stop local frontend/demo; preserve any new private demo
data desired for audit. Review application/read-router/repository changes against
09bd8d1 before restoring only Phase 05 files. No schema/data migration was added;
existing SQLite/media remain compatible. Do not reset/clean Git, delete private
data/markers or overwrite .env. Phase 04 sources/tests remain the fallback.

Recommend review and a Phase 05 commit after user approval. No commit or deployment
performed. All mandatory local gate A-P checks have executed evidence; Phase 06
and 07 remain outside this authorization. File manifest and final Git status follow.

Final browser artifacts: `.venv/phase05-browser-1794544569437`, with 14 actual PNG captures.
Redacted persisted run/review/receipt/gate counts and screenshot dimensions/hashes:
[PHASE_05_BROWSER_ARTIFACTS.json](PHASE_05_BROWSER_ARTIFACTS.json).
The final revocation test waits for initial authenticated dashboard reads to finish
before revocation, so it specifically proves mutation denial rather than an earlier
read correctly ending the session. That initial test race is preserved separately.

New Phase 05 PowerShell Tee artifacts were normalized from UTF-16 BOM to UTF-8
for review/JSON interoperability, preserving their text. Earlier Phase 04 artifacts
and private files were not rewritten. Final new-source trailing whitespace was
removed; no runtime behavior changed.

## Files and final Git verification

Modified application files: backend/app/api.py (router composition only),
backend/app/repository.py (bounded identifier read only), .gitignore (browser
artifacts). Added backend/app/portal_router.py, backend/tools/portal_demo.py and
backend/tests/phase05/test_portal_reads.py. Created the React project/configuration,
typed client/domain/session/shared components, role feature modules, three unit
test files and real browser tests listed below. Updated README, frontend README,
architecture/security docs and all four requested tracking files; added portal
documentation, this report, baseline hashes, raw-content execution logs and
redacted browser/security artifacts. Full path manifest is the actual status below.

Final checks: 36/36 old test-file hashes and 10/10 protected artifacts match;
49 local links across ten documents resolve; no private secret matches in three
built assets or generated passwords/challenges in 20 execution logs; new-source
trailing-whitespace check clean. Protected permission/approval/provider/settings/
Python dependency diff is empty. git diff --check exit 0 (informational CRLF
notices only). Index empty. HEAD remains 09bd8d1; no deleted files or commits.

Final git status --short --untracked-files=all: 11 modified, 51 untracked,
all unstaged. Private demo data/screenshots/cache remain ignored and preserved.

```text
 M .gitignore
 M README.md
 M backend/app/api.py
 M backend/app/repository.py
 M docs/architecture.md
 M docs/security.md
 M frontend/README.md
 M tracking/EXECUTION_LOG.md
 M tracking/REQUIREMENT_MATRIX.md
 M tracking/SECURITY_TEST_CATALOG.md
 M tracking/STATUS_LEDGER.md
?? backend/app/portal_router.py
?? backend/tests/phase05/test_portal_reads.py
?? backend/tools/portal_demo.py
?? docs/portals_phase05.md
?? frontend/e2e/portals.spec.ts
?? frontend/index.html
?? frontend/package-lock.json
?? frontend/package.json
?? frontend/playwright.config.ts
?? frontend/src/App.tsx
?? frontend/src/api.ts
?? frontend/src/auth.tsx
?? frontend/src/domain.ts
?? frontend/src/features/cases.tsx
?? frontend/src/features/engineering.tsx
?? frontend/src/features/jobs.tsx
?? frontend/src/main.tsx
?? frontend/src/style.css
?? frontend/src/test/api.test.ts
?? frontend/src/test/presentation.test.tsx
?? frontend/src/test/session.test.tsx
?? frontend/src/test/setup.ts
?? frontend/src/ui.tsx
?? frontend/tsconfig.json
?? frontend/vite.config.ts
?? tracking/PHASE_05_BACKEND_TEST_OUTPUT.txt
?? tracking/PHASE_05_BASELINE_OUTPUT.txt
?? tracking/PHASE_05_BASELINE_TEST_HASHES.json
?? tracking/PHASE_05_BROWSER_ARTIFACTS.json
?? tracking/PHASE_05_BROWSER_FOURTH_OUTPUT.txt
?? tracking/PHASE_05_BROWSER_INITIAL_OUTPUT.txt
?? tracking/PHASE_05_BROWSER_OUTPUT.txt
?? tracking/PHASE_05_BROWSER_PRE_ACCEPTANCE_OUTPUT.txt
?? tracking/PHASE_05_BROWSER_RESPONSIVE_INITIAL_OUTPUT.txt
?? tracking/PHASE_05_BROWSER_REVOCATION_INITIAL_OUTPUT.txt
?? tracking/PHASE_05_BROWSER_SECOND_OUTPUT.txt
?? tracking/PHASE_05_BROWSER_SIX_PASS_OUTPUT.txt
?? tracking/PHASE_05_BROWSER_THIRD_OUTPUT.txt
?? tracking/PHASE_05_BROWSER_VERIFIED_SIX_OUTPUT.txt
?? tracking/PHASE_05_BUILD_OUTPUT.txt
?? tracking/PHASE_05_DEPENDENCY_AUDIT.json
?? tracking/PHASE_05_DEPENDENCY_FIX_OUTPUT.txt
?? tracking/PHASE_05_DEPENDENCY_INITIAL_AUDIT.json
?? tracking/PHASE_05_FRONTEND_TEST_OUTPUT.txt
?? tracking/PHASE_05_INITIAL_BACKEND_TEST_OUTPUT.txt
?? tracking/PHASE_05_INITIAL_BUILD_OUTPUT.txt
?? tracking/PHASE_05_INITIAL_FRONTEND_TEST_OUTPUT.txt
?? tracking/PHASE_05_INSTALL_OUTPUT.txt
?? tracking/PHASE_05_PIP_CHECK_OUTPUT.txt
?? tracking/PHASE_05_REPORT.md
?? tracking/PHASE_05_SECURITY_CHECKS.json
```
