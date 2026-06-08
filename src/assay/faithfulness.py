"""Faithfulness by entailment — does the EVIDENCE actually support the CLAIM?

`grounding.is_grounded` answers a narrower question ("is the cited span present in
the source?"). It can't catch a fluent, ungrounded rationale that cites a *real*
span, nor a true claim paraphrased from the source. This grader asks a model to
judge **entailment**, and is the faithfulness signal behind the gate for
natural-language claims.

The judge is injectable, so the grader is fully testable offline; the live default
calls the model in `assay.llm`. Recommended use: substring grounding as a cheap
pre-filter, entailment for anything that passes (or for prose claims).
"""
from __future__ import annotations

from typing import Callable, Optional

from assay.graders import Score

# A judge maps a prompt to raw model text.
Judge = Callable[[str], str]

_PROMPT = """You are a strict auditor checking whether evidence supports a claim.
Answer with exactly SUPPORTED or UNSUPPORTED on the first line, then one short
line of reason. Be conservative: if the evidence does not *directly* support the
claim, answer UNSUPPORTED.

CLAIM: {claim}
EVIDENCE: {evidence}
"""


def faithfulness(claim: str, evidence: str, *, judge: Optional[Judge] = None) -> Score:
    """1.0 if the evidence entails the claim, else 0.0 — carrying the judge's reason."""
    judge = judge or _default_judge
    raw = (judge(_PROMPT.format(claim=claim, evidence=evidence)) or "").strip()
    lines = raw.splitlines()
    verdict = lines[0].strip().upper() if lines else ""
    supported = verdict.startswith("SUPPORTED")
    reason = " ".join(line.strip() for line in lines[1:]).strip() or raw or verdict
    return Score(1.0 if supported else 0.0, reason)


def _default_judge(prompt: str) -> str:
    from assay.llm import complete

    return complete(prompt)
