"""End-to-end demo of the change-approval workflow on the control plane.

    python examples/change_approval_demo.py
"""
import json
import tempfile
from pathlib import Path

from assay.apps.change_approval.app import build
from assay.apps.change_approval.controls import (
    CLEAN_CHANGE,
    FABRICATED_CHANGE,
    SELF_APPROVED_CHANGE,
)
from assay.plane.core import record_approval


def show(title, r):
    print(f"\n=== {title} ===")
    print(f"run_id : {r.run_id}")
    print(f"status : {r.status.value.upper()}")
    if "gate" in r.state:
        g = r.state["gate"]
        print(f"gate   : {g['verdict']} (grounded={g['grounded']}, ungrounded={g['ungrounded']})")


plane = build()
plane.root = Path(tempfile.mkdtemp()) / "runs"

# 1) Fabricated approval -> the anti-fabrication gate BLOCKS it.
r = plane.execute(FABRICATED_CHANGE)
show("Fabricated approval — should BLOCK at the gate", r)
for reason in r.state.get("gate", {}).get("reasons", []):
    print("  -", reason)

# 2) Clean change -> pauses for maker-checker, then approve & resume -> COMPLETED.
r = plane.execute(CLEAN_CHANGE)
show("Clean change — should pause AWAITING_APPROVAL", r)
record_approval(r.rundir, "change_approval", approver="a.singh")  # independent reviewer
r = plane.execute(CLEAN_CHANGE)  # resume from checkpoint
show("Clean change resumed after sign-off — should COMPLETE", r)
wp = json.loads((r.rundir / "artifacts" / "workpaper.json").read_text())
print("  workpaper conclusion:", wp["conclusion"])

# 3) Self-approval -> grounded, but the workpaper records the SoD deficiency.
r = plane.execute(SELF_APPROVED_CHANGE)
record_approval(r.rundir, "change_approval", approver="a.singh")
r = plane.execute(SELF_APPROVED_CHANGE)
show("Self-approved change — grounded, but SoD exception noted", r)
wp = json.loads((r.rundir / "artifacts" / "workpaper.json").read_text())
print("  exceptions:", wp["exceptions"])
print("  conclusion:", wp["conclusion"])

print("\nEvery decision above is in the tamper-evident audit.jsonl of each run dir.")
