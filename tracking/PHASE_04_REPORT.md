# Phase 04 acceptance report — 12 November 2026

**Verdict: PASS — LOCAL BACKEND ACCEPTANCE GATE.** Fresh final verification:
**69 Phase 04 tests passed in 24.93s**, **562 complete-suite tests passed in
91.60s**, zero failed. All **493 original tests** are retained unchanged. Actual
localhost TCP/HTTP smoke passed with independent synthetic labels, genuine weak-
candidate failures, engineer review and safe release-readiness decisions.
No policy was published. Stop at Phase 04, awaiting user review/commit approval.

## 1. Scope, baseline and acceptance audit

Continued the recovered implementation, without restarting or discarding work.
Git baseline is **f4ed39e — feat: live validation deferred**. Initial status was
clean before implementation; recovered status contained the Phase 04 files below.
Read AGENTS, Master Book relevant chapters/PDF pp.14–18,20,29, Phase 04 prompt,
contracts, Phase 03/diagnostic reports, tracking and architecture/security docs.
Audited current source, tests, request/label manifests and saved execution outputs.

| Capability | Status and executed evidence |
|---|---|
| Independent fixed corpus/oracle | IMPLEMENTED AND TESTED — separate input/label files, 38 cases, manifest hashes, conflict/review checks; oracle test forbids SUT calls while assembling labels. |
| Isolated deterministic execution | IMPLEMENTED AND TESTED — real pure-policy evaluation, disposable authenticated API and read-only binding snapshots; subprocess time/count/output controls. |
| FA/FR/review scoring | IMPLEMENTED AND TESTED — binary confusion matrix, explicit denominators/null rates, review/abstention and exact-status mismatch cases. |
| Real deliberately weakened failure | IMPLEMENTED AND TESTED — 45-PSI A02 expected DENY, actual ALLOW under test max=50; persisted finding, unsafe gate blocked, original safe candidate rejects. |
| In-app engineering findings/review | IMPLEMENTED AND TESTED — dedup/occurrences, safe repro links, triage/version/audit, distinct active reviewer, safe remediation verification. |
| Role/tenant restrictions | IMPLEMENTED AND TESTED — missing auth/business roles/other tenants denied; engineer cannot approve business action. |
| Candidate/source/corpus/review-bound gate | IMPLEMENTED AND TESTED — changed bindings, rejection/disabled reviewer, races and incomplete/forged/failed runs block readiness. |
| Persistence/migration/logical history | IMPLEMENTED AND TESTED — restart, Phase 03 upgrade, all old namespaces v1 retained, new security v1, unknown-version refusal and append-only controls. |
| Actual local TCP/HTTP workflow | IMPLEMENTED AND TESTED — authenticated create/run/find/triage/propose/review/gate, unsafe and safe controls, role/tenant denial. |
| Production/distributed/Firestore/load guarantees | DEFERRED; protocol compatibility is an architectural intention, not evidence of implemented adapters, deployment or load guarantees. |
| Live Gemini suggestions/perception | BLOCKED / DEFERRED by explicit freeze; disabled suggestion route is tested, no generation/inference success claimed. |
| Portal/UI, automatic scheduler, external notifications, CI/deployment release integration | DEFERRED; no Phase 05 or production publication implemented. |

Strongest supported claim: SENTINEL can independently regression-test its
permission policies against labeled synthetic scenarios, reproduce failures,
notify engineers through a restricted in-app API feed, and require independent
human-account review before marking a tested candidate ready for manual release.
This is a local MVP capability, not actual deployment or real-world accuracy.

## 2. Implementation architecture and endpoints

`assurance_models` defines typed requests/results; `assurance_corpus` generates
fixed inputs and assembles separate labels; `assurance_executor` adapts the existing
SUT; `assurance_worker` executes in disposable scope; `assurance_scoring` compares
outcomes; `assurance_service` handles tenant auth, persistence, triage/review/gates;
`assurance_router` extends the existing application factory. Repository changes
are additive namespace v1 tables and bounded page queries. Pure policy, manager
logic and Gemini provider remain unchanged.

Normal factory: backend.app.api:create_app --factory, assurance enabled by default.
Historical backend.testing.create_test_app explicitly disables assurance to retain
the original Phase 01 no-red-team schema contract. New current-factory OpenAPI,
positive/negative API tests and actual TCP smoke cover enabled assurance. No pytest
detection or existing assertion edit is used. Worker disables nested assurance.

All routes below require current authenticated ENGINEER and tenant scope:

| Method | Endpoint |
|---|---|
| POST / GET | /v1/redteam/candidates |
| GET / PATCH | /v1/redteam/candidates/{id} |
| POST | /v1/redteam/run |
| GET | /v1/redteam/runs |
| GET | /v1/redteam/runs/{id} |
| POST | /v1/redteam/suggest — BLOCKED, GEMINI_FROZEN, no candidates |
| GET | /v1/alerts |
| GET | /v1/alerts/{id} |
| POST | /v1/alerts/{id}/triage |
| POST | /v1/alerts/{id}/remediations |
| POST | /v1/redteam/candidates/{id}/reviews |
| POST | /v1/redteam/candidates/{id}/release-gate |
| GET | /v1/redteam/release-gates/{id} |
| GET | /v1/redteam/audit |

Exact roles, typed fields, statuses, limits, version requirements and errors are
documented in [assurance_phase04.md](../docs/assurance_phase04.md). Paths consistently
use /v1/, never /api/v1. No arbitrary code/policy/scenario upload, public fixture
endpoint, shell execution route or policy publication operation was added.

## 3. Corpus, oracle and isolation

Corpus sentinel-independent-synthetic v1.0.0 contains **38 unique scenarios**:
24 pure-policy, nine authenticated API, five read-only binding snapshots. Input
mutations and static labels are separate files; a pinned manifest, duplicate/
semantic conflict checks and deterministic ID/version ordering protect assembly.
Each typed scenario records source/version/target policy, fictional scope, actor/
authorization context, action, observations, category/risk/rationale and repro
steps. Labels separately define expected decision, applicable HTTP/inspection/
permission fields and required reason codes. NaN/infinity use explicit mutation
tags, not invalid JSON constants.

Source is SYNTHETIC / SPECIFICATION_REFERENCE from accepted Master Book/domain
requirements. No additional human dataset review or live AI labeling is claimed.
Pending/unreviewed HUMAN_LABELED types cannot enter the oracle. No expectation is
computed from authorize(). Parents recompute all comparisons from pinned labels
and actual results, ignoring worker-reported success/summary claims.

Coverage includes missing/incorrect/expired asset/challenge/evidence, replay,
missing/nonfinite/negative readings, units, unsafe pressure/calibration, conflicts,
authority-field injection, contractor/engineer escalation, other tenant/unassigned
job, stale evidence/policy/invoice binding, concurrent mutation, L2≠L3 and valid
cases. The final audit corrected A05 actor metadata to describe the same unassigned
Tenant B engineer used by its API test. Expected labels and test count unchanged;
the existing oracle test was strengthened.

Fixed worker command has no user code/path or provider credentials. It runs in
temporary local SQLite/media scope with explicit SYNTHETIC/MOCK_AI inputs, no
external sockets, 20-second parent deadline, max 64 scenarios and 512-KiB output
check. Caller repository/policies/cases are not passed to the child. It creates
no SQL manager approval or business action. Binding snapshots use the real
verifier on read-only fictional rows, not an authenticated new sign-off; existing
493-test baseline retains real approval/transaction tests.

Corpus SHA-256:
2c795fd87fe822c3ee89b1c5ee934a9011bb38e9dc31bc64f6fd9a546580933d.
Candidate hash binds profile, artifact revision, exact policy config and all
backend app source hashes. Run/review/gate also bind corpus/software hashes.

## 4. Executed synthetic metrics and genuine failures

Fresh acceptance HTTP smoke executes the 38-case corpus against three candidates:
**114 scenario/candidate evaluations, not 114 independent real-world samples**.

| Candidate | Passed / failed | TP / FN / TN / FP | False approval rate | False rejection rate | Exact review matches | Review bypasses / abstentions | Gate |
|---|---|---|---|---|---|---|---|
| SAFE_BASELINE | 38 / 0 | 26 / 0 / 6 / 0 | 0/26 = 0 | 0/6 = 0 | 6/6 | 0 / 0 | READY_FOR_MANUAL_RELEASE after review |
| WEAK_TEST_ONLY | 36 / 2 | 25 / 1 / 6 / 0 | 1/26 = 3.846% | 0/6 = 0 | 5/6 | 1 / 0 | BLOCKED, even with reviewer approval |
| OVERRESTRICTIVE_TEST_ONLY | 19 / 19 | 20 / 0 / 2 / 2 | 0/20 = 0 | 2/4 = 50% | 3/6 | 0 / 8 | BLOCKED |

Positive binary class is **should DENY**. TP=invalid correctly denied,
FN=false approval, TN=valid correctly allowed, FP=false rejection. Expected
NEEDS_REVIEW and actual review/abstention on binary-expected cases are excluded
from binary denominators and shown separately. The restrictive candidate scores
24 binary outcomes from 32 binary-expected cases, with eight abstentions excluded;
its two valid-case abstentions also fail exact regression expectations. Review
bypasses and wrong SAFETY_ALERT/REVIEW_REQUIRED/permission/reason fields fail the
gate even when not counted in binary rates. Zero denominators are null/N/A.
All three executions had zero skipped/unevaluable cases. No rate is a production
fraud/attack-prevention or visual-perception measurement.

The weakened in-memory candidate changes only fictional max pressure 40→50.
**A02** evaluates 45 PSI through the real authenticated invoice API: independent
expected DENY/SAFETY_ALERT/L1; actual ALLOW/EVIDENCE_COMPLETE/L2. **P15** independently
expects pure NEEDS_REVIEW/SAFETY_ALERT/L1; actual ALLOW, a separate review bypass.
Original safe candidate rejects/reviews the same inputs correctly and still
accepts valid 35 PSI. No result was hardcoded; the smoke uses fresh isolated
workers and existing evaluator code. The restrictive min=36 variant measures
false rejections and prevents a deny-everything claim from appearing successful.
No weakened policy file was saved under production policies or registered there.

## 5. Findings, review, gate and security invariants

Mismatch records bind scenario/version, candidate/policy/artifact/corpus hashes,
expected/actual fields, mismatch/severity rationale, first/last timestamps, owner,
run occurrence and restricted reproduction references. A02 is a HIGH test-only
false-approval finding; ordinary regression/false-rejection findings are MEDIUM,
reason-only mismatches LOW. Correct attack denials create no alert; not every
failure is critical. Fingerprints deduplicate identical tenant-scoped failures;
each occurrence/run stays auditable. Details cap occurrence/proposal history at
100 with a truncation flag. No raw media, private tokens, challenge secrets,
untrusted injection text or provider payload is included in alerts.

Triage uses current ENGINEER identity, expected finding version and safe enum
reason. Dismissal cannot erase failed results. Remediation refers only to an
isolated candidate artifact. Independent review must be by a different active
ENGINEER than candidate/proposal author; it binds exact candidate/source/corpus/
run and separate review revision. A later rejection or changed candidate/source/
corpus/disabled reviewer invalidates earlier readiness. Two concurrent reviews
have one revision winner. Races cannot restore obsolete authority.

READY requires complete current execution, no mandatory mismatch/unevaluable
case, no false approval/review bypass, valid-case acceptance, and current exact
independent review. Green tests alone fail without review; an approval alone
cannot release a failing candidate. Every gate says published=false. Historical
gate decision is preserved; its current effective decision becomes BLOCKED when
binding is stale. Verified triage requires this finding's accepted current gate.

Bearer/role/tenant checks cover every engineering route; manager/contractor/
service-agent denials, other-tenant object/cursor denials and engineer business
approval denial are executed. No policy, case or payment authority is granted by
a test result, notification, model text or finding badge. Core L0–L3 and inspection
semantics remain separate and unchanged.

## 6. Persistence, concurrency and limits audited

SQLite BEGIN IMMEDIATE and explicit candidate/finding/review revisions protect
state; run reservation/finalization, occurrence/finding/audit and review/gate
records commit transactionally. Worker I/O is outside the lock. Idempotency keys
are hashed/scoped to tenant/actor/request; pending duplicates return 202 without
another worker, changed payload conflicts, repeated completed requests return
the same run. Changed candidate mid-run is STALE; logout records FAILED without
returning private results. Interrupted/failed/missing/forged/unevaluable execution
cannot become a false PASS. Proposal failure rolls back all records.

Security migration namespace v1 is additive; core/media/workflow namespaces remain
v1. Restart and pre-security migration tests preserve records. Run/result/
occurrence/proposal/review/gate/audit histories reject ordinary UPDATE/DELETE;
database owners can still alter files/triggers. This is logical audit history,
not a cryptographically immutable ledger. No Firestore correctness is claimed.

## 7. Actual commands, logs and historical evidence

The saved generic PHASE_04_TEST_OUTPUT.txt and INITIAL_TEST_OUTPUT.txt contain the
**historical** first full-run result: 560 passed, one failure in 96.05s. Its Phase 01
schema asserted no red-team paths. The explicit historical test-factory option
resolved that conflict, with current normal-factory security coverage added;
no baseline assertion changed. The old PHASE_04_HTTP_SMOKE_OUTPUT.txt and INITIAL
HTTP output are successful earlier smoke evidence for their recorded source hashes.
They are preserved, not overwritten or treated as final current-source validation.

The user separately reported recovery passes (69 and 562/87.04s) plus a Windows
Temp WinError 5 workaround. Those are user-reported results. This acceptance
rerun uses new writable ignored .venv roots and has its own executed logs below;
it did not alter system permissions or delete unrelated temp files.

Before implementation: 493 passed in 63.80s, saved in PHASE_04_BASELINE_OUTPUT.txt;
29 original Python test file hashes recorded before edits. Intermediate new-suite
68/68 and compatibility scope 25/25 runs passed. Final accepted commands:

```powershell
Set-Location D:\project\sentinel_ladder_v2
$phase04Temp = Join-Path (Resolve-Path .venv).Path ('phase04-acceptance-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $phase04Temp | Out-Null
$env:TEMP = $phase04Temp
$env:TMP = $phase04Temp
$env:TMPDIR = $phase04Temp
.\.venv\Scripts\python.exe -m pytest backend/tests/phase04 -q -p no:cacheprovider --basetemp (Join-Path $phase04Temp 'pytest') | Tee-Object -FilePath tracking/PHASE_04_ACCEPTANCE_SCOPE_OUTPUT.txt
exit $LASTEXITCODE
```

Actual: **69 passed in 24.93s**, exit 0. Breakdown: oracle 18, scope 15,
transactions 15, persistence/limits 15, workflow 6.

The full-suite command used an independently created root with prefix
phase04-regression-, the same TEMP/TMP/TMPDIR assignments, then:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp (Join-Path $phase04Temp 'pytest') | Tee-Object -FilePath tracking/PHASE_04_ACCEPTANCE_TEST_OUTPUT.txt
exit $LASTEXITCODE
```

Actual: **562 passed in 91.60s (0:01:31)**, exit 0. All 493 baseline tests plus
69 Phase 04 tests; zero failed. Windows Python 3.14.7 only. No coverage percentage,
Python 3.11/3.12 or remote CI execution claimed.

The actual HTTP command used a new phase04-http- GUID root with the same temp
assignments, then:

```powershell
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase04 | Tee-Object -FilePath tracking/PHASE_04_ACCEPTANCE_HTTP_SMOKE_OUTPUT.txt
exit $LASTEXITCODE
```

Actual exit 0, final line:

```text
PASS Phase 04 actual TCP/HTTP; SYNTHETIC and isolated MOCK_AI only; Gemini frozen; no publication
```

Smoke uses existing factory/Uvicorn over real loopback TCP. Only fictional identity
provisioning is local setup; all exposed engineering/business transitions use
authenticated HTTP. It retrieves results/findings, checks redaction/dedup, triages,
proposes/reviews weak and safe candidates, blocks weak even after review, accepts
safe after independent fictional reviewer, verifies remediation, rejects stale
triage and denied roles/tenant/business approval, and confirms suggestions blocked.
Review accounts are simulated people for testing, not an actual multi-human
operational sign-off or production release. Only its own temporary resources clean up.

Final acceptance run IDs: weak 883c8a1a-6f73-4ada-923c-81aef21049e8;
safe b4318628-ca8f-46db-b5df-040db753bfdc;
restrictive d26628d1-6156-47ec-81b2-2a5d38108783. Exact artifact hashes and all
metrics are retained in the fresh smoke log; no fabricated screenshots/chart.

Also executed pip check: **No broken requirements found.**, exit 0. No dependency
install/pin changes. Baseline verification: 29 old test files and eight frozen
policy/model/provider/dependency/credential/marker/result files matched their
captured hashes, mismatches=[]. Protected source diffs and final whitespace/link/
Git verification are recorded in the acceptance audit below.

## 8. Gemini freeze and remaining limitations

No Gemini/API/list-models/availability probe, real key use, billable AI call,
provider/model/config change or marker reset occurred. Automated fixtures use
dummy data and controlled SYNTHETIC/MOCK_AI. Original failure root remains UNKNOWN;
no LIVE_GEMINI observations were fabricated. Further Gemini work remains deferred
until Phases 04–07 complete. No Phase 05 UI or frontend work.

Remaining limits: local trusted-code process separation, not a hostile-code OS
sandbox; stdout buffered before its size check; no global memory/disk/retention
quota or distributed abuse limiter. Reads/results are bounded; the ten-run guard
uses a recent tenant history window. Periodic/targeted triggers are metadata/manual
operations, not a scheduler or customer-data ingestion. Histories cap detail pages
and expose truncation. No external alert delivery, real multi-human IAM, production
TLS/load, Firestore or distributed transaction evidence. Synthetic labels are
specification reference, not additional independent human/customer evaluation.

Gate output is readiness evidence for a **manual** release only. No CI/deploy/
publication workflow was implemented. Existing trusted offline policy registration
retains its prior controls and does not auto-consume these candidate fixtures;
no enforcement over privileged operator/file edits is claimed. No policy mutation
or automatic healing. Photos/schema-valid observations cannot establish genuine
repair, authenticity, industrial safety or payment authorization.

## 9. Files changed/added and rollback

Modified code: backend/app/api.py, backend/app/repository.py, backend/testing.py.
Added code: backend/app/assurance_models.py, assurance_corpus.py,
assurance_scoring.py, assurance_executor.py, assurance_worker.py,
assurance_schema.py, assurance_service.py, assurance_router.py;
backend/tools/smoke_phase04.py.

Added tests: backend/tests/phase04/__init__.py, conftest.py, test_oracle.py,
test_scope.py, test_transactions.py, test_persistence_and_limits.py, test_workflow.py.
Added corpus: fixtures/security/scenarios_v1.json, labels_v1.json,
manifest_v1.json, README.md. Added docs: docs/assurance_phase04.md.
Modified docs: README.md, docs/architecture.md, docs/security.md, docs/decisions.md.

Tracking additions: this report; PHASE_04_BASELINE_TEST_HASHES.json;
PHASE_04_BASELINE_OUTPUT.txt; PHASE_04_TEST_OUTPUT.txt;
PHASE_04_INITIAL_TEST_OUTPUT.txt; PHASE_04_HTTP_SMOKE_OUTPUT.txt;
PHASE_04_INITIAL_HTTP_SMOKE_OUTPUT.txt; PHASE_04_ACCEPTANCE_SCOPE_OUTPUT.txt;
PHASE_04_ACCEPTANCE_TEST_OUTPUT.txt; PHASE_04_ACCEPTANCE_HTTP_SMOKE_OUTPUT.txt.
Updated STATUS_LEDGER.md, REQUIREMENT_MATRIX.md, SECURITY_TEST_CATALOG.md,
EXECUTION_LOG.md. The ignored phase04_protected.local.json is new local hash
evidence only; private credentials and consumed/live result artifacts unchanged.

Rollback (not executed): stop the local server, preserve a consistent SQLite
backup using SQLite backup API plus matching private media/config, and keep all
old/new run/review/evidence records. Restore only reviewed Phase 04 application/docs
changes against f4ed39e after user direction. Do not drop additive tables, delete
private data/markers, reset/clean Git or run an automatic schema downgrade. Keep
the upgraded database offline until compatibility/review obligations are assessed.

## 10. Final gate and Git evidence

All mandatory local Phase 04 gates have executed evidence. No current test/smoke
failure remains. Reported production/live/portal limitations do not change the
local backend verdict: **PASS / TESTED**, awaiting user acceptance. Recommend a
reviewed Phase 04 commit of the manifest above; no commit/push is performed.
Phase 05 requires separate authorization. Final actual Git status and acceptance
hash/whitespace/link checks follow.


Final executed checks: original test hashes **29/29 match**; protected source,
dependency and private artifacts **8/8 match**; local documentation links **30
checked across 11 documents, zero missing**. Protected policy/provider/model/
case-service/dependency Git diff is empty. Staged diff is empty; HEAD remains
f4ed39e. `git diff --check` initially found an extra final blank line in the
new execution-log entry; removed it and reran successfully (**exit 0**). Git's
LF-to-CRLF notices remain informational. No current test, dependency or whitespace
failure is outstanding. No files are staged or deleted.

Exact local backend startup (PowerShell; independent hidden-password prompts):

```powershell
Set-Location D:\project\sentinel_ladder_v2
.\.venv\Scripts\python.exe -m backend.tools.manage init-demo
.\.venv\Scripts\python.exe -m backend.tools.manage create-user --tenant demo-a --username engineering_reviewer --role ENGINEER
.\.venv\Scripts\python.exe -m uvicorn backend.app.api:create_app --factory --host 127.0.0.1 --port 8000
```

Keep the provider DISABLED. Login using the provisioned ENGINEER and separate
reviewer accounts in local Swagger. These commands are reproduction instructions,
not an additional execution/deployment claim.

Final `git status --short --untracked-files=all`: **11 modified, 31 untracked**;
all changes unstaged. Private/ignored files remain outside this manifest.

```text
 M README.md
 M backend/app/api.py
 M backend/app/repository.py
 M backend/testing.py
 M docs/architecture.md
 M docs/decisions.md
 M docs/security.md
 M tracking/EXECUTION_LOG.md
 M tracking/REQUIREMENT_MATRIX.md
 M tracking/SECURITY_TEST_CATALOG.md
 M tracking/STATUS_LEDGER.md
?? backend/app/assurance_corpus.py
?? backend/app/assurance_executor.py
?? backend/app/assurance_models.py
?? backend/app/assurance_router.py
?? backend/app/assurance_schema.py
?? backend/app/assurance_scoring.py
?? backend/app/assurance_service.py
?? backend/app/assurance_worker.py
?? backend/tests/phase04/__init__.py
?? backend/tests/phase04/conftest.py
?? backend/tests/phase04/test_oracle.py
?? backend/tests/phase04/test_persistence_and_limits.py
?? backend/tests/phase04/test_scope.py
?? backend/tests/phase04/test_transactions.py
?? backend/tests/phase04/test_workflow.py
?? backend/tools/smoke_phase04.py
?? docs/assurance_phase04.md
?? fixtures/security/README.md
?? fixtures/security/labels_v1.json
?? fixtures/security/manifest_v1.json
?? fixtures/security/scenarios_v1.json
?? tracking/PHASE_04_ACCEPTANCE_HTTP_SMOKE_OUTPUT.txt
?? tracking/PHASE_04_ACCEPTANCE_SCOPE_OUTPUT.txt
?? tracking/PHASE_04_ACCEPTANCE_TEST_OUTPUT.txt
?? tracking/PHASE_04_BASELINE_OUTPUT.txt
?? tracking/PHASE_04_BASELINE_TEST_HASHES.json
?? tracking/PHASE_04_HTTP_SMOKE_OUTPUT.txt
?? tracking/PHASE_04_INITIAL_HTTP_SMOKE_OUTPUT.txt
?? tracking/PHASE_04_INITIAL_TEST_OUTPUT.txt
?? tracking/PHASE_04_REPORT.md
?? tracking/PHASE_04_TEST_OUTPUT.txt
```

