"""assay — audit-first evaluation primitives for AI in high-consequence domains.

Grounding, anti-fabrication gating, and (incoming) faithfulness, drift, and
honest baseline-vs-treatment experiments — the reusable core behind
filing-event-eval and agentic-test-eval.
"""
from assay.grounding import is_grounded
from assay.gate import Claim, GateDecision, Verdict, evaluate
from assay.graders import Grader, GroundingGrader, Score

__version__ = "0.0.1"
__all__ = [
    "is_grounded",
    "Claim",
    "GateDecision",
    "Verdict",
    "evaluate",
    "Grader",
    "GroundingGrader",
    "Score",
]
