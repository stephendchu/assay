"""Governance gate: turn eval signals into an auditable ship / hold decision.

The point of an eval in a high-consequence domain isn't a score — it's a
*decision you can defend.* The gate consumes cited claims and emits an
APPROVE / REVIEW / BLOCK verdict plus a provenance record: what was checked,
what failed, and why. That record is the audit trail.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from assay.grounding import is_grounded


class Verdict(str, Enum):
    APPROVE = "approve"
    REVIEW = "review"
    BLOCK = "block"


@dataclass(frozen=True)
class Claim:
    """A statement an AI made, with the source span it claims to be backed by."""

    text: str
    citation: str


@dataclass
class GateDecision:
    verdict: Verdict
    grounded: int
    ungrounded: int
    reasons: list[str] = field(default_factory=list)
    checked_at: str = field(
        default_factory=lambda: _dt.datetime.now(_dt.UTC).isoformat()
    )

    @property
    def total(self) -> int:
        return self.grounded + self.ungrounded


def evaluate(
    claims: Sequence[Claim],
    source: str,
    *,
    block_if_any_ungrounded: bool = True,
    min_chars: int = 12,
) -> GateDecision:
    """Decide whether a set of cited claims is safe to ship against `source`.

    Audit-first posture (default): ANY ungrounded claim BLOCKs — in a regulated
    decision you cannot act on a claim you cannot trace. Set
    `block_if_any_ungrounded=False` to route ungrounded claims to REVIEW instead.
    """
    grounded = ungrounded = 0
    reasons: list[str] = []
    for c in claims:
        if is_grounded(c.citation, source, min_chars=min_chars):
            grounded += 1
        else:
            ungrounded += 1
            reasons.append(f"ungrounded: {c.text!r} — citation not found in source")

    if ungrounded == 0:
        verdict = Verdict.APPROVE
    elif block_if_any_ungrounded:
        verdict = Verdict.BLOCK
    else:
        verdict = Verdict.REVIEW
    return GateDecision(
        verdict=verdict, grounded=grounded, ungrounded=ungrounded, reasons=reasons
    )
