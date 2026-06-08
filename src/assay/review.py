"""Build a stratified human-review queue from a population of run results.

Assurance at scale = review everything risky (blocks + abstentions) at 100%, plus a
stratified **sample** of the clean approvals to bound the missed-error rate — not a
human reading every item. (See docs/VALIDATION.md.)
"""
from __future__ import annotations

import random


def review_queue(items, *, sample_rate: float = 0.2, seed: int = 0) -> dict:
    """`items`: list of {"id", "verdict", ...}. Returns the queue + coverage summary.

    Blocks and abstentions ("review") are queued at 100%; approvals are
    stratified-sampled (deterministic given `seed`).
    """
    must_review = [it for it in items if it.get("verdict") in ("block", "review")]
    approvals = [it for it in items if it.get("verdict") == "approve"]
    k = min(len(approvals), round(len(approvals) * sample_rate))
    sampled = random.Random(seed).sample(approvals, k) if k else []

    queue = (
        [{**it, "why": "exception" if it["verdict"] == "block" else "abstention/uncertain"}
         for it in must_review]
        + [{**it, "why": "sampled assurance"} for it in sampled]
    )
    return {
        "population": len(items),
        "full_review": len(must_review),
        "approvals_total": len(approvals),
        "approvals_sampled": len(sampled),
        "sample_rate": sample_rate,
        "queue": queue,
        "note": ("Blocks + abstentions reviewed 100%; approvals stratified-sampled. "
                 "Raise sample_rate to tighten the bound on the missed-error rate."),
    }
