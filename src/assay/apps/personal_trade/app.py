"""Personal-account-dealing (PAD) surveillance — domain #2 on the assay plane.

Reconciles an employee TRADE against messy evidence (Legal pre-approvals, emails,
brokerage statement) + reference data (blackout list, covered accounts), and checks the
PAD rules. Two layers of defense, on purpose:

  - the **grounding gate** catches *fabricated* evidence (an invented pre-approval);
  - **deterministic checks** decide the rule *logic* (timing, blackout) — never the
    model's say-so;
  - **abstention** routes the genuinely ambiguous cases (an informal "go ahead" that
    isn't a formal pre-clearance) to a human.

PUBLIC / SYNTHETIC ONLY.
"""
from __future__ import annotations

import json

from assay import llm
from assay.apps.personal_trade.data import BLACKOUT, COVERED_ACCOUNTS
from assay.gate import Claim, Verdict, evaluate
from assay.plane.core import Run, RunContext, Status, StepResult

RULES = {
    "PAD-1": "A Legal pre-clearance must exist and PRE-DATE the trade.",
    "PAD-3": "No trade in a security on the blackout list as-of the trade date.",
    "PAD-4": "Trades in covered (employee + family) accounts are in scope.",
}


def _evidence(trade) -> str:
    """All normalized evidence sources joined (the adapter layer would feed this)."""
    parts = [str(v) for v in trade.get("evidence", {}).values() if v]
    return "  ".join(parts) or "[no evidence on file]"


def ingest(ctx: RunContext) -> StepResult:
    ctx.state["trade_id"] = ctx.state["payload"]["id"]
    return StepResult(Status.OK, f"ingested {ctx.state['payload']['id']}")


def _parse_pad(raw: str):
    """Tolerant parse -> (claims, abstentions), preserving rule + approval_date."""
    if not raw:
        return [], []
    s = raw.strip().strip("`").strip()
    if s[:4].lower() == "json":
        s = s[4:].strip()
    try:
        if s.lstrip().startswith("{"):
            obj = json.loads(s[s.find("{") : s.rfind("}") + 1])
        else:
            obj = {"claims": json.loads(s[s.find("[") : s.rfind("]") + 1]), "abstentions": []}
    except Exception:
        return [], []
    claims = [{"rule": str(d.get("rule", "")), "text": str(d.get("text", "")),
               "citation": str(d.get("citation", "")), "approval_date": str(d.get("approval_date", ""))}
              for d in (obj.get("claims", []) if isinstance(obj.get("claims"), list) else [])
              if isinstance(d, dict) and d.get("citation")]
    abst = [{"rule": str(d.get("rule", "")), "reason": str(d.get("reason", ""))}
            for d in (obj.get("abstentions", []) if isinstance(obj.get("abstentions"), list) else [])
            if isinstance(d, dict)]
    return claims, abst


_ASSESS_PROMPT = """You are a personal-account-dealing (PAD) compliance analyst.
Decide ONLY whether a valid **Legal pre-clearance** exists for THIS trade, and cite it.

Return ONLY JSON:
{{"claims": [{{"rule": "PAD-1", "text": "pre-cleared by Legal before the trade",
              "citation": "<span copied VERBATIM from EVIDENCE>", "approval_date": "YYYY-MM-DD"}}],
  "abstentions": [{{"rule": "PAD-1", "reason": "<why you cannot confirm a formal pre-clearance>"}}]}}

Rules: cite verbatim from EVIDENCE; never invent. An informal "go ahead" / casual email is
NOT a formal Legal pre-clearance — if you cannot confirm a formal pre-clearance naming this
security, ABSTAIN (do NOT guess).

TRADE: {trade}
EVIDENCE: {evidence}
"""


def assess_llm(ctx: RunContext, judge=None) -> StepResult:
    trade = ctx.state["payload"]
    prompt = _ASSESS_PROMPT.format(
        trade=json.dumps({k: v for k, v in trade.items() if k != "evidence"}),
        evidence=_evidence(trade))
    if callable(judge):
        raw, model = judge(prompt), "injected-judge"
    else:
        raw, model = llm.complete(prompt, temperature=0.0), llm.model_id()
    ctx.artifact("assessment.json", json.dumps(
        {"model": model, "temperature": 0, "prompt": prompt, "response": raw}, indent=2))
    claims, abst = _parse_pad(raw)
    ctx.state["claims"], ctx.state["abstentions"] = claims, abst
    return StepResult(Status.OK, f"{len(claims)} cited, {len(abst)} abstained ({model})")


def assess_baseline(ctx: RunContext) -> StepResult:
    """Honest deterministic baseline: assert pre-clearance only if a formal APPROVED line
    names this security; otherwise abstain (never guess). It does NOT extract dates — so it
    misses the *late-approval* case, which is where the LLM earns its place."""
    trade = ctx.state["payload"]
    ev = _evidence(trade)
    claims, abst = [], []
    if "APPROVED" in ev.upper() and trade["symbol"].upper() in ev.upper():
        claims.append({"rule": "PAD-1", "text": "pre-cleared by Legal", "citation": ev})
    else:
        abst.append({"rule": "PAD-1", "reason": "no formal pre-clearance naming this security"})
    ctx.state["claims"], ctx.state["abstentions"] = claims, abst
    return StepResult(Status.OK, f"{len(claims)} cited, {len(abst)} abstained (deterministic)")


def gate(ctx: RunContext) -> StepResult:
    ev = _evidence(ctx.state["payload"])
    claims = [Claim(c.get("text", ""), c.get("citation", "")) for c in ctx.state.get("claims", [])]
    decision = evaluate(claims, ev)
    abst = ctx.state.get("abstentions", [])
    verdict = decision.verdict
    if verdict is not Verdict.BLOCK and abst:
        verdict = Verdict.REVIEW
    ctx.state["gate"] = {"verdict": verdict.value, "grounded": decision.grounded,
                         "ungrounded": decision.ungrounded, "abstentions": len(abst),
                         "reasons": decision.reasons}
    if verdict is Verdict.BLOCK:
        return StepResult(Status.BLOCKED, f"anti-fabrication gate: {decision.ungrounded} unciteable claim(s)")
    if verdict is Verdict.REVIEW:
        return StepResult(Status.OK, f"{len(abst)} abstention(s) -> human review")
    return StepResult(Status.OK, "claims grounded in evidence")


def rules(ctx: RunContext) -> StepResult:
    """Deterministic rule logic — the verdicts are computed, never the model's say-so."""
    trade = ctx.state["payload"]
    sym, td = trade["symbol"].upper(), trade["trade_date"]
    violations = []
    win = BLACKOUT.get(sym)
    if win and win[0] <= td <= win[1]:
        violations.append({"rule": "PAD-3", "detail": f"{sym} on blackout {win[0]}..{win[1]}; traded {td}"})
    for c in ctx.state.get("claims", []):
        if c.get("rule") == "PAD-1" and c.get("approval_date") and c["approval_date"] > td:
            violations.append({"rule": "PAD-1", "detail": f"pre-clearance dated {c['approval_date']} AFTER trade {td}"})
    if trade["account"] not in COVERED_ACCOUNTS:
        violations.append({"rule": "PAD-4", "detail": f"account {trade['account']} not in covered set"})
    ctx.state["violations"] = violations
    return StepResult(Status.OK, f"{len(violations)} rule violation(s)")


def emit_report(ctx: RunContext) -> StepResult:
    trade = ctx.state["payload"]
    v, a = ctx.state.get("violations", []), ctx.state.get("abstentions", [])
    report = {"trade_id": trade["id"], "employee": trade["employee"], "symbol": trade["symbol"],
              "gate": ctx.state.get("gate", {}), "violations": v, "abstentions": a,
              "conclusion": "VIOLATION" if v else ("NEEDS HUMAN REVIEW" if a else "clear")}
    ctx.artifact("pad_report.json", json.dumps(report, indent=2))
    return StepResult(Status.OK, f"report: {report['conclusion']}")


def build(*, use_llm: bool = False, judge=None) -> Run:
    assessor = (lambda ctx: assess_llm(ctx, judge)) if use_llm else assess_baseline
    return Run(name="personal-trade-compliance", steps=[
        ("ingest", ingest),
        ("assess", assessor),
        ("gate", gate),
        ("rules", rules),
        ("emit_report", emit_report),
    ])
