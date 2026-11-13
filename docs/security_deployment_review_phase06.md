# Phase 06 hosting security review

Implemented local controls: loopback-only Uvicorn, single process, proxy_headers
disabled, trusted localhost/127.0.0.1 Host values; same-origin static assets/API,
no CORS/cookies, strict frontend CSP (self scripts/styles, blob images, no frames/
objects), no-referrer, nosniff and no-store. Swagger external-CDN UI omitted from
this offline wrapper; actual API/OpenAPI and existing metadata health remain.
Readiness exposes status only, not DB paths/user counts/config/exception text.

Existing auth/session expiry/revocation, tenant/assignment, exact CAS/approval,
safe media decoder/5MiB/4Mpx limits, 16KiB JSON bounds, redacted failures/audit,
login throttling and bounded isolated-worker controls remain authoritative.
No policy/provider/approval-service edit. Frontend dev proxy now rejects external,
credential-bearing or path/query-bearing targets; native package needs no proxy.

Operations: new private generated root only; Windows ACL owner+SYSTEM or POSIX
0700, random operator token separate from app bearer roles, per-root OS lease,
instance-verified stop without PID killing, one-hour deadline, explicit resume,
no implicit user reprovisioning or data deletion. Child environment drops API keys,
cloud credentials, proxy configuration and live flags. Demo never reads .env.
Logs omit request bodies/auth headers; no access logger or exception echo.

Package uses exact source allowlist, fixed ZIP metadata, per-file SHA-256 and
bounded safe verification/extraction. No .env, credentials, DB/media, private
markers/results, screenshots, node_modules, .venv, caches or runtime directory.
Digests detect changes; they are not signed provenance or tamper-proof storage.

Recommendations, NOT implemented production controls: HTTPS/reverse proxy,
production IdP/MFA, hard account lifecycle, distributed/IP limits, durable cloud
DB/object adapters, retention/deletion/orphan repair, encrypted off-machine backup,
load/chaos recovery, production monitoring and independent security review. No
HTTPS claim follows from a possible future proxy. Current loopback HTTP is for
fictional local data, never a public/customer service.

SQLite BEGIN IMMEDIATE serializes writers locally; no production throughput or
Firestore parity claim. Media and DB commits are separate; abrupt shutdown may
leave pending analysis or orphan bytes, always non-authorizing until current
checks pass. Native readiness cannot certify power-loss durability. Backup requires
a stopped service and matching media; no automatic destructive restore.

Cloud IAM service identities govern infrastructure access, not app roles or tenant
authorization. A later remote host needs separate approval of account/project,
cost, public/private access, durable persistence and scoped credentials. No IAM,
cloud resource, public tunnel, billing or deployment action is authorized here.
Gemini work remains frozen through 07; old private marker/result unchanged.
