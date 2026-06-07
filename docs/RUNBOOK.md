# SRE runbook & SLAs  *(design — matures with reference app #2: incident runbook)*

## Operating the pipeline
- **Start a run:** `Run(...).execute(payload)`.
- **Resume:** re-`execute()` the same payload — idempotent; resumes from checkpoint.
- **Approve (maker-checker):** `record_approval(rundir, key, approver)`, then re-execute.
- **Verify integrity:** `AuditLog(rundir / "audit.jsonl").verify()`.

## SLAs (targets)
| Stage | Target |
|---|---|
| Run completion (no human step) | ▶ set per deployment |
| Maker-checker sign-off | ▶ e.g. within N business hours |
| Gate-block triage | ▶ within N hours |

## Conditions & response
| Condition | Meaning | Response |
|---|---|---|
| `BLOCKED` | gate caught an ungrounded assertion | review evidence; **do not** override the gate — fix the input |
| `AWAITING_APPROVAL` | needs independent sign-off | route to reviewer; SLA clock starts |
| `FAILED` | a step errored (captured in the audit log) | inspect the audit event; re-execute (idempotent) |
| `verify()` is false | audit log was tampered | treat as a control incident → [ESCALATION.md](ESCALATION.md) |

*Targets marked ▶ are owner-assigned.*
