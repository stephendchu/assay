"""Run the eval over the gold set.

Deterministic baseline always runs (no key). The LLM mapper runs too if a backend
is configured (ANTHROPIC_API_KEY, or the ASSAY_LLM_* free-backend vars).

    python examples/eval_demo.py
"""
from assay.apps.change_approval.gold import GOLD
from assay.eval import evaluate

print("=== deterministic baseline ===")
base = evaluate(GOLD, use_llm=False)
print(base)
for row in base.rows:
    print("   ", row)

try:
    from assay import llm

    llm.complete("ping", max_tokens=1)  # probe for a configured backend
    print(f"\n=== LLM mapper (live: {llm.model_id()}) ===")
    rep = evaluate(GOLD, use_llm=True)
    print(rep)
    for row in rep.rows:
        print("   ", row)
    print("\nCompare control-F1 and gate-acc: the LLM should beat the baseline on the "
          "partial-evidence cases by *omitting* unsupported controls instead of over-claiming.")
except Exception as exc:
    print(f"\n(LLM run skipped — no backend configured: {exc})")
    print("Set a key and re-run to get the live model-vs-baseline number.")
