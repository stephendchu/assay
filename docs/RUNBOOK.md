# SRE runbook & SLAs  *(design — matures with reference app #2: incident runbook)*

## Operating the pipeline
- **Start a run:** `Run(...).execute(payload)`.
- **Resume:** re-`execute()` the same payload — idempotent; resumes from checkpoint.
- **Approve (maker-checker):** `record_approval(rundir, key, approver)`, then re-execute.
- **Verify integrity:** `AuditLog(rundir / "audit.jsonl").verify()`.

## SLAs (targets — **business hours**, tiered by change type)
Three separate clocks — don't collapse them into one "human SLA":

| Clock | Standard in-scope change | Emergency | Breach |
|---|---|---|---|
| **Independent operator review** (the gating judge) | 4 business hrs (½ day) | 1 hr | escalate to control owner |
| **Maker-checker approval** | 1 business day | 1 hr + retroactive | escalate to process owner |
| **3rd-party observation — exceptions / blocks** | 24 hrs (next business day) | 4 hrs | SEV-2/3 |
| **3rd-party observation — clean population** | periodic (e.g. monthly sample) | — | completeness review |

The clock starts at handoff. **A breached SLA is itself an exception** (a finding), not
just a late ticket — it is logged and escalated, never silently cleared. The 3rd party does
*not* observe every clean run in real time: exceptions fast, completeness over a period
(this is the continuous-controls-monitoring model).

## Conditions & response
| Condition | Meaning | Response |
|---|---|---|
| `BLOCKED` | gate caught an ungrounded assertion | review evidence; **do not** override the gate — fix the input |
| `AWAITING_APPROVAL` | needs independent sign-off | route to reviewer; SLA clock starts |
| `FAILED` | a step errored (captured in the audit log) | inspect the audit event; re-execute (idempotent) |
| `verify()` is false | audit log was tampered | treat as a control incident → [ESCALATION.md](ESCALATION.md) |

## Retention & data lifecycle
SLAs govern **timeliness of review, not deletion.** Run evidence — the hash-chained audit
log, workpaper, handoff report, and the logged model prompt/output — is **retained per the
records-retention policy** (SOX-relevant evidence is typically kept ~7 years), so any control
test can be re-performed long after the run.

- A 24-hour **review** SLA does **not** clear data at 24 hours — the evidence persists.
- Retention is its own control; early deletion is itself a control failure.
- ▶ Exact retention period + storage (ideally **WORM / write-once**) are owner-assigned.

*Targets marked ▶ are owner-assigned.*
