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
from assay.grounding import is_grounded
from assay.plane.audit import AuditLog
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
    ctx.state["abstentions"] = []   # naive baseline never abstains (it over-claims instead)
    return StepResult(Status.OK, f"{len(claims)} controls mapped, {len(findings)} finding(s)")


def gate(ctx: RunContext) -> StepResult:
    src = _evidence_text(ctx.state["payload"])
    claims = [Claim(c["text"], c["citation"]) for c in ctx.state["claims"]]
    decision = evaluate(claims, src)
    abstentions = ctx.state.get("abstentions", [])
    verdict = decision.verdict
    if verdict is not Verdict.BLOCK and abstentions:
        verdict = Verdict.REVIEW              # the agent abstained -> escalate to a human
    ctx.state["gate"] = {
        "verdict": verdict.value,
        "grounded": decision.grounded,
        "ungrounded": decision.ungrounded,
        "abstentions": len(abstentions),
        "reasons": decision.reasons,
    }
    if verdict is Verdict.BLOCK:
        return StepResult(Status.BLOCKED,
                          f"anti-fabrication gate: {decision.ungrounded} unciteable assertion(s)")
    if verdict is Verdict.REVIEW:
        return StepResult(Status.OK, f"{len(abstentions)} abstention(s) -> routed to human review")
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

Return ONLY a JSON object:
{{"claims": [{{"control": "<id>", "text": "<short assertion>", "citation": "<span copied VERBATIM from evidence>"}}],
  "abstentions": [{{"control": "<id>", "reason": "<why you cannot determine it>"}}]}}

Rules: copy every citation verbatim from the EVIDENCE — never paraphrase or invent.
If the evidence is missing or too ambiguous to determine a control, put it under
"abstentions" (do NOT guess). Only put a control under "claims" when you can cite evidence.

CONTROLS:
{controls}

CHANGE (excluding evidence):
{change}

EVIDENCE:
{evidence}
"""


def _controls_text() -> str:
    return "\n".join(f"{cid}: {desc}" for cid, desc in CONTROLS.items())


def _parse_output(raw: str):
    """Tolerant parse of the model's output -> (claims, abstentions). Accepts a JSON
    array of claims (legacy) or a JSON object {"claims": [...], "abstentions": [...]}."""
    if not raw:
        return [], []
    s = raw.strip().strip("`").strip()
    if s[:4].lower() == "json":
        s = s[4:].strip()
    try:
        if s.lstrip().startswith("{"):
            obj = json.loads(s[s.find("{") : s.rfind("}") + 1])
            claims_raw, abst_raw = obj.get("claims", []), obj.get("abstentions", [])
        else:
            claims_raw, abst_raw = json.loads(s[s.find("[") : s.rfind("]") + 1]), []
    except Exception:
        return [], []
    claims = [{"control": str(d.get("control", "")), "text": str(d.get("text", "")),
               "citation": str(d.get("citation", ""))}
              for d in (claims_raw if isinstance(claims_raw, list) else [])
              if isinstance(d, dict) and d.get("citation")]
    abst = [{"control": str(d.get("control", "")), "reason": str(d.get("reason", ""))}
            for d in (abst_raw if isinstance(abst_raw, list) else []) if isinstance(d, dict)]
    return claims, abst


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

    claims, abstentions = _parse_output(raw)
    ctx.state["claims"] = claims
    ctx.state["abstentions"] = abstentions
    ev = change.get("evidence", {})
    findings = []
    if ev.get("approver") and ev["approver"] == change.get("author"):
        findings.append({"control": "ITGC-CM-02", "severity": "deficiency",
                         "detail": f"self-approval: {change['author']} approved their own change"})
    ctx.state["findings"] = findings
    return StepResult(Status.OK, f"{len(claims)} mapped, {len(abstentions)} abstained ({model})")


def _default_reviewer(summary: dict) -> dict:
    """Mock operator / human judge — a plain Python stand-in for an independent
    reviewer (in production, a person in a review UI). It applies its OWN policy on
    the independent re-check, never the agent's say-so."""
    failed = [c for c in summary["claims"] if not c["grounded_on_recheck"]]
    if failed:
        return {"reviewer": "ops.reviewer", "decision": "reject",
                "notes": f"{len(failed)} claim(s) failed independent re-check"}
    note = "claims re-verified; exceptions noted" if summary["exceptions"] else "claims re-verified"
    return {"reviewer": "ops.reviewer", "decision": "accept", "notes": note}


def independent_review(ctx: RunContext, reviewer=None) -> StepResult:
    """Management-review control OVER the agent. Independently re-performs each
    claim's citation check against the evidence (does NOT trust the agent), then
    hands off to an operator/judge (`reviewer`, injectable) for accept/reject.
    A separate code path from the agent — the preparer cannot validate its own work."""
    change = ctx.state["payload"]
    ev = _evidence_text(change)
    rechecked = [{"control": c["control"], "text": c["text"], "citation": c["citation"],
                  "grounded_on_recheck": is_grounded(c.get("citation", ""), ev)}
                 for c in ctx.state.get("claims", [])]
    summary = {"change_id": change["id"], "claims": rechecked,
               "exceptions": ctx.state.get("findings", []), "gate": ctx.state.get("gate", {})}
    verdict = (reviewer or _default_reviewer)(summary)
    ctx.artifact("independent_review.json", json.dumps({"summary": summary, "verdict": verdict}, indent=2))
    ctx.state["review"] = verdict
    if verdict.get("decision") != "accept":
        return StepResult(Status.BLOCKED, f"independent review: {verdict.get('decision')} — {verdict.get('notes', '')}")
    return StepResult(Status.OK, f"independently reviewed by {verdict.get('reviewer', 'operator')}")


def handoff_report(ctx: RunContext) -> StepResult:
    """Attestation report for an INDEPENDENT consuming team (audit / risk). Carries the
    audit-log head hash so the receiver can verify integrity — the producer can't
    silently rewrite history."""
    change = ctx.state["payload"]
    records = AuditLog(ctx.rundir / "audit.jsonl").records()
    head = records[-1]["hash"] if records else "genesis"
    report = {
        "to": "audit-risk (independent consumer)",
        "change_id": change["id"], "system": change.get("system"),
        "controls_tested": [c["control"] for c in ctx.state.get("claims", [])],
        "gate": ctx.state.get("gate", {}),
        "independent_review": ctx.state.get("review", {}),
        "exceptions": ctx.state.get("findings", []),
        "approval": ctx.state.get("approvals", {}).get("change_approval"),
        "conclusion": "exceptions noted" if ctx.state.get("findings") else "no exceptions",
        "audit_log_head": head,
        "verify": "AuditLog(<run>/audit.jsonl).verify() must be True; head must match audit_log_head",
    }
    ctx.artifact("handoff_report.json", json.dumps(report, indent=2))
    return StepResult(Status.OK, "handoff report issued to the independent consumer")


def build(*, use_llm: bool = False, judge=None, reviewer=None) -> Run:
    """`use_llm=True` swaps in the model-backed mapper (reproducible: temp 0, pinned
    model, prompt + raw output logged). `judge`/`reviewer` override the live model /
    the mock operator for offline tests. Default stays deterministic, key-free.

    SoD across the pipeline: agent (preparer) → gate (system) → independent review
    (operator/judge) → maker-checker (approver ≠ author) → handoff (consumer)."""
    mapper = (lambda ctx: map_controls_llm(ctx, judge)) if use_llm else map_controls
    return Run(name="change-approval", steps=[
        ("ingest", ingest),
        ("map_controls", mapper),
        ("gate", gate),
        ("independent_review", lambda ctx: independent_review(ctx, reviewer)),
        ("human_approval", human_approval),
        ("emit_workpaper", emit_workpaper),
        ("handoff_report", handoff_report),
    ])
