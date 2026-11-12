# PHASE 02 — Evidence intake + first actual Gemini observation

Read Master Book chapters 6–8,12–15,21 and Appendix A. Preserve earlier tests. **This phase is a priority in the 48-hour sprint; use the smallest reliable real image path.**

## Build
1. `POST /v1/cases/{id}/evidence` for authenticated assigned contractor. Support JPEG/PNG first, optional short MP4 ONLY if JPEG/PNG path reliable and cost/latency understood. Reject spoofed content types by parsing actual bytes; enforce byte/pixel (and frame if video) limits; randomized storage names; private local storage and future cloud adapter.
2. Compute SHA-256 and compare with scoped previously submitted media; duplicate status and policy reason. Do not claim semantic duplicate or authenticity proof. Optionally parse EXIF/GPS as untrusted supporting claims; absence is `UNKNOWN`, not fraud.
3. Persist evidence versions atomically; any new evidence invalidates previous approval. Challenge must match active job/asset/session and expire in server time.
4. `PerceptionProvider` protocol with `MockPerceptionProvider` and `GeminiPerceptionProvider` using `google-genai` SDK and structured observation schema. Provider outputs values, `UNKNOWN`/uncertainty, and optionally frames/field explanations; **never** tier, approval or financial decisions.
5. Validate schema AND semantics; normalize numeric units/dates through the approved fictional policy; discard instructions found in image. Return `REVIEW_REQUIRED` for incomplete/conflicting interpretation; timeout/failure -> no escalation.
6. Add a controlled real Gemini smoke command (credentials from `.env`, never browser) that measures model ID, latency and extracted fields. **If user has not provided credentials, do not invent success:** report live smoke BLOCKED while mocked tests remain valid.
7. Add clearly labeled `provider_mode` in data, logs and future UI. No live `Gemma` required; adapter architecture should make swapping possible later but not promise accuracy or private installation.

## Tests and evidence
- MIME spoof, invalid/huge images, duplicate SHA-256, wrong tenant, expired/old token, prompt injection text on image, Gemini schema mismatch, missing numeric value, provider timeout/quota/exception.
- Real image reading should be compared against **manual ground-truth fields**, never inferred from model's self-confidence. Record media/fixture origin with consent.
- A successful new upload cannot preserve previous L3; prove via tests.
- L2 is only for complete approved observations. A visible but unsafe gauge reading => `SAFETY_ALERT`, **not** L2.

## Gate
- One uploaded image results in inspectable structured observations and a policy decision; mocked path reproducible, real path attempted only with permission/credentials and reported accurately.
- Show tests, failures, sample API response, command traces, cost/latency if actually measured. Stop for approval before Phase 03. Do not build decorative frontend.
