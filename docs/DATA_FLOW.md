# Data flow & trust boundaries

How a request moves through the `assay` control plane, and where the control
points / trust boundaries are. (Reference workflow: change-approval.)

## Flow
```
input: synthetic change record + evidence
   │
   ▼  ingest .............. validate scope, load into run state
   ▼  map_controls ........ agent maps change → controls, with cited assertions
   ▼  GATE (grounding) .... anti-fabrication: every assertion must be citeable
   │        └─ BLOCK → run halts, audit-logged, nothing ships
   ▼  human_approval ...... maker-checker: independent reviewer signs off (SoD)
   │        └─ pause AWAITING_APPROVAL → resume from checkpoint on sign-off
   ▼  emit ................ workpaper + team-handoff report + ops report
   ▼
runs/<run_id>/  →  artifacts/  +  audit.jsonl (tamper-evident)
```

## Trust boundaries (where a control sits)
| Boundary | Control |
|---|---|
| AI output → decision | the **grounding gate** — ungrounded assertions never pass |
| automated → ship | **maker-checker** approval, independent of the author |
| run record → evidence | **hash-chained audit log** (`verify()`) + content-hashed artifacts |

## State & idempotency
- Each run is keyed by `run_id = hash(workflow, payload)` → same input, same run
  directory; replayable.
- State is checkpointed after every step; a paused or blocked run resumes with **no
  recomputation**.

## Data classification
- **Inputs:** synthetic change records + evidence — public/synthetic only.
- **No PII, no employer data.** Anything an LLM step may cite is restricted to the
  run's own evidence (the gate enforces this).
