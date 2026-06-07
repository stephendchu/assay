# Observability & the operations report  *(design — lands with tracing)*

## Principle: instrument once, export anywhere
Tracing is built on the **open standard — OpenTelemetry / OpenInference — not a
single vendor.** `assay` emits standard spans; the backend is a **swappable
exporter.** No lock-in, and the same instrumentation lands in whichever tool a
team already runs.

| Backend | Role | Why |
|---|---|---|
| **Arize Phoenix** | default | open-source, runs locally, OpenInference-native — zero setup |
| **W&B Weave** | supported export | instrument once, view in Weave too |
| **Self-hosted** (Phoenix / Langfuse) | regulated / on-prem | data residency — traces never leave your environment |
| Others (Galileo, Braintrust, raw OTLP) | swap the exporter | standard OTLP out |

## Tracing
- Every step, gate decision, approval, and artifact write emits a **span**,
  mirroring the audit log.
- LLM judgment steps emit one span per model call (prompt, tokens, latency, cost).
- Spans carry the `run_id`, so a trace and its tamper-evident `audit.jsonl` line up.

## SLIs
- run outcome (completed / blocked / awaiting / failed)
- per-step + end-to-end latency
- gate block-rate; exception rate
- maker-checker wait time
- LLM cost / latency / token usage

## Operations report — clean vs. issues
A rollup across runs for the operations team:
- **Clean:** completed · gate APPROVE · no exceptions.
- **Issues:** BLOCKed (fabrication) · exceptions noted · FAILED · SLA-breached.

Each issue links to its run directory + audit log for triage, so the report is a
**queue**, not just a dashboard. Feeds [ESCALATION.md](ESCALATION.md).

*Data residency: with a self-hosted backend, no trace data leaves the deployment —
the same property the audit log guarantees for evidence.*
