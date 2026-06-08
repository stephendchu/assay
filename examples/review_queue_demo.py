"""Stratified human-review queue over the gold set (deterministic; no key).

    python examples/review_queue_demo.py
"""
import tempfile
from pathlib import Path

from assay.apps.change_approval.app import build
from assay.apps.change_approval.gold import GOLD
from assay.review import review_queue

items = []
for case in GOLD:
    run = build(use_llm=False)
    run.root = Path(tempfile.mkdtemp()) / "runs"
    r = run.execute(case["change"])
    items.append({"id": case["change"]["id"],
                  "verdict": r.state.get("gate", {}).get("verdict", r.status.value)})

q = review_queue(items, sample_rate=0.5)
print(f"population={q['population']}  full-review (blocks+abstentions)={q['full_review']}  "
      f"approvals sampled {q['approvals_sampled']}/{q['approvals_total']}")
for row in q["queue"]:
    print(f"   {row['id']:>10}  {row['verdict']:<8}  <- {row['why']}")
print("\n" + q["note"])
