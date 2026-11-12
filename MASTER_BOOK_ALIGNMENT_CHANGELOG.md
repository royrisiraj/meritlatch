# Master Book v2.0 alignment — what changed from the original Codex kit

**Authoritative source:** `reference/SENTINEL_LADDER_MASTER_BOOK_PREBUILD_V2.pdf` (35 pages; 12 November 2026). This package is a set of instructions; **no production source code, implemented APIs, measured metrics or deployment is contained in it**.

## Scope decisions

| Earlier handoff | This Master Book–aligned handoff | Master Book reference |
|---|---|---|
| Rework a prior starter app | Bootstrap an empty repo; earlier ZIP is **not** code to copy | pp.1–5, 28 |
| Four large prompts with a broad phase 1 | Eight sequential checkpoints starting with a small pure-policy kernel | pp.26, 28–29 |
| Model can report a visible reading | Strongly typed numerical reading + unit + domain-specific bounds | pp.8, 12–13, 18 |
| Permission level conflates safety and approval | Evidence/inspection status and L0–L3 authorization are distinct | pp.7–8 |
| Shared demo keys/role switcher | Backend-authenticated distinct contractor, manager, engineer and tenant scopes | pp.6, 13–14 |
| Generic reviewer approval | Transaction-bound, version-bound approval invalidated on any relevant change | pp.8, 14, 17 |
| Generic photo upload | Safe file parsing, scoped SHA-256 duplicate lookup, fresh challenge binding | pp.11–12, 18 |
| AI red-team output treated as discovered vulnerabilities | Independent labeled oracle, sandbox test, reproducible failure and human-reviewed regression gate | pp.15–16, 20 |
| Post-checkout red team as the only protection | Mandatory pre-release regression + scheduled/targeted audits | pp.15–16 |
| Start with fancy frontend | Swagger/API -> functional portals -> UI polish after tests | pp.10, 26, 28 |
| Deploy first or claim Gemini/demo success | Verify real media inference and authenticated flow; cloud deploy only with approval | pp.20, 26–28 |
| Gemma as hackathon model | Gemini now; Gemma model adapter possible only after measured compatibility | pp.12–13, 24 |
| Previous scoring/market claims | No official numerical category weights, no traction/benchmarks until measured | pp.20, 25, 33–34 |

## Exactly what to do next

1. Extract this ZIP in a new empty folder called `sentinel-ladder-v2`.
2. Open that folder in Antigravity IDE. Use Codex through the terminal or a compatible extension (not two coding agents on the same files simultaneously).
3. Paste **`CODEX_FIRST_MESSAGE.md`** into Codex. It directs Codex to run `prompts/00_BOOTSTRAP.md` only.
4. Evaluate actual output with **`tracking/PHASE_GATE_REPORT_TEMPLATE.md`**. Never declare success without executed tests.
5. Proceed through `prompts/01_...` to `07_...` one at a time after approval. **Do not start UI polish early.**

## Important scope boundary

The Master Book defines a safe, fictional maintenance inspection flow and a simulated INR 5,000 invoice. It does **not** authorize real payments, safety certification, self-editing permission policies, or claims that photographs establish real service completion. Claims of uniqueness, security benchmark improvement, and commercial viability require independently collected evidence.
