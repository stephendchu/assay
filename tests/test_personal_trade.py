import json

from assay.apps.personal_trade.app import build
from assay.apps.personal_trade.data import (
    AMBIGUOUS,
    BLACKOUT_TRADE,
    CLEAN,
    LATE_APPROVAL,
    NO_APPROVAL,
)
from assay.plane.core import Status


def _approves(citation, approval_date):
    return lambda _p: json.dumps({"claims": [{"rule": "PAD-1", "text": "pre-cleared before trade",
                                              "citation": citation, "approval_date": approval_date}],
                                  "abstentions": []})


def _fabricates(_p):
    # cites an approval that is NOT in the (no-approval) evidence
    return json.dumps({"claims": [{"rule": "PAD-1", "text": "pre-cleared",
                                   "citation": "Pre-clearance APPROVED for u.chu to BUY GADGET. — Legal",
                                   "approval_date": "2026-03-05"}], "abstentions": []})


def _abstains(_p):
    return json.dumps({"claims": [],
                       "abstentions": [{"rule": "PAD-1", "reason": "informal email, not a formal pre-clearance"}]})


def test_clean_trade_clears(tmp_path):
    j = _approves("Pre-clearance APPROVED for u.chu to BUY WIDGET, valid 2026-03-04 to 2026-03-06. — Legal", "2026-03-04")
    run = build(use_llm=True, judge=j); run.root = tmp_path
    r = run.execute(CLEAN)
    assert r.status is Status.COMPLETED
    rep = json.loads((r.rundir / "artifacts" / "pad_report.json").read_text())
    assert rep["conclusion"] == "clear"


def test_fabricated_preapproval_is_blocked(tmp_path):
    run = build(use_llm=True, judge=_fabricates); run.root = tmp_path
    r = run.execute(NO_APPROVAL)                      # evidence says none; the model invents one
    assert r.status is Status.BLOCKED and r.state["gate"]["ungrounded"] >= 1


def test_late_preapproval_is_a_violation(tmp_path):
    j = _approves("Pre-clearance APPROVED for u.chu to BUY SPROCKET on 2026-03-08. — Legal", "2026-03-08")
    run = build(use_llm=True, judge=j); run.root = tmp_path
    r = run.execute(LATE_APPROVAL)
    assert any(v["rule"] == "PAD-1" for v in r.state["violations"])   # caught by the deterministic timing check


def test_blackout_trade_is_a_violation(tmp_path):
    j = _approves("Pre-clearance APPROVED for u.chu to BUY ACME, valid 2026-03-09 to 2026-03-11. — Legal", "2026-03-09")
    run = build(use_llm=True, judge=j); run.root = tmp_path
    r = run.execute(BLACKOUT_TRADE)
    assert any(v["rule"] == "PAD-3" for v in r.state["violations"])   # grounded approval, but blacked out


def test_ambiguous_punts_to_human(tmp_path):
    run = build(use_llm=True, judge=_abstains); run.root = tmp_path
    r = run.execute(AMBIGUOUS)
    assert r.state["gate"]["verdict"] == "review"
    rep = json.loads((r.rundir / "artifacts" / "pad_report.json").read_text())
    assert rep["conclusion"] == "NEEDS HUMAN REVIEW"
