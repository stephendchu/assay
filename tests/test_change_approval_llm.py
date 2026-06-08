"""Model-backed control mapping — tested fully offline with an injected judge."""
import json

from assay.apps.change_approval.app import build
from assay.apps.change_approval.controls import CLEAN_CHANGE
from assay.plane.core import Status, record_approval


def _grounded_judge(_prompt):
    # cites spans VERBATIM from CLEAN_CHANGE's evidence
    return json.dumps([
        {"control": "ITGC-CM-01", "text": "authorized before deployment",
         "citation": "Change CHG-1042 approved by j.lee on 2026-03-04, prior to deployment."},
        {"control": "ITGC-CM-03", "text": "tested with documented results",
         "citation": "Unit and regression tests passed; results attached 2026-03-03."},
    ])


def _fabricating_judge(_prompt):
    # cites an approval that is NOT in the evidence — the hallucination the gate must catch
    return json.dumps([
        {"control": "ITGC-CM-01", "text": "authorized",
         "citation": "Approved by the CEO on January 1st."},
    ])


def test_llm_grounded_mapping_flows_to_approval(tmp_path):
    run = build(use_llm=True, judge=_grounded_judge); run.root = tmp_path
    res = run.execute(CLEAN_CHANGE)
    assert res.status is Status.AWAITING_APPROVAL          # gate passed -> maker-checker
    record_approval(res.rundir, "change_approval", approver="a.singh")
    res = run.execute(CLEAN_CHANGE)
    assert res.status is Status.COMPLETED


def test_llm_fabricated_citation_is_blocked(tmp_path):
    run = build(use_llm=True, judge=_fabricating_judge); run.root = tmp_path
    res = run.execute(CLEAN_CHANGE)
    assert res.status is Status.BLOCKED                    # anti-fabrication gate catches it
    assert res.state["gate"]["ungrounded"] >= 1


def test_llm_mapping_is_logged_for_reproducibility(tmp_path):
    run = build(use_llm=True, judge=_grounded_judge); run.root = tmp_path
    res = run.execute(CLEAN_CHANGE)
    rec = json.loads((res.rundir / "artifacts" / "llm_mapping.json").read_text())
    assert rec["temperature"] == 0 and rec["prompt"] and rec["response"]


def test_independent_review_accepts_grounded(tmp_path):
    run = build(use_llm=True, judge=_grounded_judge); run.root = tmp_path
    res = run.execute(CLEAN_CHANGE)
    assert res.status is Status.AWAITING_APPROVAL          # passed gate + independent review
    assert res.state["review"]["decision"] == "accept"


def test_independent_reviewer_can_reject(tmp_path):
    reject = lambda summary: {"reviewer": "ops", "decision": "reject", "notes": "not satisfied"}
    run = build(use_llm=True, judge=_grounded_judge, reviewer=reject); run.root = tmp_path
    res = run.execute(CLEAN_CHANGE)
    assert res.status is Status.BLOCKED                     # the operator, not the agent, stopped it


def test_handoff_report_carries_audit_hash(tmp_path):
    run = build(use_llm=True, judge=_grounded_judge); run.root = tmp_path
    res = run.execute(CLEAN_CHANGE)
    record_approval(res.rundir, "change_approval", approver="a.singh")
    res = run.execute(CLEAN_CHANGE)
    assert res.status is Status.COMPLETED
    rep = json.loads((res.rundir / "artifacts" / "handoff_report.json").read_text())
    assert rep["audit_log_head"] and rep["independent_review"]["decision"] == "accept"
    assert rep["to"].startswith("audit-risk")


def _abstaining_judge(_prompt):
    return json.dumps({
        "claims": [{"control": "ITGC-CM-01", "text": "authorized",
                    "citation": "Change CHG-1042 approved by j.lee on 2026-03-04, prior to deployment."}],
        "abstentions": [{"control": "ITGC-CM-03", "reason": "no test evidence found"}],
    })


def test_abstention_routes_to_review(tmp_path):
    run = build(use_llm=True, judge=_abstaining_judge); run.root = tmp_path
    res = run.execute(CLEAN_CHANGE)
    assert res.state["gate"]["verdict"] == "review"      # abstained -> human, not auto-approve
    assert res.state["gate"]["abstentions"] == 1
    assert res.status is Status.AWAITING_APPROVAL
