# Fixed independent synthetic security corpus v1

`scenarios_v1.json` defines deterministic input mutations. `labels_v1.json` is a
separate static oracle authored from accepted Master Book pp.7–8,13–14,17–20 and
the domain contracts. `manifest_v1.json` pins both files. No expected value is
derived by executing the policy under test. Inputs and labels are joined by exact
scenario ID/version; missing, duplicate, orphan and conflicting labels fail closed.

All 38 scenarios are **SYNTHETIC / SPECIFICATION_REFERENCE**. No additional human
dataset review or Gemini generation is claimed (`human_review_claimed=false`).
HUMAN_LABELED/PENDING_REVIEW types are guarded for future use; the current API
accepts no scenario/label uploads. Suggestions are disabled under the Gemini freeze.

| IDs | Target | Scope |
|---|---|---|
| P01–P24 | Existing pure policy | Legitimate/boundary/L1/L2 cases; missing/mismatched/expired evidence, NaN/infinity, units, unsafe pressure/tag expiry, uncertainty, authority-field injection, L2≠L3 and policy mismatch. |
| A01–A09 | Isolated authenticated API | Valid/unsafe invoice evaluation; contractor/engineer approval denials, Tenant B access to Tenant A, unassigned job, exact image replay, stale evidence version, concurrent invoice mutation. |
| B01–B05 | Read-only binding verifier snapshots | Current binding, replaced evidence, changed invoice/policy and disabled reviewer. No approval record or business action is created. |

The source-controlled base policy remains fictional 30–40 PSI; it is not industrial
safety guidance. Candidate-only in-memory variants deliberately expand max to 50
or restrict min to 36. They are not deployable policy files. Unsafe 45-PSI A02
expects API DENY, while P15 expects pure NEEDS_REVIEW/SAFETY_ALERT. The weakened
candidate actually returns ALLOW; independent labels remain unchanged.

Positive binary class=should DENY. Review/abstention cases stay separate from TP/
FN/TN/FP and rate denominators; exact inspection/permission/reason mismatch fails
the scenario and release gate even with a restrictive decision. The complete
scoring rules, API and limitations are in [assurance_phase04.md](../../docs/assurance_phase04.md).
Synthetic counts do not measure real-world attack/fraud detection or perception.
