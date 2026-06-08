"""Provider-flexible, key-gated LLM client for the model-backed graders/mappers.

Built for reproducibility (an auditor must be able to re-perform the control):
calls default to **temperature 0**, and callers log the model id + prompt + raw
output. The eval core stays import- and test-clean: graders/steps take an
*injectable* judge and only fall back to this when none is supplied.

Backends (set `ASSAY_LLM_PROVIDER`):
  - `anthropic` (default) — Claude, the portfolio default.  Needs ANTHROPIC_API_KEY.
  - anything else — an **OpenAI-compatible** endpoint (Groq / OpenRouter / Together /
    local Ollama …): set ASSAY_LLM_BASE_URL, ASSAY_LLM_API_KEY, ASSAY_LLM_MODEL.
    Lets the live test run on a free platform; swap to Claude for the demo.
"""
from __future__ import annotations

import os

try:  # best-effort: load assay/.env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

PROVIDER = os.environ.get("ASSAY_LLM_PROVIDER", "anthropic").lower()
_DEFAULT_MODELS = {"anthropic": "claude-sonnet-4-6"}
DEFAULT_MODEL = os.environ.get("ASSAY_LLM_MODEL") or _DEFAULT_MODELS.get(PROVIDER, "")


def model_id() -> str:
    """Identifier logged with every call so a run can be re-performed exactly."""
    return f"{PROVIDER}:{DEFAULT_MODEL or '<unset>'}"


def complete(prompt: str, *, temperature: float = 0.0, max_tokens: int = 512) -> str:
    if PROVIDER == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set — export it or add it to assay/.env "
                "(or set ASSAY_LLM_PROVIDER to a free OpenAI-compatible backend)."
            )
        import anthropic  # lazy

        client = anthropic.Anthropic(api_key=key, max_retries=3)
        msg = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")

    # OpenAI-compatible (free platforms: Groq / OpenRouter / Ollama / …)
    base = os.environ.get("ASSAY_LLM_BASE_URL")
    if not base or not DEFAULT_MODEL:
        raise RuntimeError(
            "For a free OpenAI-compatible backend set ASSAY_LLM_BASE_URL, "
            "ASSAY_LLM_API_KEY, and ASSAY_LLM_MODEL."
        )
    import openai  # lazy

    client = openai.OpenAI(base_url=base, api_key=os.environ.get("ASSAY_LLM_API_KEY", "x"))
    msg = client.chat.completions.create(
        model=DEFAULT_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.choices[0].message.content or ""
