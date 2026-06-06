"""Append-only, hash-chained audit log — tamper-evident provenance.

Every run writes one `audit.jsonl`. Each record carries the hash of the previous
record, so any after-the-fact edit breaks the chain and `verify()` catches it.
In a regulated setting that property is the point: the log *is* the evidence.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path


def _now() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat()


def _digest(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()


class AuditLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists():
            return "genesis"
        last = ""
        for line in self.path.read_text().splitlines():
            if line.strip():
                last = line
        return json.loads(last)["hash"] if last else "genesis"

    def append(self, event: str, **fields) -> dict:
        rec = {"ts": _now(), "event": event, "prev": self._last_hash(), **fields}
        rec["hash"] = _digest({k: v for k, v in rec.items() if k != "hash"})
        with self.path.open("a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        return rec

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]

    def verify(self) -> bool:
        """True iff the hash chain is intact (no record was edited or removed)."""
        prev = "genesis"
        for rec in self.records():
            if rec.get("prev") != prev:
                return False
            if rec.get("hash") != _digest({k: v for k, v in rec.items() if k != "hash"}):
                return False
            prev = rec["hash"]
        return True
