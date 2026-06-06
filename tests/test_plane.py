import json

from assay.plane.audit import AuditLog
from assay.plane.core import Run, RunContext, Status, StepResult, run_id_for


def ok_step(msg):
    def step(ctx: RunContext) -> StepResult:
        ctx.state.setdefault("trace", []).append(msg)
        return StepResult(Status.OK, msg)
    return step


def test_run_id_is_deterministic():
    assert run_id_for("x", {"a": 1}) == run_id_for("x", {"a": 1})
    assert run_id_for("x", {"a": 1}) != run_id_for("x", {"a": 2})


def test_run_completes_and_audit_verifies(tmp_path):
    run = Run("t", [("a", ok_step("a")), ("b", ok_step("b"))], root=tmp_path)
    res = run.execute({"k": 1})
    assert res.status is Status.COMPLETED
    assert res.state["trace"] == ["a", "b"]
    assert AuditLog(res.rundir / "audit.jsonl").verify()


def test_block_halts_and_resume_is_idempotent(tmp_path):
    calls = {"a": 0}

    def a(ctx):
        calls["a"] += 1
        return StepResult(Status.OK)

    flip = {"block": True}

    def b(ctx):
        return StepResult(Status.BLOCKED, "nope") if flip["block"] else StepResult(Status.OK)

    run = Run("t", [("a", a), ("b", b)], root=tmp_path)
    res = run.execute({"k": 1})
    assert res.status is Status.BLOCKED
    assert calls["a"] == 1

    flip["block"] = False           # fix the condition and resume
    res = run.execute({"k": 1})
    assert res.status is Status.COMPLETED
    assert calls["a"] == 1          # 'a' was checkpointed, never recomputed


def test_audit_tamper_is_detected(tmp_path):
    run = Run("t", [("a", ok_step("a"))], root=tmp_path)
    res = run.execute({"k": 1})
    log = res.rundir / "audit.jsonl"
    lines = log.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["event"] = "tampered"       # edit a record without fixing the hash chain
    lines[0] = json.dumps(rec)
    log.write_text("\n".join(lines) + "\n")
    assert AuditLog(log).verify() is False
