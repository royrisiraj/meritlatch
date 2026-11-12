# Implementation decisions

1. Scope follows `prompts/00_BOOTSTRAP.md`. Master Book chapters 1–24 and
   Appendices A–E were read through the supplied complete text. The original
   35-page PDF was parsed and pp.7–8,18,26,28 were inspected directly after
   extraction-order differences appeared. No conflict affecting this gate was found.
2. `/healthz`, `/docs`, `/openapi.json`, and Swagger's OAuth redirect helper are
   public operational/documentation routes. There are no business routes.
   Future APIs will use `/v1/...` consistently as specified; no `/api/v1` alias.
   Tests assert only `/healthz` appears in the operation schema and future paths
   return 404, so this does not claim implemented case authorization.
3. `authorize()` handles evidence eligibility only, capped at L2. No stub approval,
   database, mock provider, auth mechanism or challenge issuer is introduced.
   EvaluationContext is trusted caller data, kept separate from Observation.
4. The versioned fictional policy is scoped to one synthetic tenant/job/asset.
   Bounds are invented, both inclusive, and configurable; unit conversion is
   rejected. Calibration expiry is inclusive through its UTC date, challenge
   expiry exclusive. Missing/uncertain/conflicting data cannot earn L2.
5. Known out-of-range pressure and expired calibration take SAFETY_ALERT priority
   even with a stale challenge, while the failed challenge keeps permission L0.
   Missing pressure with known valid asset/challenge may retain L1 for a
   provisional visit. That is not an equipment safety conclusion.
6. Runtime/tests/reference-reader versions are pinned in `backend/requirements.txt`.
   `pyproject.toml` records direct runtime pins and pytest configuration. pypdf is
   a reference-reading tool only; the product imports no media/model SDK.
7. Only Python 3.14.7 is installed locally. All pinned packages' metadata permits
   3.11/3.12; actual execution on those versions remains unverified. CI is a
   scaffold for 3.11/3.12/3.14, not evidence of a completed run.

Rollback: stop the local server, revert modified tracking documents from a saved
copy, and remove only the newly created Phase 00 files listed in the gate report
after review. Keep all original reference/contract/prompt files. The repository
has no baseline commit; `git reset --hard`/`git clean` are inappropriate. No
rollback, commit, push, remote connection or deployment was performed.

## Phase 01 decisions — 12 November 2026

1. Preserve the accepted pure policy and every original test byte-for-byte.
   The Phase 00 API tests explicitly require no business routes on `main.app`.
   Retain that metadata bootstrap component and compose the functioning Phase 01
   application in `backend.app.api:create_app --factory`. New tests verify the
   actual Phase 01 routes, authentication and workflow; the old tests are not
   presented as tests of the new API. Startup instructions now use the factory.
2. Keep existing lower-case Action enum values instead of adding uppercase aliases
   from the Phase 01 prose. L0–L3 semantics match Master Book pp.7–8. Managers
   approve via `/approvals`; assigned agents execute business actions, consistent
   with the role matrix on p.13. Case views replace Phase 00-only guidance with
   current manager-review guidance without modifying the pure engine.
3. Manager creates job/case; contractor issues their own bound challenge afterwards.
   Issuing the contractor's challenge under the manager's authentication session
   would violate the required session boundary. Challenges still bind the case,
   tenant, job, asset and evidence session; only the server creates tokens/expiry.
4. Amounts are integer paise: INR 5,000 = 500000 paise. This avoids floating-point
   money comparisons. There is no payment processor or equipment integration.
5. SQLite `BEGIN IMMEDIATE` plus explicit case/job CAS versions serializes local
   writers and rejects stale writes. Clock sampling occurs after lock acquisition.
   An added regression found one pre-lock clock read in action execution; it was
   fixed and the test retained. State, approval, receipt and audit changes share
   the transaction. Expiry invalidation commits even on a version-conflict denial.
6. Synthetic intake is an internal test-factory function, not an endpoint or env
   flag. Its digest covers exact canonical fixture JSON bytes, not media. Normal
   settings refuse intake and promotion of saved test evidence. Real media/Gemini
   remain Phase 02 work.
7. Reviewed policies are append-only per-job versions. The accepted fixture is
   the initial trusted template. Additional versions require offline independent
   engineer authentication, a review reference and structural regression checks;
   registration does not activate them. The only policy HTTP operation selects
   a registered version, scoped to the assigned engineer, invalidating approval.
   No AI-written policy publication or Phase 04 assurance claim is introduced.
8. Local bearer sessions avoid cookie/CSRF coupling. No CORS allowance is enabled.
   Offline provisioning uses hidden prompts; startup seeds no default account.
   SQLite/schema migration and protocols provide a future adapter boundary;
   Firestore is not implemented or tested. Only SQLAlchemy==2.1.8 was added to
   dependencies; all original pins remain unchanged.

Phase 01 rollback: stop the local server cleanly and back up its SQLite database
with SQLite's backup API before changing code. Preserve the database/credentials
and all original kit files. Restore Phase 00 documentation/dependency declarations
from a saved copy and use `backend.app.main:app` for metadata-only operation.
Remove only the new Phase 01 files listed in its report after review; do not
delete the SQLite database or run destructive Git cleanup. No schema downgrade,
rollback, commit, push or deployment was performed.

## Phase 02 decisions — 12 November 2026

1. Extend the existing `backend.app.api:create_app --factory`. Preserve all 266
   existing tests byte-for-byte, the accepted pure engine/models and user commit
   `a7e7156`. Preserve the user's two pre-existing handover-file deletions. No
   new commit or reconstruction of missing instructions is authorized.
2. Use a raw JPEG/PNG body with explicit case-version/challenge/evidence-session
   headers. Avoid accepting observation JSON or trusting filenames/MIME. Disabled
   mode returns a scoped 404 after authentication; the earlier tests for absent
   intake in unconfigured normal operation therefore remain valid. Enabled mode
   has independent positive/negative image tests and an actual HTTP smoke.
3. Retain append-only core evidence. Add append-only media-upload/analysis tables
   and a separate initial media-schema migration; do not rewrite the established
   core version-1 migration or history. Phase 01 data is preserved in migration
   tests. New evidence stores original-byte SHA-256; legacy SYNTHETIC records keep
   their canonical-JSON digests. The two digest meanings are documented explicitly.
4. Reserve pending evidence and clear approval atomically before provider I/O.
   Recheck identity, case/evidence/policy/amount revision and challenge validity
   when finalizing. Do not hold a SQLite lock over network calls. Late results
   append a stale-analysis record and never replace current evidence authority.
5. Keep provider input to decoded metadata-stripped pixels and a source reference;
   do not supply expected answers, policies, actor secrets or approvals. Strict
   observation fields cannot assign roles/tiers/payments. SDK tools/function
   calling/automatic continuation and SDK hidden retries are disabled.
6. Modes are explicit: DISABLED by default, MOCK_AI for development/tests, or
   LIVE_GEMINI with a private key and explicit billing opt-in. Never fall back.
   Mock data cannot remain eligible after leaving mock mode. Existing SYNTHETIC
   injection remains internal-only. No synthetic HTTP route exists.
7. Official Google documentation lists stable `gemini-3.6-flash` with image input
   and structured outputs; use it as configurable default. This is documentation
   verification, not authenticated account/model availability or live success.
   Live smoke additionally needs a consented fictional image and human-reviewed
   ground truth; neither was supplied and no billable call was approved. Report
   live verification BLOCKED while keeping local mock/SDK-stub evidence separate.
8. Pillow, google-genai, dotenv and their new transitive dependencies are pinned;
   prior pins are unchanged. SDK-required httpx2 is now installed and Starlette
   uses it, so the previous TestClient deprecation warning is no longer emitted.
   A new decoder-warning test initially failed in fixture rendering before the
   validator ran; image creation was moved before the lowered test limit, keeping
   the rejection assertion. No original assertion was changed.
9. JPEG/PNG only; MP4/APNG and reanalysis/recovery/retention workflows are deferred.
   Duplicate bytes are conservatively rejected, including failed-attempt retries;
   no fraud finding is inferred. Storage is private by server routing, with local
   ACLs still an operator responsibility. Crash orphans/pending rows cannot grant
   permission, but automatic cleanup is not implemented.

Phase 02 rollback (not executed): stop the server, preserve/back up the SQLite
database and private media, restore only the Phase 02 tracked edits from a reviewed
baseline copy, and remove only new Phase 02 code if requested. Additive media
tables/files can remain safely preserved when running old code; do not drop them
or delete evidence as an automatic downgrade. Leave user deletions unchanged.
Do not reset the repository, remove the existing commit, or discard user data.
