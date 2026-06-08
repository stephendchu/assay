"""Offline-runnable eval harness: score a control mapper against the gold set.

Metrics (per docs/VALIDATION.md): control-mapping precision/recall/F1, citation
grounding rate, deficiency-call accuracy, and gate efficacy — aggregated with
bootstrap CIs. Runs on the deterministic baseline (no key) OR the LLM mapper
(live, or an injected judge offline), so the same harness yields an honest
baseline-vs-model comparison.
"""
from __future__ import annotations

import random
import statistics
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from assay.grounding import is_grounded


def precision_recall(predicted, expected) -> tuple[float, float]:
    predicted, expected = set(predicted), set(expected)
    tp = len(predicted & expected)
    precision = tp / len(predicted) if predicted else (1.0 if not expected else 0.0)
    recall = tp / len(expected) if expected else 1.0
    return precision, recall


def f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r) if (p + r) else 0.0


def bootstrap_ci(values, *, n: int = 2000, alpha: float = 0.05, seed: int = 0):
    """(point estimate, lower, upper) — percentile bootstrap of the mean."""
    if not values:
        return (0.0, 0.0, 0.0)
    rng = random.Random(seed)
    k = len(values)
    means = sorted(statistics.fmean(rng.choices(values, k=k)) for _ in range(n))
    return (statistics.fmean(values), means[int(alpha / 2 * n)], means[int((1 - alpha / 2) * n)])


@dataclass
class Report:
    n: int
    f1: tuple
    grounding_rate: tuple
    deficiency_accuracy: float
    gate_accuracy: float
    rows: list = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"n={self.n}  control-F1={self.f1[0]:.2f} [{self.f1[1]:.2f},{self.f1[2]:.2f}]  "
            f"grounding={self.grounding_rate[0]:.2f}  "
            f"deficiency-acc={self.deficiency_accuracy:.2f}  gate-acc={self.gate_accuracy:.2f}"
        )


def evaluate(cases, *, use_llm: bool = False, judge=None) -> Report:
    from assay.apps.change_approval.app import build

    f1s, grates, defs, gates, rows = [], [], [], [], []
    for case in cases:
        run = build(use_llm=use_llm, judge=judge)
        run.root = Path(tempfile.mkdtemp()) / "runs"
        r = run.execute(case["change"])
        claims = r.state.get("claims", [])
        mapped = {c["control"] for c in claims}
        ev = " ".join(str(v) for v in case["change"].get("evidence", {}).values())
        grounded = sum(1 for c in claims if is_grounded(c.get("citation", ""), ev))
        grate = grounded / len(claims) if claims else 1.0
        p, rec = precision_recall(mapped, case["controls"])
        case_f1 = f1(p, rec)
        found = {fd["control"] for fd in r.state.get("findings", [])}
        def_ok = found == set(case["deficiencies"])
        verdict = r.state.get("gate", {}).get("verdict", "")
        gate_ok = (verdict == "block") == bool(case["expect_block"])

        f1s.append(case_f1)
        grates.append(grate)
        defs.append(def_ok)
        gates.append(gate_ok)
        rows.append({"id": case["change"]["id"], "f1": round(case_f1, 2),
                     "grounding": round(grate, 2), "deficiency_ok": def_ok,
                     "gate": verdict or r.status.value, "gate_ok": gate_ok})

    mean = lambda xs: statistics.fmean(xs) if xs else 0.0
    return Report(
        n=len(cases),
        f1=bootstrap_ci(f1s),
        grounding_rate=bootstrap_ci(grates),
        deficiency_accuracy=mean([1.0 if d else 0.0 for d in defs]),
        gate_accuracy=mean([1.0 if g else 0.0 for g in gates]),
        rows=rows,
    )
