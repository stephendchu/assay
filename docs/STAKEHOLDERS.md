# Stakeholders, process owners & RACI

## Roles
| Role | Responsibility |
|---|---|
| **Change author (maker)** | submits the change + evidence |
| **Independent reviewer (checker)** | approves; must be ≠ author (segregation of duties) |
| **Control owner** | owns control definitions & deficiency criteria ([CONTROLS.md](CONTROLS.md)) |
| **Platform owner (assay)** | owns the control plane, gates, audit log |
| **Validation team** | owns the golden dataset & eval metrics ([VALIDATION.md](VALIDATION.md)) |
| **Operations / SRE** | runs the pipeline; consumes the ops report; handles escalation |
| **Audit / risk (consuming team)** | relies on the team-handoff report as evidence |

## RACI
| Activity | Author | Reviewer | Control owner | Platform | Validation | Ops | Audit |
|---|---|---|---|---|---|---|---|
| Submit change | **R/A** | I | – | – | – | – | – |
| Control mapping (AI) | C | – | A | **R** | – | – | I |
| Gate decision | – | – | C | **R/A** | C | I | I |
| Human sign-off | I | **R/A** | C | – | – | – | I |
| Issue reports | – | I | C | **R** | – | C | **A** |
| Validate the AI (golden set) | – | – | C | C | **R/A** | – | I |
| Operate / escalate | – | – | – | C | – | **R/A** | I |

*R responsible · A accountable · C consulted · I informed.*

▶ Roles are illustrative for the reference workflow; real names/owners are assigned
per deployment.
