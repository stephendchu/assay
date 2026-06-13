# assay — roadmap & plan

The third part of a three-part arc — **🔎 Validate** ([agentic-test-eval](https://github.com/stephendchu/agentic-test-eval))
→ **📊 Measure** ([filing-event-eval](https://github.com/stephendchu/filing-event-eval))
→ **🛡 Govern** (assay). assay is the governance layer: an audit-first evaluation +
control plane that makes AI behavior **provable and auditable** in regulated
environments.

## Status

**Done**
- [x] **Eval core** — grounding, anti-fabrication gate, composable graders.
- [x] **Control plane** — deterministic checkpointed run loop, tamper-evident
  audit log, content-hashed artifacts, maker-checker (SoD) human approval.
- [x] **LLM judgment step** — Claude does control mapping + evidence sufficiency, with abstention.
- [x] **Reference domains** — SOX ITGC change-management *and* PAD trade surveillance on one engine (synthetic data).
- [x] **Observability** — OpenTelemetry / OpenInference spans, Phoenix UI.

**Next**
- [ ] **Eval layer** — control-F1 + bootstrap CIs on a larger, less-synthetic gold set (the *measured* result).
- [ ] **Team-handoff & ops reports** as first-class, audit-hash-carrying artifacts.

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
   *measured* result, not just orchestration.

## Build order
Each step ships code **and** its governance doc together — the doc isn't an
afterthought, it's part of the deliverable. (✅ = doc already drafted in
[`docs/`](docs/); 🔧 = doc finalized when this step lands.)

0. **Governance spine** — DATA_FLOW, STAKEHOLDERS/RACI, CONTROLS, ARTIFACTS,
   VALIDATION drafted up front. ✅ *(done)*
1. **LLM judgment step** (control mapping + evidence sufficiency, behind the existing
   deterministic step interface). → exercises **CONTROLS.md** against real model
   behavior; needs `ANTHROPIC_API_KEY`.
2. **Team-handoff + ops reports** as first-class artifacts. 🔧 finalizes
   **ARTIFACTS.md** (report schemas + audit-hash).
3. **Observability** — OpenTelemetry / OpenInference (vendor-neutral; Phoenix default,
   W&B Weave export, self-host for on-prem) feeding the ops "clean vs. issues" report.
   🔧 finalizes **OBSERVABILITY.md** (spans → SLIs → ops queue).
4. **Eval layer + gold set** (revisit hand-verification). 🔧 finalizes
   **VALIDATION.md** (metrics + acceptance thresholds).
5. **Reference app #2 — incident runbook** (SLA + escalation). 🔧 finalizes
   **RUNBOOK.md** + **ESCALATION.md** (SLA targets, SEV tiers, on-call).

*Public / synthetic data only — never employer control, ticket, or audit data.*
