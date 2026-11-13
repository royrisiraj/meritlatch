# Phase 06 deployment decision

Selected: native Windows **loopback** demonstration. One Uvicorn process serves
the built React bundle and the accepted FastAPI APIs from one origin. SQLite and
private original media stay on explicitly named local disk. This is a local
rehearsal, not an Internet deployment. No Docker, cloud account or spending needed.

| Option | Persistence/concurrency/recovery | Security, complexity and cost exposure | Decision |
|---|---|---|---|
| A. Local Windows | Existing SQLite BEGIN IMMEDIATE/CAS, local private media, explicit stopped backup and restart | Loopback, app bearer auth and private generated root; operator disk/backup responsibility. No cloud charge assumed. | Selected and tested locally; fastest defensible buildathon path. |
| B. Private single machine | Explicit durable disk, same SQL transactions, managed backups needed; one application process | Later HTTPS, machine hardening, access controls, patching, monitoring and cost review. Private network only until separately approved. | Technically closest future staging option; NOT configured or deployed. |
| C. Cloud Run + external durable storage | Instance filesystem is disposable. External DB and private object storage required; existing SQLite cannot be substituted automatically. | Cloud IAM, application auth, network, service accounts, secret management, billing and migration tests required. No free-tier assumption or price invented. | BLOCKED/DEFERRED; architecture planning only. |
| D. Kubernetes/multiple services | Same external persistence issues plus orchestration | Unnecessary complexity for current product and presentation. | Not recommended for this phase. |

Cloud Run filesystem facts verified against [official overview](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run)
and [security design](https://docs.cloud.google.com/run/docs/securing/security).
Minimum/maximum instances=1 or concurrency=1 does **not** make local data durable.

## Persistent state inventory

All database rows below are currently in the configured SQLite file; demo uses
only its generated root/data/demo.sqlite, never backend/local.sqlite. API access
always rechecks authenticated tenant/role/assignment. Retention is operator-managed;
no automated deletion or immutable ledger is claimed. Back up the entire coherent
DB plus media, not independent table exports. Recovery requires compatible source,
schema and protected local files. No table is already a Firestore collection.

| State / actual tables | Owner and read/write path | Atomicity/concurrency | Confidentiality, retention and recovery | Cloud migration |
|---|---|---|---|---|
| tenants, users, password hashes | Trusted offline provisioning; login/me/current actor | Unique tenant/user, active role checked within transaction | Password hashes/private identity data; retain only needed demo period; coherent DB backup | High: auth store/IAM design, no browser credential access |
| sessions, auth_limits | Login/logout and every private API | Hashed random session, revocation/expiry, persistent failed-login updates | Session hashes, private IDs; challenge-dependent expiry must survive restart | High: shared durable sessions/throttles, preserve revocation |
| jobs, job_workflow, job_events | Manager create/assign; scoped job reads | Same-tenant role assignments, versioned reassign invalidates all case authority atomically | Fictional asset/user metadata; events retained, no fake timestamps | High: composite constraints, joins and version transactions |
| cases, case_workflow / invoice revisions | Case service/workflow service | BEGIN IMMEDIATE, explicit case version and invoice revision | Private business state; no real payment; recover all related snapshots | High: exact CAS and state-machine parity |
| policies | Source-controlled approved template; trusted registration/select | Reviewed immutable versions; selection invalidates approval | Config plus author/reviewer references; preserve version provenance | High: no automatic candidate promotion |
| challenges | Assigned contractor challenge API | secrets token, tenant/job/asset/case/auth/evidence-session, expiry | Actual tokens private; never in package/screenshots/audit exports; retain only isolated state | High: transactional challenge/session validity |
| evidence, media_uploads | Actual byte intake; private content API | Reserve version before provider; scoped exact hash duplicate checks | SHA-256, internal private storage key, provenance; no authenticity claim | High: metadata/object lifecycle reconciliation |
| raw image files | LocalPrivateMediaStorage put/read/discard | O_EXCL names, fsync, bounded decode; DB/filesystem not one atomic transaction | Private original bytes; current-only authorized downloads; operator retention/orphan repair | High: private object store adapter, digest recheck and orphan handling |
| normalized provider input | Media decoder/provider call; memory bytes and normalized digest | Derived from bounded decoded original, no persistent normalized image file | Transient normalized image bytes; DB keeps digest/metadata, not a second public file | Medium: preserve byte semantics, never assume object mount gives SQL durability |
| media_analyses, analysis_runs/results | Two-stage media analysis/recovery | Provider I/O outside DB lock, current-version finalization, append-only outcomes | Untrusted observation JSON; public projection redacts challenge; failed/pending states retained | High: late-result and concurrent mutation tests unchanged |
| submission_operations | Upload idempotency | Hashed actor/session/request binding; exact replay, no repeat inference | Private operation hashes/digest/version; preserve across restart | High: unique request binding and current scope |
| approvals, manager_reviews | Authenticated independent manager approval/rejection | Exact tenant/case/action/amount/evidence/policy/reviewer/challenge binding, CAS | Internal approval keys private; public snapshots redacted; evidence changes invalidate | Critical: do not emulate with several independent document writes |
| action_runs | Assigned agent execute | Unique simulated receipt per current binding, replay returns same receipt | Historical simulated receipt, no money/control; never restore obsolete approval | Critical: action authorization and receipt commit together |
| decision_events, workflow_events | Case service/audit API | Append-only logical events with transaction ordering | Redacted public references; DB owner can alter files/triggers | High: durable ordering/retention, no tamper-proof claim |
| security_candidates | Engineer candidate APIs | Artifact/source/version binding; revision CAS | SYNTHETIC/test-only metadata, no operational policy | High: current-source hash and independent review semantics |
| security_runs, security_results | Fixed isolated worker coordinator | Reservation/idempotency and immutable final result; failed/interrupted never pass | Independent expected/actual and denominators, not customer accuracy | High: queries/limits/transactions/worker isolation |
| security_findings, security_occurrences | Engineer feed/detail/triage | Tenant fingerprint dedup, versioned finding plus append-only occurrences | Safe reasons/repro refs, no raw customer media or payload | High: dedup uniqueness and bounded history |
| security_proposals, security_reviews | Engineer proposal and distinct reviewer | Artifact/corpus/run/reviewer + review revision CAS | Human-account identity is not real staff operational sign-off | Critical: cannot self-review or preserve a stale approval |
| security_gates, security_events | Engineer readiness/history/audit | Exact current complete run/review, stale binding blocks | published=false, append-only logical history | Critical: readiness is not publication |
| schema namespaces | SQLite migration core/media/workflow/security v1 | Additive migrations, unknown versions rejected | Metadata, no runtime secret; coherent backup before any future migration | High: explicit migration, not copying SQL to Firestore |
| local config / .env | Local operator, Settings | No UI writes; demo never loads it | May contain real API key; excluded and untouched | Separate future Secret Manager/IAM design |
| historical Gemini marker/result/image/review | Original guarded runner/operator | One consumed attempt must remain consumed | Private historical files outside demo; never package, reset or fabricate | Not a deployment input; preserve offline |
| demo control/credentials/logs/screenshots | Phase 06 operator only | Owned-root lease, instance-bound stop, one-hour service deadline | Random private credentials; root-only ACL; no tokens in args/logs; preserve evidence on stop | Demo-only, excluded from package; not production account provisioning |

## Prepared future cloud design, not implementation

Book-aligned candidate: Cloud Run + Firestore + private Cloud Storage. Firestore's
[transaction isolation](https://firebase.google.com/docs/firestore/transaction-data-contention)
does not implement this repository's SQL joins, FK/unique constraints, event ordering,
CAS and idempotency automatically. A Firestore adapter, indexes and full concurrency/
restart contract suite are a separate engineering migration. No Firestore SDK or
resource has been configured here.

Alternative: Cloud SQL PostgreSQL may fit existing relational data better, but
SQLite BEGIN IMMEDIATE/WAL/trigger/migration behavior must be replaced with reviewed
PostgreSQL transactions/locking and a tested connection pool. [Official connector
requirements](https://docs.cloud.google.com/sql/docs/postgres/connect-connectors)
and [Cloud Run connectivity/IAM](https://docs.cloud.google.com/sql/docs/postgres/connect-run)
require infrastructure plus a supported connector/driver; current Python pins do
not constitute such an adapter. No connector installed or credentials used.

Private object storage requires an actual storage-protocol adapter and object
permissions, not a public bucket or a fake shared disk. Preserve reserve/upload/
finalize and digest checks; DB and object store are not a distributed atomic commit.
Orphan/pending recovery, backups, retention, deletion and failure testing are required.
Use [public access prevention](https://docs.cloud.google.com/storage/docs/public-access-prevention)
and least-privilege object access after authorization; never expose raw internal URIs.

Cloud IAM governs which service identities can reach infrastructure. It does not
replace application MANAGER/CONTRACTOR/ENGINEER/SERVICE_AGENT, tenant or assignment
checks. A future browser-access strategy must reconcile Cloud Run IAM/IAP/front-door
auth with the app's opaque bearer sessions. No unauthenticated Cloud Run flag,
cloud secret, service account, billing or public endpoint was created.

Statuses: LOCAL TESTED and PACKAGE BUILT/LOCAL REHEARSAL PASSED require the report's
executed results. CLOUD CONFIGURATION PREPARED means this design/checklist only,
not executable provisioned manifests. REMOTE DEPLOYMENT: NOT ATTEMPTED. Durable
cloud adapters, accounts/permissions, cost review, explicit access approval and
independently verified remote transactions remain blockers. No exact price or
free-tier guarantee is asserted.
