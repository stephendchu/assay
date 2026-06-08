# assay

> **🛡 Govern (capstone)** · part 3 of a 3-part series on measuring & governing AI in regulated domains —
> [🔎 Validate](https://github.com/stephendchu/agentic-test-eval) · [📊 Measure](https://github.com/stephendchu/filing-event-eval) · **Govern (here)**

**Audit-first evaluation *and a governance control plane* for AI in high-consequence, regulated domains.**

> I build evaluation systems that define *correctness* for agentic and LLM-based
> software — grounded, anti-fabrication, and auditable — and run them like an
> SRE: deterministic, checkpointed, gated, human-approved, and provable.

Two layers, one repo:
- **Eval core** — grounding, anti-fabrication gating, composable graders.
- **Control plane** (`assay.plane`) — a deterministic, checkpointed run loop with
  eval **gates**, **maker-checker** human approval, durable **artifacts**, and a
  **tamper-evident audit log**.

Demonstrated across domains (the proof it generalizes):
- **[filing-event-eval](https://github.com/stephendchu/filing-event-eval)** — grounded event extraction from SEC filings (measure / trust).
- **[agentic-test-eval](https://github.com/stephendchu/agentic-test-eval)** — does repo-aware tooling help an agent write better tests? (validate).
- **`assay.apps.change_approval`** — SOX **ITGC change-management** control testing (govern), included here.

## The stance
An eval in a high-consequence domain isn't a leaderboard score — it's a
**decision you can defend.** So `assay` is built around:
1. **Grounding over judgment** — verifiable checks over fuzzy LLM-judge scores.
2. **Anti-fabrication by default** — a claim you can't trace doesn't ship.
3. **Auditability** — every decision emits tamper-evident provenance.
4. **Deterministic, resumable process** — gates and human sign-offs pause a run;
   it resumes from checkpoint with no recomputation.

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python examples/quickstart.py              # the anti-fabrication gate
python examples/change_approval_demo.py    # the full governed workflow
```

## The change-approval workflow (reference app)
A synthetic change record flows through the control plane:

`ingest → map to ITGC controls (cited) → anti-fabrication GATE → maker-checker approval → auditable workpaper`

- A change citing an **approval that isn't in the evidence** → the gate **BLOCKS** it.
- A clean change → **pauses for an independent reviewer** (segregation of duties),
  then resumes and issues a **workpaper** artifact.
- A **self-approved** change → grounded, but the workpaper records the **SoD deficiency**.

*Public / synthetic data only — generic COSO/ITGC language + made-up tickets.
Never any employer control, ticket, or audit data.*

## Proofs (show, don't tell)
Each guarantee is backed by a **test** (`pytest -q`) *and* an **artifact you can open**
in [`examples/sample_run/`](examples/sample_run/) — not just a claim in prose:

| Guarantee | Proof |
|---|---|
| **Reproducible AI control** — temperature 0, pinned model, full prompt + raw output + model id logged | test `test_llm_mapping_is_logged_for_reproducibility` · artifact [`sample_run/clean/artifacts/llm_mapping.json`](examples/sample_run/clean/artifacts/llm_mapping.json) |
| **Anti-fabrication** — a fabricated citation is blocked; nothing ships | test `test_llm_fabricated_citation_is_blocked` · artifact [`sample_run/blocked/audit.jsonl`](examples/sample_run/blocked/audit.jsonl) (verdict **BLOCK**) |
| **Tamper-evident audit log** — edit any record and `verify()` fails | test `test_audit_tamper_is_detected` |
| **Idempotent / resumable** — a paused/blocked run resumes with no recomputation | test `test_block_halts_and_resume_is_idempotent` |
| **Maker-checker (SoD)** — approver must differ from author | test `test_clean_change_pauses_then_completes` |
| **Faithfulness by entailment** (not brittle substring) | test `test_faithfulness.py` |
| **Measured eval** — gold set, control-F1 + bootstrap CIs, an *honest* baseline finding | [docs/EVAL.md](docs/EVAL.md) · test `test_deterministic_baseline_runs_and_scores` |

*Offline samples use an injected judge (no key) so they're reproducible; a live run logs the real model id.*

## Layout
```
src/assay/
  grounding.py gate.py graders.py      # eval core
  plane/ audit.py core.py              # control plane (deterministic, audited)
  apps/change_approval/                # reference workflow (SOX ITGC change mgmt)
```

## Governance docs
Running AI in a regulated environment is a *controlled process*, documented like any
financially-relevant system — see **[docs/](docs/)**: data flow, stakeholders / RACI,
the control register, auditable artifacts, validation (golden dataset), observability,
runbook & escalation.

## Roadmap
**Full plan & the decisions behind it: [ROADMAP.md](ROADMAP.md).**

- `faithfulness` — entailment scoring (does the evidence support the conclusion?).
- `experiment` — baseline-vs-treatment runner + bootstrap CIs (honest nulls).
- LLM control-mapper behind the same step interface (today's mapper is deterministic).
- More reference apps on the same plane: incident-runbook, financial-close.
- `tracing` — Phoenix / OpenTelemetry hooks.

*Public-data / synthetic only. No proprietary content.*
