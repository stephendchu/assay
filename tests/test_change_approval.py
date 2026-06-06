import json

from assay.apps.change_approval.app import build
from assay.apps.change_approval.controls import (
    CLEAN_CHANGE,
    FABRICATED_CHANGE,
    SELF_APPROVED_CHANGE,
)
from assay.plane.core import Status, record_approval


def test_fabricated_approval_is_blocked(tmp_path):
    run = build()
    run.root = tmp_path
    res = run.execute(FABRICATED_CHANGE)
    assert res.status is Status.BLOCKED
    assert res.state["gate"]["ungrounded"] >= 1


def test_clean_change_pauses_then_completes(tmp_path):
    run = build()
    run.root = tmp_path
    res = run.execute(CLEAN_CHANGE)
    assert res.status is Status.AWAITING_APPROVAL          # maker-checker pause

    record_approval(res.rundir, "change_approval", approver="a.singh")
    res = run.execute(CLEAN_CHANGE)                        # resume from checkpoint
    assert res.status is Status.COMPLETED
    wp = json.loads((res.rundir / "artifacts" / "workpaper.json").read_text())
    assert wp["conclusion"] == "no exceptions"


def test_self_approval_is_flagged_as_exception(tmp_path):
    run = build()
    run.root = tmp_path
    res = run.execute(SELF_APPROVED_CHANGE)               # grounded -> gate passes
    assert res.status is Status.AWAITING_APPROVAL
    record_approval(res.rundir, "change_approval", approver="a.singh")
    res = run.execute(SELF_APPROVED_CHANGE)
    assert res.status is Status.COMPLETED
    wp = json.loads((res.rundir / "artifacts" / "workpaper.json").read_text())
    assert any(f["control"] == "ITGC-CM-02" for f in wp["exceptions"])
