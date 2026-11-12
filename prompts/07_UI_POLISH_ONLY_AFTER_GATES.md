# PHASE 07 — Refine UI only after workflow and tests are accepted

**Prerequisite:** all essential gates for actual backend, Gemini, authorization, red-team and functional portals are PASSED or their explicitly accepted demo limitations are documented. This phase is never permission to break the workflow.

## Design brief
- Original SENTINEL brand. Inspiration only: https://veriq.axiomjisu.tech/ and https://sayanghosh67.github.io/CyberTrust-360/#investigate. Inspect when possible; if a site cannot be accessed, say so rather than invent screenshots. No third-party code, graphics or brand copying.
- Purpose: an efficient security operations product, not a promotional landing page. Restrained dark navy/charcoal, cobalt/teal accent, legible typography, high contrast and informative status labels.
- UX priority: show case asset/job, evidence source/metadata uncertainty, **separate** inspection status vs permission L0–L3, required missing proof, clear next action, human review and red-team results.
- Visual red-team report must show dataset size, true/false approvals/rejections and policy version, not a fabricated success rate.
- Contractor flow should optimize camera upload and specific resubmission guidance; manager flow should prioritize queue and reviewer decisions; engineer flow should prioritize reproducible alerts. Responsive for laptop/tablet/mobile, accessible labels and keyboard nav.
- Add helpful microcopy, friendly but serious empty/error states and loading skeletons only where genuinely useful. No gratuitous animation, fake network topology or floating 3D decor.

## Acceptance
- Document accessible before/after screenshots of the real running UI, not concept mockups.
- Rerun backend tests, frontend tests and one complete contractor→manager→engineer journey, including direct-API role rejection.
- Verify privacy (no exposed secrets/raw customer media in public dashboard), performance and error states.
- Record actual changed files and rollback instructions; stop on regressions, prioritize restoring correctness.
