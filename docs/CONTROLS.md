# Control register & control-check format

In `assay`, **controls are the format** — every check is a control with a defined
objective, test, evidence requirement, and deficiency criteria. The AI *proposes*;
the control + gate *decide*.

## Control-check format
| Field | Meaning |
|---|---|
| **ID** | stable identifier (e.g. `ITGC-CM-02`) |
| **Objective** | the risk it mitigates |
| **Type** | ToD (test of design) / ToE (test of operating effectiveness) |
| **Test procedure** | how the system checks it |
| **Evidence required** | what must be present and **citeable** |
| **Frequency / population** | per-change, or sampled |
| **Owner** | accountable role |
| **Deficiency criteria** | what counts as an exception, and its severity |

## Register — reference: ITGC change management

### ITGC-CM-01 — Change authorization
- **Objective:** in-scope changes are authorized before deployment. **Type:** ToE.
- **Test:** an approval record exists and predates deployment; the assertion must be
  **grounded** in evidence.
- **Deficiency:** no / post-deployment approval → *deficiency*; **fabricated** approval
  → **gate BLOCK** (never accepted).

### ITGC-CM-02 — Segregation of duties
- **Objective:** the approver is independent of the developer. **Type:** ToE.
- **Test:** `approver ≠ author`.
- **Deficiency:** self-approval → *deficiency* (recorded in the workpaper).

### ITGC-CM-03 — Testing evidence
- **Objective:** changes are tested with documented results before promotion. **Type:** ToE.
- **Test:** a test sign-off is present and citeable.
- **Deficiency:** missing / ungrounded test evidence → *deficiency* or **BLOCK**.

## Anti-fabrication principle
Across all controls, a conclusion the AI cannot **ground in the evidence** is never
accepted — it BLOCKs at the gate. Controls measure the *evidence*, not the model's
confidence.

*Control language is generic public COSO / ITGC; never employer-specific controls.*
