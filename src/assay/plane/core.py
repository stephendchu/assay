"""Deterministic, checkpointed run loop with gates, human approvals, artifacts.

A Run executes an ordered list of named Steps over a shared, JSON-serializable
state dict. After every step the state is checkpointed to disk, so a run that is
BLOCKED by a gate or paused for human approval resumes exactly where it stopped —
no recomputation, no drift. Every transition is written to the tamper-evident
AuditLog. The run id is a hash of (name, payload): identical input, identical
run directory — idempotent and replayable.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

from assay.plane.audit import AuditLog


class Status(str, Enum):
    OK = "ok"
    BLOCKED = "blocked"
    AWAITING_APPROVAL = "awaiting_approval"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class StepResult:
    status: Status
    reason: str = ""


@dataclass
class RunContext:
    state: dict
    rundir: Path
    audit: AuditLog

    def artifact(self, name: str, content: str) -> str:
        """Write a durable, content-hashed artifact into the run directory."""
        path = self.rundir / "artifacts" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        self.state.setdefault("artifacts", {})[name] = {"sha256_12": digest, "path": str(path)}
        self.audit.append("artifact_written", name=name, sha256_12=digest)
        return digest


# A Step reads/writes ctx.state and returns a StepResult.
Step = Callable[[RunContext], StepResult]


def run_id_for(name: str, payload: dict) -> str:
    blob = json.dumps({"name": name, "payload": payload}, sort_keys=True, default=str)
    return f"{name}-{hashlib.sha256(blob.encode()).hexdigest()[:12]}"


@dataclass
class RunResult:
    run_id: str
    status: Status
    rundir: Path
    state: dict


def record_approval(rundir, key: str, approver: str, decision: str = "approved") -> None:
    """Maker-checker sign-off: record an approval into the checkpoint, then
    re-run `execute(payload)` to resume from where it paused."""
    rundir = Path(rundir)
    state = json.loads((rundir / "state.json").read_text())
    state.setdefault("approvals", {})[key] = {"approver": approver, "decision": decision}
    (rundir / "state.json").write_text(json.dumps(state, indent=2, default=str))
    AuditLog(rundir / "audit.jsonl").append(
        "approval_recorded", key=key, approver=approver, decision=decision
    )


@dataclass
class Run:
    name: str
    steps: list[tuple[str, Step]]
    root: Path = field(default_factory=lambda: Path("runs"))

    def execute(self, payload: dict) -> RunResult:
        rid = run_id_for(self.name, payload)
        rundir = Path(self.root) / rid
        (rundir / "artifacts").mkdir(parents=True, exist_ok=True)
        audit = AuditLog(rundir / "audit.jsonl")
        state_path = rundir / "state.json"

        if state_path.exists():  # resume from checkpoint
            state = json.loads(state_path.read_text())
        else:
            state = {"payload": payload, "artifacts": {}, "approvals": {}, "_done": []}
            audit.append("run_started", run_id=rid, name=self.name)

        ctx = RunContext(state=state, rundir=rundir, audit=audit)

        def checkpoint() -> None:
            state_path.write_text(json.dumps(state, indent=2, default=str))

        for name, step in self.steps:
            if name in state["_done"]:
                continue  # completed in a prior attempt — never recomputed
            audit.append("step_started", step=name)
            try:
                result = step(ctx)
            except Exception as exc:  # failures are measured signals, never silent
                audit.append("step_failed", step=name, error=repr(exc))
                checkpoint()
                return RunResult(rid, Status.FAILED, rundir, state)

            audit.append("step_result", step=name, status=result.status.value, reason=result.reason)
            if result.status is Status.OK:
                state["_done"].append(name)
                checkpoint()
                continue
            checkpoint()  # BLOCKED / AWAITING_APPROVAL / FAILED — resumable
            return RunResult(rid, result.status, rundir, state)

        audit.append("run_completed", run_id=rid)
        checkpoint()
        return RunResult(rid, Status.COMPLETED, rundir, state)
