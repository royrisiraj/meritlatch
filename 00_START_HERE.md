# SENTINEL//LADDER — Antigravity + Codex rebuild kit (Master Book v2.0)

**Status: instructions and reference materials only; no product code exists in this kit.**

## Authoritative source
- `reference/SENTINEL_LADDER_MASTER_BOOK_PREBUILD_V2.pdf` is the **authoritative** 35-page source, dated 12 November 2026.
- `reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt` is a convenience text extraction to let Codex search/read all chapters. If its formatting or text conflicts with the PDF, follow the PDF.
- `AGENTS.md` adds safety/implementation constraints consistent with the Master Book. `contracts/` elaborates proposed contracts to reduce ambiguity, **not** claims of existing endpoints.
- Do **not** copy the former SENTINEL starter ZIP or use earlier concept scores as measured results.

See also `ANTIGRAVITY_WINDOWS_HANDOFF.md`, `MASTER_BOOK_ALIGNMENT_CHANGELOG.md`, and `tracking/PHASE_GATE_REPORT_TEMPLATE.md` for Windows setup, changes from the former kit, and evidence-based phase acceptance.

## Exact setup in Antigravity IDE (Windows)
1. Create a NEW EMPTY folder, e.g. `sentinel-ladder-v2`, and extract this kit's files **directly** into it (keeping `prompts`, `reference`, `tracking`, `contracts`).
2. Open that folder in Google Antigravity IDE. In the integrated terminal check:

```powershell
py -3 --version
node --version
git --version
```

3. Start your installed OpenAI Codex extension or the Codex CLI (if CLI is installed, run `codex` in the repository root). Codex is distinct from Antigravity's own agent; avoid concurrent editing of the same files.
4. Open `CODEX_FIRST_MESSAGE.md` and paste it into Codex. Ask Codex to **execute Phase 00 only**.
5. Require Codex to show concrete test output, modified files, and a status ledger before giving it the next phase. Use **one prompt per checkpoint**. Do not ask Codex to execute the whole kit in one step.

## Build order (workflow > visuals)
| Milestone | Prompt | Evidence required before next phase |
|---|---|---|
| 00 | `prompts/00_BOOTSTRAP.md` | Python environment, health route, first failing/negative policy tests, CI scaffold |
| 01 | `prompts/01_POLICY_AUTH_CASES.md` | P0 permissions/roles/transactions/challenge tests pass |
| 02 | `prompts/02_SAFE_MEDIA_AND_GEMINI.md` | Safe image upload, model adapter, honest live/fixture traces and fail-closed tests |
| 03 | `prompts/03_COMPLETE_CASE_WORKFLOW.md` | Full L0–L3 API flow and concurrency tests pass |
| 04 | `prompts/04_REDTEAM_ALERTS.md` | Independent labels, false approval/rejection report, reproducible engineer alert |
| 05 | `prompts/05_THREE_FUNCTIONAL_PORTALS.md` | Contractor → manager → engineer journeys, role security enforced by API |
| 06 | `prompts/06_CLOUD_AND_THREE_MINUTE_DEMO.md` | Verified deployment if access available, 3 consecutive rehearsals, honest deck status |
| 07 | `prompts/07_UI_POLISH_ONLY_AFTER_GATES.md` | UI improvements after backend and E2E acceptance; no regressions |

The Master Book's **48-hour sprint** (chapter 21, p.26) front-loads real Gemini media and permission controls, followed by red-team, portals, deployment and rehearsal. Phases are a **quality gate sequence**, not promises of implementation within particular hours. Adapt time boxes while preserving the chapter's priorities.

## Fixed product scope
- First domain: fictional maintenance inspection of a specifically configured piece of equipment; INR 5,000 **mock** invoice.
- Three authenticated roles: contractor, manager, security engineer; optional service-agent identity with action-only scope.
- L0 draft only; L1 provisional visit; L2 prepare invoice *for human review*; L3 **simulated completion** after separately authenticated manager approval of current evidence, policy and amount.
- `SAFETY_ALERT`, `REVIEW_REQUIRED`, `EVIDENCE_MISSING`, `OBSERVATION_PENDING`, `EVIDENCE_COMPLETE` are **inspection statuses** separate from L0–L3.
- Gemini observes; pure deterministic Python policy authorizes. `UNKNOWN`/uncertain visual fields must never silently become safe.
- Human-reviewed adversarial test → engineering issue → regression → approved policy release. No uncontrolled code or policy self-mutation.
- No real transfers, bank/industrial device integrations, immutable-ledger claims, zero-fraud claims, or benchmark numbers until tests run.

## Local execution constraints
- Windows PowerShell commands in every milestone.
- Python/FastAPI, Pydantic v2, SQLAlchemy+SQLite for local, pytest. `google-genai` for live Gemini after configuration.
- React/Vite/TypeScript/Tailwind only when functional portals are built; **Swagger and a thin UI are sufficient before then**.
- Cloud Run with source-based deployment and provider adapters later. No Docker/WSL/GPU dependency.
- No secrets in source, screenshots, git, client scripts or logs.

## Agent reporting format (every phase)
1. Changed files / diff summary.
2. Actual commands executed (or precisely why a command could not run).
3. Tests with counts/results; separate unit, mocked AI, live Gemini, E2E, and cloud results.
4. Security invariants exercised and new gaps.
5. Requirements ledger updated with evidence path and status.
6. Next phase readiness: PASS/FAIL. Stop until user approves.

## External UI references (design inspiration only, Phase 07)
- https://veriq.axiomjisu.tech/
- https://sayanghosh67.github.io/CyberTrust-360/#investigate
Avoid copying source assets, branding, or pages. Workflow is more important than aesthetics.
