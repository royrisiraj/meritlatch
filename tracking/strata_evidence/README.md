# MeritLatch / Strata — actual local browser evidence

All captures show the real React application and existing FastAPI backend, with
fictional local data. Perception is ordinary UNKNOWN or explicitly acknowledged
**MOCK_AI — CANNED DEMONSTRATION / NOT VERIFIED LIVE IMAGE EXTRACTION**; engineering
is **SYNTHETIC SECURITY EVALUATION**. No live Gemini, payment, equipment control,
production deployment or certification is represented.

## Core screens

| Surface | Actual captures |
|---|---|
| Strata split login | [1440px](strata-login-1440.png), [375px](strata-login-375.png), [768px](strata-login-768.png), [320px](strata-login-320.png) |
| Contractor | [Assigned work](03-contractor-dashboard-mobile.png), [unsafe L1](04-contractor-unsafe-mobile.png), [correction upload](05-contractor-correction-upload-mobile.png) |
| Case reflow | [320px](06-contractor-case-320.png), [375px](06-contractor-case-375.png), [768px](06-contractor-case-768.png), [1440px](06-contractor-case-1440.png) |
| Manager | [Queue](02-manager-queue-desktop.png), [evidence/decision](07-manager-evidence-review-desktop.png), [tablet](08-manager-review-tablet.png), [bound L3](09-manager-approved-desktop.png) |
| Engineer | [Overview](10-engineer-overview-desktop.png), [findings](12-engineer-findings-desktop.png), [expected/actual](13-engineer-finding-comparison-desktop.png), [exact metrics](11-engineer-synthetic-metrics-desktop.png), [unpublished gate](15-engineer-unpublished-gate-desktop.png), [tablet gate](16-engineer-gate-tablet.png) |
| Restricted service agent | [Desktop](strata-agent-1440.png), [mobile](strata-agent-375.png) |
| Job creation | [Desktop](strata-job-form-1440.png), [tablet](strata-job-form-768.png), [375px](strata-job-form-375.png), [320px](strata-job-form-320.png) |
| Compiled native package | [Login](native-login.png), [manager](native-manager.png), [actual run](result.json) |

36 PNGs total include additional shell/width variants. Password and challenge areas
are masked during capture; gray/magenta rectangles are masks, not application UI.
No bearer/operator token, private media path or historical provider artifact is
shown. The fictional white evidence card is actual uploaded media and deliberately
retains its original pixels rather than being recolored to suit the dark theme.
Original screenshots remain untouched; no fabricated mockup or edited image.

## Before / after

| Previous accepted application | Implemented Strata application |
|---|---|
| [Phase07 sign-in](../phase07_evidence/01-login-desktop.png) | [MeritLatch split sign-in](strata-login-1440.png) |
| [Phase07 manager review](../phase07_evidence/07-manager-evidence-review-desktop.png) | [Strata manager review](07-manager-evidence-review-desktop.png) |
| [Phase07 finding](../phase07_evidence/13-engineer-finding-comparison-desktop.png) | [Strata finding](13-engineer-finding-comparison-desktop.png) |
| [Phase07 metrics](../phase07_evidence/11-engineer-synthetic-metrics-desktop.png) | [Strata metrics](11-engineer-synthetic-metrics-desktop.png) |

Different isolated runs/record IDs; these are genuine before/after screens, not
pixel-identical fixtures. The supplied Strata HTML was consulted as a visual
specification, never shipped as an authentication implementation. Screenshot
checkpoints for desktop/mobile auth/shell and populated operational views were
visually inspected before subsequent passes. Final representative views were
inspected again, including restriction, metrics, gate, tablet and native serving.

## Accessibility evidence

Six computed-style samples are included as JSON: primary/secondary button,
active navigation, current permission, safety notice text and input boundary.
Text samples pass4.5:1; input boundary passes3:1. Actual keyboard login order,
native disclosure Enter/focus, reduced motion, one manager form and 44px challenge
control are asserted by the original/new browser tests. No horizontal page
overflow at asserted320/375/768/1440 views. No screen-reader, real-device or full
WCAG certification; viewport reflow does not establish actual browser zoom behavior.
No custom dialogs or decorative motion were added.

[Report](../STRATA_VISUAL_OVERHAUL_REPORT.md),
[design system](../../docs/strata_design_system.md),
[integrity manifest](MANIFEST.json). Digests are not signatures or tamper-proof
provenance. Native release archive excludes this screenshot/evidence directory.
