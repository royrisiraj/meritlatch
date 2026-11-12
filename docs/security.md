# Security and limits

Phase 04 assurance controls and scope are documented in
[`assurance_phase04.md`](assurance_phase04.md). ENGINEER-only tenant-wide synthetic
security access does not grant business-manager approval or access to another
tenant. Current actor identity is rechecked on mutations/finalization. Review
revision CAS and independent reviewer identity prevent self/stale sign-off;
source/corpus/candidate changes invalidate readiness. Failed or interrupted runs
cannot pass a gate; dismissed findings retain their failing evidence.

This is a local trusted-code assurance runner, not an arbitrary-code sandbox,
production fraud benchmark or policy publisher. Subprocess time/count bounds,
credential-free environment, fixed commands, no external sockets and safe output
validation are tested. Total retention/storage quotas and distributed rate limits
are not implemented. The existing offline policy registrar is a separate trusted
operator path, not automatically driven by these test candidates. Live Gemini
remains deferred through Phases 04–07; no provider/configuration/key changes.

Phase 03 current workflow controls: [`workflow_phase03.md`](workflow_phase03.md),
`backend/tests/phase03/`, and the [report](../tracking/PHASE_03_REPORT.md).
Manager-only tenant-scoped queue/review/rejection cannot authorize through badges.
Rejection stores the authenticated snapshot, clears approval atomically and caps
matching bytes at L0; a fresh contractor challenge and new eligible bytes are
required. Invoice/policy changes and stale/concurrent requests cannot undo it.
Completed receipts remain historical rather than being rewritten by rejection.

Optional upload replay binds hashed key to actor/auth session/case/original
expected version/challenge/evidence session/bytes/MIME and reauthorizes current
scope. Explicit recovery reads digest-checked private bytes, enforces same mode,
valid original session/challenge, deadline grace and three-run limit, then uses
the existing two-phase CAS. Successful/blocked/schema-invalid/rejected evidence
cannot be retried into approval. Live recovery also needs per-request billable
consent; all live verification remains BLOCKED. No credential or observation
injection endpoint was added. Review/event/operation/recovery histories reject
ordinary mutation; privileged database tampering remains possible.

Phase 02's current media/provider boundaries and remaining risks are in
[`media_and_gemini.md`](media_and_gemini.md). New controls include bounded signature
and decoder validation, scoped exact duplicates/private reads, two-phase CAS
analysis, immutable logical analysis records, schema/semantic validation,
provider timeout/error denial and explicit provenance modes. Gemini has no
authorizing tools or approval credentials. Live verification is BLOCKED; mocked
transport tests do not establish real perception accuracy or injection immunity.

## Retained Phase 01 security baseline (historical scope)

Evidence: `tracking/EXECUTION_LOG.md`, `tracking/PHASE_01_REPORT.md`, and
`backend/tests/phase01/`. These are local SYNTHETIC authorization tests, not
perception, industrial safety, production-load or fraud-detection benchmarks.

All business routes require opaque bearer authentication. Current tenant, role
and assignment are loaded inside the case transaction. Contractors see assigned
jobs; engineers see assigned jobs with redacted observations; service agents are
action-only with individual job assignments. Managers review their tenant's
cases and cannot edit policy rules. No public role-provisioning route exists.

Passwords use salted PBKDF2-HMAC-SHA256 (600,000 iterations). Sessions are random,
expire after one hour, are stored as hashes and can be revoked by logout. Current
account status/role is checked on each request. Five failed logins per hashed
tenant/username bucket block attempts for up to 15 minutes. Failed-attempt writes
persist despite error responses. There are no shared/default credentials.

Challenges use `secrets.token_urlsafe(32)` and bind tenant, job, asset, case,
contractor authentication session, random evidence session and five-minute expiry.
At most five challenges per actor/job in ten minutes are issued; a fresh login
cannot bypass this limit. Client-supplied challenge scope/token/expiry is rejected.
Visible challenge text supports evidence; it does not prove authenticity or a
physical visit.

The pure policy rejects invalid numbers and authority fields; unknown/missing
units, uncertainty, stale challenges and unsafe readings remain restricted. L2
never implies L3. Independent active managers approve simulations; only assigned
service agents execute completion against the full current-state binding.

Mutations invalidate approvals transactionally. Tests race actual separate SQLite
connections for approval/replacement and completion/replacement, assert CAS
conflicts, and prove rollback after an injected failure. Append-only triggers
reject ordinary history UPDATE/DELETE; a database owner can still change the
file or drop triggers. This is an auditable logical history, **not a tamper-proof
or immutable ledger**.

No HTTP synthetic intake exists. Only explicit Python test factories enable it;
normal settings also refuse promotion of previously persisted test artifacts.
Model adapters have no authority-bearing tools. Offline policy version
registration needs two independently authenticated engineers, a review reference
and a structural regression guard. It does not activate the version. Assigned
engineers may select an already registered version, invalidating approval. The
larger Phase 04 adversarial/release gate is not claimed as complete.

Health/docs/schema are public metadata. JSON bodies are bounded to 16 KiB before
parsing, including chunked input. Validation and exception responses omit input
echoes, credentials and exception text. Unexpected request exceptions are caught
before general server exception logging. Responses use `no-store` and `nosniff`.
Scoped audit records omit raw observations/challenges/tokens. No CORS middleware
or session cookies are enabled; later browser cookie/CSRF design is still pending.

Remaining risks:

- Local development only: no production TLS, MFA, password reset, external identity
  provider, global/IP abuse prevention or distributed throttling. An attacker can
  use account-specific throttling to deny login to a known username. Use loopback
  and fictional data only.
- Safe JPEG/PNG intake/private storage and bounded explicit provider recovery
  exist; retention/deletion, orphan repair and automated crash recovery do not.
  Synthetic hashes identify fixture JSON bytes; image hashes identify exact
  original media. Incorrect but compliant observations can pass; there is no
  physical truth, authenticity or verified live image-reading guarantee.
- SQLite serializes writers; busy conflicts fail closed. Tests establish local
  orderings, not arbitrary production load or Firestore correctness.
- Core, media and workflow migrations each retain additive version 1. Back up
  database and media before upgrade; there is no automatic downgrade. Queue
  filtering scans at most 500 cases per page; review history is capped at 100,
  with truncation flag and paged audit. Old media downloads remain current-only.
- Only Python 3.14.7 was executed. Python 3.11/3.12 and remote CI remain unverified.
  Dependency verification passes; no production load/compatibility claim follows.
- Local database/backup ACLs depend on the Windows operator. No external audit
  retention or cryptographic event attestation is implemented.

No money movement, equipment control, external notification, cloud resource,
live AI call or production deployment occurred.
