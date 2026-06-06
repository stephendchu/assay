"""Grounding: is a claim's citation actually present, verbatim, in the source?

The cheapest, most defensible faithfulness signal — no LLM judge, no fuzziness.
A claim is grounded only if its cited span appears (whitespace/case-normalized)
in the source text. In a high-consequence domain this is the floor: a claim
whose citation cannot be located in the source is, by definition, unverifiable.
"""
from __future__ import annotations

import re

_WS = re.compile(r"\s+")


def _normalize(s: str) -> str:
    """Collapse whitespace and lowercase — so formatting differences don't matter."""
    return _WS.sub(" ", s).strip().lower()


def is_grounded(citation: str, source: str, *, min_chars: int = 12) -> bool:
    """True iff `citation` appears (normalized) in `source`.

    Citations shorter than `min_chars` are rejected: a tiny overlap ("was",
    "the") proves nothing and would let fabricated claims pass on coincidence.
    """
    c = _normalize(citation)
    if len(c) < min_chars:
        return False
    return c in _normalize(source)
