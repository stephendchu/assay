# Auditable artifacts

Every run produces durable, content-hashed artifacts under `runs/<run_id>/`, each
referenced in the tamper-evident audit log.

| Artifact | Audience | Purpose |
|---|---|---|
| `audit.jsonl` | auditor | hash-chained log of every step / gate / approval — `verify()` detects tampering |
| `artifacts/workpaper.json` | control owner | the test workpaper: controls tested, gate decision, exceptions, conclusion |
| `artifacts/approval_request.json` | reviewer | the maker-checker ask, written when a run pauses for sign-off |
| **team-handoff report** *(planned)* | audit / risk (consuming team) | clean, relyable summary carrying the audit-log hash so the team can **verify** it |
| **ops report** *(planned)* | operations | clean-vs-issues rollup across runs, for triage |

## Properties
- **Content-hashed** — every artifact records a `sha256` so changes are detectable.
- **Provenance** — the audit log hash-chains every event; editing any record fails `verify()`.
- **Self-contained** — a run directory is the complete, replayable evidence package.

## Example — `workpaper.json`
```json
{
  "change_id": "CHG-1042",
  "controls_tested": ["ITGC-CM-01", "ITGC-CM-03"],
  "gate": { "verdict": "approve", "grounded": 2, "ungrounded": 0 },
  "exceptions": [],
  "approval": { "approver": "a.singh", "decision": "approved" },
  "conclusion": "no exceptions"
}
```
