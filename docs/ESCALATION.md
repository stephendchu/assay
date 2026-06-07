# Escalation playbook  *(design — matures with reference app #2)*

## Severity
| Sev | Trigger | Notify | Timeline |
|---|---|---|---|
| **SEV-1** | audit log fails `verify()` (tamper) / gate bypass | platform owner + audit/risk | immediate |
| **SEV-2** | repeated gate BLOCKs / fabrication pattern | platform owner + control owner | same day |
| **SEV-3** | SLA breach (sign-off or triage overdue) | process owner + ops | next business day |
| **SEV-4** | single exception in a workpaper | control owner | normal queue |

## Flow
1. **Detect** — ops report, failed `verify()`, or SLA monitor.
2. **Classify** severity (table above).
3. **Notify** per table; open an incident referencing the `run_id` + audit log.
4. **Contain** — halt the workflow for SEV-1 / SEV-2.
5. **Resolve & record** — SEV-1 / SEV-2 get a written post-incident review.

## Principles
- The gate is **not** overridable by ops — a BLOCK is fixed at the source, never bypassed.
- Every escalation references immutable evidence (run directory + hash-chained log).
- ▶ Notification targets / on-call rotation are owner-assigned.
