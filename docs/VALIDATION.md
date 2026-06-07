# Validation — what the validation team does

The control plane governs *each run*. The validation team governs *whether the AI is
good enough to trust* — measured, not assumed.

## Golden dataset
- **Construction:** the AI drafts candidate change→control mappings and evidence
  judgments; **a human verifies** (keep / drop / fix, add anything missed). That human
  pass breaks the AI-grading-AI circularity — an unverified AI gold set is worthless.
- **Composition:** clean cases + **seeded deficiencies** with known labels
  (self-approval, retroactive approval, missing test evidence, fabricated approval).
- **Governance:** versioned, change-reviewed; the gold set is itself an audited artifact.

## Metrics
| Metric | Question |
|---|---|
| **Precision / recall** | did the AI map the right controls (and miss none)? |
| **Faithfulness** | is the rationale supported by the cited evidence? |
| **Deficiency accuracy** | did it call exceptions — and severity — correctly? |
| **Gate efficacy** | did the anti-fabrication gate catch the fabricated cases? |

## Acceptance gates
- The AI judgment step ships only if it clears agreed thresholds on the **verified**
  gold set.
- A null or regression is **reported honestly** — nothing ships on an unproven
  improvement.
- ▶ Thresholds, sample sizes, and re-validation cadence are set by the validation owner.

*Golden data is synthetic and human-verified; never employer audit data.*
