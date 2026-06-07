# Governance documentation

Running an AI process in a regulated environment isn't just code — it's a
**controlled process** that must be documented the way any financially-relevant
system is. These docs are that control documentation for `assay`.

| Doc | Covers |
|---|---|
| [DATA_FLOW.md](DATA_FLOW.md) | How data moves through the control plane; trust boundaries |
| [STAKEHOLDERS.md](STAKEHOLDERS.md) | Stakeholders, process owners, RACI |
| [CONTROLS.md](CONTROLS.md) | Control register + the control-check **format** (objective, test, evidence, deficiency criteria) |
| [ARTIFACTS.md](ARTIFACTS.md) | The auditable artifacts each run emits (workpaper, team report, ops report, audit log) |
| [VALIDATION.md](VALIDATION.md) | What the validation team does — golden dataset, eval metrics, acceptance gates |
| [OBSERVABILITY.md](OBSERVABILITY.md) | Tracing + the operations report (clean vs. issues) · *design, lands with tracing* |
| [RUNBOOK.md](RUNBOOK.md) | SRE runbook + SLAs · *design, matures with reference app #2* |
| [ESCALATION.md](ESCALATION.md) | Escalation playbook (severity, paging, SLA breach) · *design, matures with reference app #2* |

Spots marked **▶** are owner-assigned per deployment (thresholds, SLAs, names) —
they're configuration, not gaps.

*Public / synthetic only — illustrative control documentation, never employer data.*
