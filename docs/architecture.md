# Architecture

Current Phase 02 additions: [`media_and_gemini.md`](media_and_gemini.md).
`media_service.py` authenticates/validates intake, atomically reserves a new
non-authorizing evidence version, runs a perception provider outside the DB lock,
then rechecks identity/version/challenge before appending the final observation.
`media.py` decodes bounded JPEG/PNG; `media_storage.py` is private local storage
behind a protocol. `perception.py` is the untrusted observation protocol/mock;
`gemini_provider.py` wraps the official SDK without policy or role authority.
Append-only media tables use an additive media-schema migration namespace;
existing core tables/schema/test files are preserved. The pure policy is unchanged.

## Phase 01 foundation retained

One FastAPI application, one synchronous case service, one SQLite database. No
microservices, provider SDKs, UI, bank integration or cloud resources.

`backend/app/api.py:create_app` composes the authenticated application.
`backend/app/main.py:app` is the unchanged Phase 00 metadata-only component; its
original regression tests still run. Independent Phase 01 tests cover the actual
business factory. Use that factory in startup commands.

`models.py` and `policy.py` retain the accepted pure Pydantic/Python boundary:
no I/O, network, provider, wall clock or persistence imports, and no L3 eligibility.
`case_service.py` supplies authoritative context and independently verifies human
approval before granting L3.

`auth.py` provides salted PBKDF2-HMAC-SHA256 hashes (600,000 iterations),
constant-time comparison and random opaque bearer tokens. Only token SHA-256
values are stored. Users have one server-controlled role; sessions reference the
current user record and contain no trusted client role claims.

`repository.py` implements Repository/UnitOfWork protocols through SQLAlchemy.
Tables cover tenants, users, sessions, authentication limits, jobs, reviewed
policy versions, cases, challenges, evidence metadata, approvals, action receipts,
logical decision events and schema migrations. Composite foreign keys enforce
tenant consistency for jobs, cases and policies. Initial migration version 1 is
idempotent; unsupported future schema versions fail closed.

Each case operation opens `BEGIN IMMEDIATE`, samples the server UTC clock after
obtaining the lock, reloads session/user/assignment, evaluates current stored
state and performs CAS writes in the same transaction. SQLite serializes writers;
expected versions reject stale writes. Audit/state/approval/receipt changes commit
or roll back together.

Evidence is append-only metadata with increasing versions. In Phase 01, the
internal test factory hashes exact UTF-8 canonical synthetic observation JSON
bytes, not real media. There is no HTTP intake route. Normal settings refuse test
evidence intake and promotion of saved test artifacts.

Approval binds tenant, case, job, asset/job version, action, integer amount,
evidence ID/SHA-256/version, reviewed case version, policy version, reviewer, and
challenge/evidence/auth-session context. The active case references an append-only
approval. Every L3 decision rechecks its complete binding, effective case version,
active manager identity and challenge/session validity. Approval references and
bindings remain internal; they are not credentials or model output.

Evidence, invoice, policy selection, assignment and challenge rotation invalidate
approval. Rotation/reassignment also clear current evidence. Expiry/session/
reviewer changes invalidate approval upon the next evaluation. That invalidation
commits even when the response denies an action because its version is stale.
No background expiry job is needed to prevent stale authorization.

Execution records a local simulated receipt. Completion receipts are unique per
case/action/approval binding; repeated and concurrent requests return the same
receipt. Old receipts never authorize new evidence.

A future Firestore adapter must implement the same transaction/CAS, append-only
application semantics and concurrency contract tests. The protocols are a
migration boundary, not a working Firestore adapter. The database is not claimed
to be immutable.
