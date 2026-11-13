# Phase 07 — actual local application evidence

These are real Chromium captures from the final eight-test run. Data is fictional;
positive observations are **MOCK_AI — CANNED DEMONSTRATION**, **NOT VERIFIED LIVE
IMAGE EXTRACTION**. Security results are **SYNTHETIC SECURITY EVALUATION**.
No customer, live perception, real payment, equipment safety or cloud result is
represented here. Magenta blocks are explicit screenshot privacy masks, not UI.

| Screen | Captured evidence |
|---|---|
| Login | [Desktop](01-login-desktop.png); blank password field masked; visible route focus ring. |
| Manager queue | [Desktop table](02-manager-queue-desktop.png), scoped loaded-page count and independent state/source columns. |
| Contractor worklist | [375px](03-contractor-dashboard-mobile.png), asset and next server-permitted task first. |
| Contractor restriction | [Unsafe L1](04-contractor-unsafe-mobile.png), safety warning separate from authority. |
| Contractor correction | [Upload](05-contractor-correction-upload-mobile.png), challenge masked; actual selected fictional PNG and explicit submission. |
| Case reflow | [320px](06-contractor-case-320.png), [375px](06-contractor-case-375.png), [768px](06-contractor-case-768.png), [1440px](06-contractor-case-1440.png). |
| Manager review | [Desktop](07-manager-evidence-review-desktop.png), [tablet](08-manager-review-tablet.png), [approved](09-manager-approved-desktop.png). Single form with full digest/version/amount context. |
| Engineer overview | [Desktop](10-engineer-overview-desktop.png), actual initial empty-state counts. |
| Regression | [Metrics](11-engineer-synthetic-metrics-desktop.png), weak candidate 36/38, 1/26 false approvals, 0/6 false rejections, one separate review bypass. |
| Findings | [Register](12-engineer-findings-desktop.png), [comparison](13-engineer-finding-comparison-desktop.png), [375px](14-engineer-finding-375.png), [768px](14-engineer-finding-768.png). |
| Independent release gate | [Desktop](15-engineer-unpublished-gate-desktop.png), [tablet](16-engineer-gate-tablet.png), actual READY_FOR_MANUAL_RELEASE and published=false. |
| Compiled native package | [Manager](17-native-manager.png), [execution record](native-result.json); different fresh isolated state. |

Before/after references preserve original Phase 06 evidence:

| Before | After | Change |
|---|---|---|
| [Phase 06 unsafe mobile](../phase06_evidence/01-unsafe-canned.png) | [Phase 07 unsafe mobile](04-contractor-unsafe-mobile.png) | Distinct safety/authority states; intake before current observations; metadata disclosure. |
| [Phase 06 manager](../phase06_evidence/02-simulated-completion.png) | [Phase 07 manager](09-manager-approved-desktop.png) | Evidence/decision split and inspectable exact approval binding. |
| [Phase 06 finding](../phase06_evidence/03-reproduced-finding.png) | [Phase 07 finding](13-engineer-finding-comparison-desktop.png) | Aligned expected denial versus actual allowance, context and technical references. |
| [Phase 06 gate](../phase06_evidence/04-independent-unpublished-readiness.png) | [Phase 07 gate](15-engineer-unpublished-gate-desktop.png) | Section index, full reviewer/run binding and distinct unpublished gate result. |

These compare different genuine isolated executions, not identical record IDs or
pixel-matched fixtures. Original files are unchanged. Twelve representative views
(login, queue, contractor dashboard/restriction/upload, manager desktop/tablet,
engineer overview/findings/comparison/metrics/gate) were visually inspected; other
width captures additionally support automated reflow assertions.

Five measured computed-style contrast samples are stored as JSON: primary button
6.95:1, secondary button 17.15:1, active navigation 6.28:1, current permission
17.15:1 and safety notice 9.26:1. Each passed 4.5:1; this is a sample, not a full
WCAG audit. Native disclosures were operated using Enter with visible focus;
login Tab order, reduced motion, upload touch height and single approval form
were checked in the actual browser. Width checks are not a real-device/browser
zoom or assistive-technology certification. No dialogs were introduced.

All 21 PNGs are copied from actual test outputs. Password/challenge masks are
applied during capture; no bearer/control token, private media path or historical
Gemini artifact was captured. Raw DBs/credentials/failure traces stay ignored.
[Report and limitations](../PHASE_07_REPORT.md),
[design system](../../docs/design_system_phase07.md), [checksums](MANIFEST.json).
