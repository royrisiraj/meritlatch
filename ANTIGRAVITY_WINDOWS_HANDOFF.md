# Antigravity + OpenAI Codex — Windows handoff

This guide assumes **no existing code**. The Markdown/PDF files in this folder are requirements, not a runnable application.

## Before Codex

Open Antigravity IDE on the **folder that directly contains** `AGENTS.md` and `00_START_HERE.md`. In its PowerShell terminal:

```powershell
Get-Location
Get-ChildItem AGENTS.md, CODEX_FIRST_MESSAGE.md, reference
py -3 --version
node --version
git --version
```

A missing `py`, `node`, or `git` command is an environment issue to resolve before requiring Codex to run the corresponding checks. Codex can run from its CLI (`codex`) if installed and logged in, or from a compatible extension. **Do not run both Codex and Antigravity's built-in agent against the same files concurrently.**

Read and paste **the contents** of `CODEX_FIRST_MESSAGE.md`. Don't paste the entire 35-page PDF into a prompt: the PDF and an extracted searchable text copy are already in `reference/`. Ask Codex to finish Phase 00, then stop.

## For every next phase

```text
Read AGENTS.md and the Master Book. Read the previous phase's implementation and tests. Execute only prompts/0X_*.md, including its acceptance gate. Run actual tests and provide the result in the tracking/PHASE_GATE_REPORT_TEMPLATE.md format. Update status ledger and requirement matrix. Do not proceed to the next phase or begin appearance work without my approval.
```

Replace `0X_*.md` with the actual filename from `00_START_HERE.md`. Avoid asking for all phases in one chat turn because the agent may skip test gates.

## Practical secrets and deployment rules

- Create `.env` locally **only after** Phase 02 instructions and obtaining your own Gemini key. Never paste the key into agent messages or commit it.
- Demo/test users must have distinct authenticated roles. Changing tabs in a web page must not change security permissions.
- Production Cloud Run/Firestore/Cloud Storage may need billing, IAM and secrets; deployment is **not** automatic. Confirm scope and expenses before authorizing resources.
- Keep `SYNTHETIC` fixtures unmistakably labeled; record at least one successful `LIVE_GEMINI` result before claiming model integration.
- Keep your existing PowerPoint separately. Update slides from actual tested functionality and screenshots once the app exists.

## First user-facing milestone

FastAPI starts locally, `/healthz` and `/docs` work, a pure Python policy can be tested without Gemini, and the initial negative tests **actually pass**. The next milestone is server-authenticated roles, state transitions and atomic approvals—not UI polish.
