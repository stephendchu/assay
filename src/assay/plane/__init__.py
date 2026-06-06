"""assay.plane — a deterministic, checkpointed, audited run loop.

Steps execute over a shared JSON state; gates and human approvals pause a run
and it resumes from checkpoint with no recomputation. Every transition is
written to a tamper-evident audit log. This is the 'run it like an SRE' layer
around the eval core.
"""
from assay.plane.audit import AuditLog
from assay.plane.core import (
    Run,
    RunContext,
    RunResult,
    Status,
    Step,
    StepResult,
    record_approval,
    run_id_for,
)

__all__ = [
    "AuditLog",
    "Run",
    "RunContext",
    "RunResult",
    "Status",
    "Step",
    "StepResult",
    "record_approval",
    "run_id_for",
]
