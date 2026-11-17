# MeritLatch — implemented Strata Obsidian Cobalt

The complete user-supplied integration handoff, adapted HTML preview and token
stylesheet define this implementation. They were read as design specifications;
preview scripts, simulated authentication, unsupported identity providers, theme
export controls and certification claims were not imported. The stylesheet
`frontend/src/strata-tokens.css` is an exact copy of the supplied tokens.

## Surfaces, geometry and typography

Application #07080B; surface #0C0E15; raised #131722; input #090B10. Primary text
#F8FAFC, secondary #94A3B8, accent #3B82F6 and hover #2563EB. Cards 16px,
inputs 10px, buttons 12px; subtle/strong rgba-white borders, restrained shadows.
System/local font fallbacks only: no Google Fonts, Tailwind CDN or external asset.
Small technical labels use system monospace; operational text remains16px.

CSS retains supplied token names/values. For actual accessible combinations,
filled buttons use the supplied darker cobalt #2563EB with white text (the brighter
#3B82F6 remains the main interaction/geometry accent). Inputs use #52627B borders
for 3:1 boundary contrast; informational labels use secondary text or #A8B6C9 rather
than the lower-contrast muted token. Active nav uses an opaque dark cobalt surface
#131E36 so its contrast is explicit. These narrow adjustments preserve the preset.

## Authentication and shared shell

Desktop splits editorial and real auth card approximately 50/50. The editorial
contains the MeritLatch mark, exact approved copy, environment badge and a static
26-node geometric mesh. It stacks on mobile. `strata.tsx` supplies inline SVG
geometry, aria-hidden/focusable=false; no animation loop, pointer listeners,
timers, network, theme drawer or auth behavior. Static geometry inherently respects
reduced motion and incurs no canvas frame work. Narrow views scale it responsively.

The form still calls the original FastAPI login with tenant/username/password,
uses memory-only bearer sessions and routes by authenticated server identity.
Welcome back is the main heading; a small Sign in to your workspace subheading
retains the existing semantic/test contract. No registration, OAuth, magic-link,
reset, remember-device, sample account or fake success control. Operational pages
use a compact brand header and role navigation, not the sign-in editorial hero.
SERVICE_AGENT has no empty navigation landmark or links to other role portals.

## Operational views

The same surface/radius/input/navigation system covers worklists, queue/table,
case evidence, one manager decision form, engineer comparisons/metrics/review/gate,
job forms, agent simulation, audit and errors. Valid status colors retain their
separate meaning: red safety/failure, amber caution, teal actual positive states;
cobalt indicates interaction/current permission, never fabricated approval.

Ladder rungs use geometric marks and one server-current highlight; the L3 human
boundary and downward-retraction semantics remain explicit. Expected/actual
comparison highlights a reported decision discrepancy, without calculating policy
or permissions. Complete hashes/versions/amount/reviewer remain inspectable.
Synthetic metrics retain denominators, SHOULD_DENY, N/A and separate review values.
No policy publication or real payment/equipment control is added.

## Verification and limits

Real Chromium screenshots were inspected between bounded passes and again at the
final gate. 320/375/768/1440px widths, native disclosures, keyboard order/focus,
touch targets, reduced motion and sampled text/input contrast are tested. No
custom dialogs. Screen readers, non-Chromium browsers, real devices, actual high
zoom and complete WCAG conformance remain unverified; viewport reflow is not a
claim of assistive-technology certification.

Native packaging remains unchanged: SVG is bundled React markup, tokens become
compiled CSS, no new file type/CDN/CSP allowance. See
[acceptance report](../tracking/STRATA_VISUAL_OVERHAUL_REPORT.md) and
[actual evidence](../tracking/strata_evidence/README.md).
