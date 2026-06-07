# Observability & the operations report  *(design — lands with tracing)*

## Tracing
- Every step, gate decision, approval, and artifact write emits a span
  (Phoenix / OpenTelemetry), mirroring the audit log.
- LLM judgment steps emit one span per model call (prompt, tokens, latency).

## SLIs
- run outcome (completed / blocked / awaiting / failed)
- per-step latency; end-to-end latency
- gate block-rate; exception rate
- maker-checker wait time
- LLM cost / latency / token usage

## Operations report — clean vs. issues
A rollup across runs for the operations team:
- **Clean:** completed · gate APPROVE · no exceptions.
- **Issues:** BLOCKed (fabrication) · exceptions noted · FAILED · SLA-breached.

Each issue links to its run directory + audit log for triage, so the report is a
*queue*, not just a dashboard. Feeds [ESCALATION.md](ESCALATION.md).
