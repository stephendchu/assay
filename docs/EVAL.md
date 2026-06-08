# Evaluation — gold set + measured results

The review's sharpest hit (Anthropic ML engineer): *"the eval itself is unvalidated —
no gold set, no precision/recall, no honest experiment."* This is the answer: a
**human-verifiable** gold set + a harness that scores any control mapper with bootstrap
CIs, runnable offline (`python examples/eval_demo.py`).

## Gold set
[`src/assay/apps/change_approval/gold.py`](../src/assay/apps/change_approval/gold.py) — 5
synthetic, labeled change records (public/synthetic only). Each labels the controls the
evidence *grounds*, any seeded deficiency, and whether the gate should block. Starter set;
expand via the AI-draft → human-verify workflow in [VALIDATION.md](VALIDATION.md) — the
pass that breaks AI-grading-AI circularity.

## Metrics
- **Control mapping** — precision / recall / **F1** vs the labels.
- **Grounding rate** — fraction of the mapper's citations actually present in the evidence.
- **Deficiency accuracy** — did it flag the seeded SoD failure correctly?
- **Gate efficacy** — did the gate's block/allow match the label?

All aggregated with a **percentile bootstrap CI**.

## Result — deterministic baseline (n=5)
```
control-F1 = 0.87 [0.73, 1.00]   grounding = 0.80   deficiency-acc = 1.00   gate-acc = 0.60
```
| change | F1 | grounding | gate | correct? |
|---|---|---|---|---|
| CHG-1042 (clean) | 1.00 | 1.00 | approve | ✅ |
| CHG-1120 (clean) | 1.00 | 1.00 | approve | ✅ |
| CHG-1101 (self-approval) | 1.00 | 1.00 | approve + SoD finding | ✅ |
| CHG-1077 (missing test evidence) | 0.67 | 0.50 | **block** | ❌ |
| CHG-1099 (no approval evidence) | 0.67 | 0.50 | **block** | ❌ |

### The honest finding
The deterministic baseline **over-claims** — it asserts every control regardless of
evidence — so on **partial-evidence** changes it cites absent spans, which the
anti-fabrication gate (correctly) flags as ungrounded, and it **over-blocks**
(gate-acc **0.60**). A real weakness surfaced by the eval, not a vanity number.

## The experiment (LLM vs baseline)
The LLM mapper is prompted to **omit** controls the evidence doesn't support, so it should
beat the baseline on the two partial-evidence cases (higher precision, fewer false blocks)
— *unless* it fabricates citations, which the gate would catch. Run it:
```
export ANTHROPIC_API_KEY=...          # or the free ASSAY_LLM_* backend
python examples/eval_demo.py
```
The live model-vs-baseline number will be reported here **as it lands — including an
honest null** if the model doesn't beat the baseline.

## What this answers from the review
- 🤖 *"the eval is unvalidated"* → gold set + P/R/F1 + bootstrap CIs + a real, honest finding.
- 💼 CFO *"show me a number"* → control-F1 0.87, gate-acc 0.60, with CIs.
- 🏛️/🧮 *completeness / self-review* → **named, not hidden** (see Scope & limits, forthcoming):
  the gold set is small and synthetic; recall is "vs the labels we wrote," not omniscience.

*Public / synthetic data only.*
