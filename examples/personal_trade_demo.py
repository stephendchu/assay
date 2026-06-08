"""PAD surveillance over the synthetic trades (deterministic baseline; no key).

    python examples/personal_trade_demo.py
"""
import json
import tempfile
from pathlib import Path

from assay.apps.personal_trade.app import build
from assay.apps.personal_trade.data import ALL

plane = build(use_llm=False)
plane.root = Path(tempfile.mkdtemp()) / "runs"

for trade in ALL:
    r = plane.execute(trade)
    art = r.rundir / "artifacts" / "pad_report.json"
    rep = json.loads(art.read_text()) if art.exists() else {"conclusion": r.status.value, "violations": []}
    g = r.state.get("gate", {})
    print(f"  {trade['id']}  {trade['symbol']:<8} -> {rep['conclusion']:<18} "
          f"(gate={g.get('verdict', '-')}, violations={len(rep.get('violations', []))})")

print("\nThe baseline MISSES the late-approval (TRD-003) — it doesn't extract dates; the LLM does.")
print("Fabricated approvals are caught by the GATE; informal/ambiguous ones PUNT to a human.")
