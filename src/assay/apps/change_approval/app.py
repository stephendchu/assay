"""Change-Approval reference workflow on the control plane (SOX ITGC change mgmt).

Flow: ingest -> map change to ITGC controls (cited) -> anti-fabrication GATE ->
maker-checker human approval -> auditable workpaper.

The control mapping is deterministic and rule-based here; an LLM mapper can drop
in behind the same step interface later. The point of the slice is the *governed
process* (gate + SoD approval + audit trail), not the model.
"""
from __future__ import annotations

import json

from assay.gate import Claim, Verdict, evaluate
from assay.plane.core import Run, RunContext, Status, StepResult


def _evidence_text(change: dict) -> str:
    """Everything the agent is allowed to cite: the change's own evidence."""
    return " ".join(str(v) for v in change.get("evidence", {}).values())


def ingest(ctx: RunContext) -> StepResult:
    change = ctx.state["payload"]
    ctx.state["change_id"] = change["id"]
    return StepResult(Status.OK, f"ingested {change['id']}")


def map_controls(ctx: RunContext) -> StepResult:
    change = ctx.state["payload"]
    ev = change.get("evidence", {})

    claims = [
        {"control": "ITGC-CM-01", "text": "change authorized prior to deployment",
         "citation": ev.get("approval", "")},
        {"control": "ITGC-CM-03", "text": "tested with documented results",
         "citation": ev.get("test_signoff", "")},
    ]

    findings = []
    if ev.get("approver") and ev["approver"] == change.get("author"):
        findings.append({"control": "ITGC-CM-02", "severity": "deficiency",
                         "detail": f"self-approval: {change['author']} approved their own change"})

    ctx.state["claims"] = claims
    ctx.state["findings"] = findings
    return StepResult(Status.OK, f"{len(claims)} controls mapped, {len(findings)} finding(s)")


def gate(ctx: RunContext) -> StepResult:
    src = _evidence_text(ctx.state["payload"])
    claims = [Claim(c["text"], c["citation"]) for c in ctx.state["claims"]]
    decision = evaluate(claims, src)
    ctx.state["gate"] = {
        "verdict": decision.verdict.value,
        "grounded": decision.grounded,
        "ungrounded": decision.ungrounded,
        "reasons": decision.reasons,
    }
    if decision.verdict is Verdict.BLOCK:
        return StepResult(Status.BLOCKED,
                          f"anti-fabrication gate: {decision.ungrounded} unciteable assertion(s)")
    return StepResult(Status.OK, "all control assertions grounded in evidence")


def human_approval(ctx: RunContext) -> StepResult:
    """Maker-checker: a human independent of the change author must sign off."""
    change = ctx.state["payload"]
    appr = ctx.state.get("approvals", {}).get("change_approval")
    if not appr:
        ctx.artifact("approval_request.json", json.dumps(
            {"change_id": change["id"], "author": change.get("author"),
             "asks": "independent reviewer sign-off (maker-checker)"}, indent=2))
        return StepResult(Status.AWAITING_APPROVAL, "awaiting independent reviewer sign-off")
    if appr.get("approver") == change.get("author"):
        return StepResult(Status.BLOCKED, "maker-checker violation: approver == author")
    return StepResult(Status.OK, f"approved by {appr.get('approver')}")


def emit_workpaper(ctx: RunContext) -> StepResult:
    change = ctx.state["payload"]
    workpaper = {
        "change_id": change["id"],
        "system": change.get("system"),
        "controls_tested": [c["control"] for c in ctx.state["claims"]],
        "gate": ctx.state["gate"],
        "exceptions": ctx.state["findings"],
        "approval": ctx.state.get("approvals", {}).get("change_approval"),
        "conclusion": "exceptions noted" if ctx.state["findings"] else "no exceptions",
    }
    ctx.artifact("workpaper.json", json.dumps(workpaper, indent=2))
    return StepResult(Status.OK, "workpaper issued")


def build() -> Run:
    return Run(name="change-approval", steps=[
        ("ingest", ingest),
        ("map_controls", map_controls),
        ("gate", gate),
        ("human_approval", human_approval),
        ("emit_workpaper", emit_workpaper),
    ])
