# assay — roadmap & plan

The capstone of a three-part arc — **🔎 Validate** ([agentic-test-eval](https://github.com/stephendchu/agentic-test-eval))
→ **📊 Measure** ([filing-event-eval](https://github.com/stephendchu/filing-event-eval))
→ **🛡 Govern** (assay). assay is the governance layer: an audit-first evaluation +
control plane that makes AI behavior **provable and auditable** in regulated
environments.

## Status
- [x] **Eval core** — grounding, anti-fabrication gate, composable graders.
- [x] **Control plane** — deterministic checkpointed run loop, tamper-evident
  audit log, content-hashed artifacts, maker-checker (SoD) human approval.
- [x] **Reference app #1** — SOX ITGC change-management (synthetic data).

## Decided direction
1. **AI-first, then refine.** Put a real LLM (Claude) in the judgment steps (control
   mapping + evidence sufficiency) so there's genuine AI behavior to *evaluate*,
   then refine prompts/graders. *(needs `ANTHROPIC_API_KEY`)*
   - ⏰ **Reminder to revisit:** gold-set strategy — hand-verified vs.
     AI-drafted-then-reviewed (the recall-rigor decision).
2. **Auditable team-handoff report.** Beyond the internal workpaper, each run emits
   a **control report for a consuming team** (operations / audit / risk): a clean,
   relyable summary (scope, results, exceptions, period) carrying the audit-log
   hash so the receiving team can *verify* it. SOC-style handoff.
3. **Observability now, with an operations report.** Phoenix / OpenTelemetry traces
   across the run, rolled up into an **ops report — clean vs. issues** — so
   operations can triage which runs passed and which hit gates / exceptions /
   failures.
4. **Reference app #2 — incident runbook (SRE).** A runbook workflow on the same
   plane with **SLAs and escalation paths** (breach → escalate; human approval for
   risky steps) — proving the plane generalizes beyond audit.
5. **The eval layer.** Gold set + metrics: precision / recall of control mapping,
   faithfulness of the rationale, deficiency-call accuracy. This is what makes it a
   *measured* capstone, not just orchestration.

## Build order
1. LLM judgment step (behind the existing deterministic step interface).
2. Team-handoff report + ops (clean / issues) report as first-class artifacts.
3. Observability (Phoenix / OTel) feeding the ops report.
4. Eval layer + gold set (revisit hand-verification then).
5. Reference app #2 — incident runbook (SLA + escalation).

*Public / synthetic data only — never employer control, ticket, or audit data.*
