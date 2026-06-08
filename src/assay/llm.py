"""Thin Anthropic client for the model-backed graders (key-gated, lazily imported).

Live model calls need `ANTHROPIC_API_KEY` (export it, or put it in `assay/.env`).
The eval core stays import- and test-clean without it: graders take an *injectable*
judge and only fall back to this when none is supplied.
"""
from __future__ import annotations

import os

try:  # best-effort: load assay/.env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

DEFAULT_MODEL = os.environ.get("ASSAY_JUDGE_MODEL", "claude-sonnet-4-6")


def complete(prompt: str, *, model: str | None = None, max_tokens: int = 256) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set — export it or add it to assay/.env to run "
            "the model-backed graders."
        )
    import anthropic  # lazy import keeps the eval core dependency-free

    client = anthropic.Anthropic(api_key=key, max_retries=3)
    msg = client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
