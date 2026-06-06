# assay

**Audit-first evaluation primitives for AI in high-consequence, regulated domains.**

> I build evaluation systems that define *correctness* for agentic and LLM-based
> software — grounded, anti-fabrication, and auditable — in environments where a
> wrong answer has consequences.

`assay` is the reusable eval **core** behind two domain projects, so each imports
the same primitives instead of re-implementing grounding and anti-fabrication:

- **[filing-event-eval](https://github.com/stephendchu/filing-event-eval)** — grounded event extraction from SEC filings (measure / trust).
- **[agentic-test-eval](https://github.com/stephendchu/agentic-test-eval)** — does repo-aware tooling help an agent write better tests? (validate).
- **SOX change-management control testing** — *next*: evidence-sufficiency as a grounding problem (govern).

## The stance
An eval in a high-consequence domain isn't a leaderboard score — it's a
**decision you can defend.** So `assay` is built around three ideas:

1. **Grounding over judgment** — prefer cheap, verifiable checks (does the cited
   span actually exist in the source?) to fuzzy LLM-judge scores.
2. **Anti-fabrication by default** — a claim you can't trace doesn't ship.
3. **Auditability** — every decision emits a provenance record: what was checked,
   what failed, and why.

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python examples/quickstart.py
pytest -q
```

## What's here (v0.0.1)
- `grounding.is_grounded` — verbatim, normalized citation verification.
- `gate.evaluate` — turns grounded/ungrounded claims into an **APPROVE / REVIEW /
  BLOCK** decision with an audit record.
- `graders` — a uniform `Grader` interface (rule + model + heuristic) so checks
  compose in experiments and gates.

## Roadmap
- `faithfulness` — entailment scoring (does the evidence support the conclusion?).
- `experiment` — baseline-vs-treatment runner + bootstrap CIs (honest nulls).
- `taxonomy` — failure classification (hallucination, missing-edge, brittle…).
- `goldset` — AI-draft → human-verify recall tooling.
- `drift` — quality drift across model versions / time.
- `tracing` — Phoenix / OpenTelemetry hooks.

*Public-data / synthetic only. No proprietary content.*
