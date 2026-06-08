# Sample run artifacts — proofs you can read

Generated **offline** (an injected judge, no API key) so anyone can reproduce them.
A live run logs the real model id instead of `injected-judge`; everything else is identical.

## `clean/` — a change that passes
- **`artifacts/llm_mapping.json` — the reproducibility proof.** It records the
  **model id**, **`temperature: 0`**, the **exact prompt**, and the **raw model output** —
  so the control test can be *re-performed* and tied out by an auditor.
- `artifacts/workpaper.json` — the auditable test result: controls tested, gate decision,
  approval, conclusion.
- `audit.jsonl` — the tamper-evident, hash-chained log of every step (`AuditLog.verify()`).

## `blocked/` — the model fabricated a citation
The model cited an approval — *"Approved by the CEO on January 1st."* — that is **not in
the evidence**. `audit.jsonl` shows the gate's verdict:

> `step_result … "status": "blocked" … "reason": "anti-fabrication gate: 1 unciteable assertion(s)"`

Nothing shipped. That's the hallucination caught and refused — with the prompt and raw
output preserved in `artifacts/llm_mapping.json` for review.
