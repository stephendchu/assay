"""LIVE demo of the model-backed control mapper. Pick a backend first:

  Claude (portfolio default):   export ANTHROPIC_API_KEY=sk-ant-...
  Free (Groq, etc.):            export ASSAY_LLM_PROVIDER=openai \\
                                       ASSAY_LLM_BASE_URL=https://api.groq.com/openai/v1 \\
                                       ASSAY_LLM_API_KEY=gsk_... \\
                                       ASSAY_LLM_MODEL=llama-3.3-70b-versatile

Then:  python examples/change_approval_llm_demo.py
"""
import json
import tempfile
from pathlib import Path

from assay import llm
from assay.apps.change_approval.app import build
from assay.apps.change_approval.controls import (
    CLEAN_CHANGE,
    FABRICATED_CHANGE,
    SELF_APPROVED_CHANGE,
)

print(f"backend: {llm.model_id()}  (temperature 0)\n")
plane = build(use_llm=True)  # the real model maps controls
plane.root = Path(tempfile.mkdtemp()) / "runs"

for change in (CLEAN_CHANGE, FABRICATED_CHANGE, SELF_APPROVED_CHANGE):
    r = plane.execute(change)
    g = r.state.get("gate", {})
    print(f"=== {change['id']} -> {r.status.value.upper()} ===")
    if g:
        print(f"  gate: {g['verdict']}  (grounded={g['grounded']}, ungrounded={g['ungrounded']})")
        for reason in g.get("reasons", []):
            print("   -", reason)
    for c in r.state.get("claims", []):
        print(f"   model mapped {c['control']}: cited “{c['citation'][:70]}…”")
    print()

print("Every run logged its model id + exact prompt + raw output to "
      "artifacts/llm_mapping.json — re-performable for audit.")
