from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from .schema import Schema

class PermanentCore:
    def __init__(self, path: str = "./eks_core"):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._schemas: dict[str, Schema] = {}
        self._load()

    def lock(self, s: Schema) -> Schema:
        s.locked = True
        self._schemas[s.id] = s
        (self.path / f"{s.id}.json").write_text(json.dumps({
            "domain": s.domain, "version": s.version, "name": s.name,
            "questions": s.questions, "locked": True,
            "parent_version": s.parent_version,
            "issue_that_triggered": s.issue_that_triggered,
        }, indent=2))
        return s

    def get_current(self, domain: str) -> Schema | None:
        c = [s for s in self._schemas.values() if s.domain == domain]
        return max(c, key=lambda s: s.version) if c else None

    def history(self, domain: str) -> None:
        for s in sorted([s for s in self._schemas.values() if s.domain == domain], key=lambda x: x.version):
            t = f" ← [{s.issue_that_triggered}]" if s.issue_that_triggered else " (seed)"
            print(f"    {s.id:25s} {s.name}{t}")

    def _load(self):
        for f in self.path.glob("*.json"):
            try:
                d = json.loads(f.read_text())
                s = Schema(domain=d["domain"], version=d["version"], name=d["name"],
                           questions=d["questions"], locked=d.get("locked", True),
                           parent_version=d.get("parent_version"),
                           issue_that_triggered=d.get("issue_that_triggered"))
                self._schemas[s.id] = s
            except Exception as e:
                print(f"⚠ load {f.name}: {e}")
