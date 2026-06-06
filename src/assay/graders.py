"""Graders: a small, uniform interface over rule / model / heuristic checks.

Every eval in a high-consequence domain reduces to: take an output, return a
score in [0, 1] plus a defensible reason. Concrete graders (grounding here;
model-judge and heuristic graders later) all satisfy the same protocol, so they
compose in experiments and gates without special-casing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from assay.grounding import is_grounded


@dataclass(frozen=True)
class Score:
    value: float  # 0.0–1.0
    reason: str


class Grader(Protocol):
    name: str

    def grade(self, output: str, *, source: str) -> Score: ...


@dataclass
class GroundingGrader:
    """Binary grounding grader: 1.0 if the output is verbatim in the source."""

    min_chars: int = 12
    name: str = "grounding"

    def grade(self, output: str, *, source: str) -> Score:
        ok = is_grounded(output, source, min_chars=self.min_chars)
        return Score(
            1.0 if ok else 0.0,
            "citation verbatim in source" if ok else "citation not found in source",
        )
