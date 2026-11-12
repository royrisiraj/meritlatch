# Choices and reconciliation against Master Book v2.0

| Choice in revised kit | Why | Master Book grounding |
|---|---|---|
| New empty repo; old MVP ignored | Pre-build existence ledger deliberately starts at zero | pp.1–5,28 |
| Full PDF + extracted plain-text included | Codex must actually read source, not rely on prior summarization | p.2 and 28 |
| Python policy, auth/transaction before UI | Prevent unsupported agent action at real API boundary | pp.7–8,11,13–14,28 |
| Live Gemini shortly after core policy | Match 48-hour sprint priority, don't defer the model until end | pp.12–13,26 |
| Typed numeric measurements (not reading_visible) | Prior critical weakness; enforce domain-specific policies | pp.8,18 |
| Separate `SAFETY_ALERT` from L0–L3 | Unsafe measurement cannot promote permissions | pp.7–8 |
| SQLite local + repository interface for Firestore | No Docker local, future Cloud Run durability without premature provision | pp.11,14–15,28 |
| Three authenticated roles and thin frontend | Source includes contractor, manager, engineer experiences | pp.6,13 |
| Red team with independent oracle and release gate | Generated cases are suggestions; no AI policy auto-edit | pp.16,20 |
| Post-checkout tests sampled, not every action | Preventive pre-release gating must precede deployment | pp.15–16 |
| Full functionality before premium UI | User priority and smallest verifiable vertical slice | pp.10,26,28 |
| No invented score/test results | Master Book says no prototype/benchmarks | pp.1–5,20,25 |
| Vendor-independent perception, Gemma future | Private deployment is a hypothesis, not MVP dependency | pp.12–13,24 |

## Risks to review before production
- Browser app security (session cookies, CSRF, CORS and tenant authorization) is more than a visual role switch.
- Authenticity is not proven by correct challenge text, EXIF, GPS, SHA-256 or Gemini anomaly labels.
- Current case and approvals must be transactionally consistent; SQLite logic requires real concurrency tests. Firestore backend adapter must replicate transaction semantics before deployment.
- Sample pressure bounds must be described as fictional rather than industrial safety standards.
- Google Cloud costs and rate limits need observed benchmarks. Never assert free or instant API operation.
