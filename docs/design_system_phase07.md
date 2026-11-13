# Phase 07 — Evidence and authority

Purpose: an industrial inspection workbench for evidence, accountable decisions
and reproducible security findings. The application frame is navy, work surfaces
are warm paper/white, and the `//` boundary before L3 denotes separate human
authority. This is operational UI, without decorative dashboards or scores.

## Tokens and components

Tokens live in frontend/src/style.css: navy #111C2B, paper #F4F3EF, ink #17232F,
muted #52606D, cobalt #2449D8, positive teal #006B60, attention amber #8A5000,
safety red #A52A36, surface #FFFFFF. Spacing uses 4/8/12/16/24/32/48px; corners
4–6px. System sans, 16px body/inputs, compact strong headings, tabular numbers,
system monospace for technical references. No font/CDN/library dependency added.

Shared ui.tsx primitives: PageHeading, Breadcrumb, Panel, TechnicalDetails,
LoadedState, Badge/Source, Ladder/CaseState, Fields, Comparison, GateResult,
MetricsView and AuditList. Original data-loading/mutation hooks are retained.
Native details/summary provides keyboard disclosures. Errors remain role=alert;
loaded-but-refreshing/failed state is explicitly marked. Status meaning always
uses text in addition to color. Source labels are deliberately neutral/dashed.

## Authority and workflows

The ladder is a noninteractive ordered list. Only backend max_permission selects
one current rung. Lower levels are reference levels, not completed milestones.
L3 explicitly requires a separate authenticated manager and means simulation only.
Case permission is not actor/assignment authorization. SAFETY_ALERT is visible
independently of L1; inspection, business, review and source remain separate.

Contractor evidence intake follows current restrictions and server guidance.
Manager evidence and one real decision form share a desktop split; narrow views
retain all binding information without a duplicated mobile form. Security findings
compare independent expected versus actual; rates retain counts, denominators,
N/A, SHOULD_DENY and separate review/abstention outcomes. Release readiness is
shown with full current/historical bindings and published=false.

No backend policy, approval, auth, upload, idempotency or gate rule is reimplemented
by presentation. Full technical bindings remain available. No private credential,
challenge or raw historical provider artifact belongs in a shared capture.

## Responsive and accessibility intent

Navigation wraps with labeled links. At narrow widths the four authority rungs
stack in DOM order; fields, comparisons and review layouts reflow. Controls are
at least 44px except native checkboxes within full clickable labels. Focus rings
remain explicit; reduced-motion disables transitions. No custom dialogs exist.
Actual browser widths/contrast samples, limitations and test results belong in
tracking/PHASE_07_REPORT.md; token selection alone is not accessibility certification.

The native wrapper serves the compiled JS/CSS with existing CSP and strict asset
hashes. Keep future font/icon additions subject to reviewed packaging constraints.
