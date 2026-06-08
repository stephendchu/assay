"""Change-Approval reference workflow on the control plane (SOX ITGC change mgmt).

Flow: ingest -> map change to ITGC controls (cited) -> anti-fabrication GATE ->
maker-checker human approval -> auditable workpaper.

The control mapping is deterministic and rule-based here; an LLM mapper can drop
in behind the same step interface later. The point of the slice is the *governed
process* (gate + SoD approval + audit trail), not the model.
"""
from __future__ import annotations

import json

from assay import llm
from assay.apps.change_approval.controls import CONTROLS
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


_MAP_PROMPT = """You are a SOX ITGC auditor. Given a change record and its evidence,
decide which controls are satisfied and cite the EXACT evidence text for each.

Return ONLY a JSON array; each item:
{{"control": "<id>", "text": "<short assertion>", "citation": "<span copied VERBATIM from the evidence>"}}
Copy every citation verbatim from the EVIDENCE — never paraphrase or invent. Omit any
control the evidence does not support.

CONTROLS:
{controls}

CHANGE (excluding evidence):
{change}

EVIDENCE:
{evidence}
"""


def _controls_text() -> str:
    return "\n".join(f"{cid}: {desc}" for cid, desc in CONTROLS.items())


def _parse_claims(raw: str) -> list[dict]:
    """Tolerant parse of the model's JSON array of cited control assertions."""
    if not raw or "[" not in raw or "]" not in raw:
        return []
    try:
        data = json.loads(raw[raw.find("[") : raw.rfind("]") + 1])
    except Exception:
        return []
    out = []
    for d in data if isinstance(data, list) else []:
        if isinstance(d, dict) and d.get("citation"):
            out.append({"control": str(d.get("control", "")),
                        "text": str(d.get("text", "")),
                        "citation": str(d.get("citation", ""))})
    return out


def map_controls_llm(ctx: RunContext, judge=None) -> StepResult:
    """Model-backed control mapping. Reproducible: temperature 0, pinned model, and
    the full prompt + raw response + model id logged for re-performance/audit.
    `judge` (a prompt->text callable) overrides the live model for offline tests."""
    change = ctx.state["payload"]
    prompt = _MAP_PROMPT.format(
        controls=_controls_text(),
        change=json.dumps({k: v for k, v in change.items() if k != "evidence"}),
        evidence=_evidence_text(change),
    )
    if callable(judge):
        raw, model = judge(prompt), "injected-judge"
    else:
        raw, model = llm.complete(prompt, temperature=0.0), llm.model_id()

    ctx.artifact("llm_mapping.json", json.dumps(
        {"model": model, "temperature": 0, "prompt": prompt, "response": raw}, indent=2))

    ctx.state["claims"] = _parse_claims(raw)
    ev = change.get("evidence", {})
    findings = []
    if ev.get("approver") and ev["approver"] == change.get("author"):
        findings.append({"control": "ITGC-CM-02", "severity": "deficiency",
                         "detail": f"self-approval: {change['author']} approved their own change"})
    ctx.state["findings"] = findings
    return StepResult(Status.OK, f"{len(ctx.state['claims'])} controls mapped by model ({model})")


def build(*, use_llm: bool = False, judge=None) -> Run:
    """`use_llm=True` swaps in the model-backed mapper (reproducible: temp 0, pinned
    model, prompt + raw output logged). `judge` overrides the live model for offline
    tests. Default stays deterministic so the suite runs with no key."""
    mapper = (lambda ctx: map_controls_llm(ctx, judge)) if use_llm else map_controls
    return Run(name="change-approval", steps=[
        ("ingest", ingest),
        ("map_controls", mapper),
        ("gate", gate),
        ("human_approval", human_approval),
        ("emit_workpaper", emit_workpaper),
    ])
