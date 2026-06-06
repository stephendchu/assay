"""Run: python examples/quickstart.py   (after `pip install -e .`)

Shows the audit-first gate: an agent proposed two cited claims — one real, one
fabricated — and the gate refuses to ship the batch because one claim can't be
traced to the source. That refusal, with its reason, is the audit trail.
"""
from assay import Claim, GroundingGrader, evaluate

source = (
    "Apple's research and development expense was $34,550 million in fiscal 2025. "
    "The company did not disclose iPhone unit sales."
)

claims = [
    Claim("R&D was $34,550M", "research and development expense was $34,550 million"),
    Claim("iPhone units fell 8%", "iPhone unit sales declined 8 percent"),  # NOT in source
]

decision = evaluate(claims, source)
print(
    f"Verdict: {decision.verdict.value.upper()}  "
    f"(grounded={decision.grounded}, ungrounded={decision.ungrounded})"
)
for r in decision.reasons:
    print("  -", r)

# The same primitive as a composable grader:
grader = GroundingGrader()
print("\nPer-claim grades:")
for c in claims:
    s = grader.grade(c.citation, source=source)
    print(f"  [{s.value:.0f}] {c.text}  ({s.reason})")

print("\nThe gate refuses to ship a claim it cannot trace — that refusal is the audit trail.")
