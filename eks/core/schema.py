from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class Schema:
    domain: str
    version: int
    name: str
    questions: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    locked: bool = False
    parent_version: int | None = None
    issue_that_triggered: str | None = None

    @property
    def id(self) -> str:
        return f"{self.domain}-v{self.version}"

    def question_names(self) -> list[str]:
        return list(self.questions.keys())

    def __repr__(self) -> str:
        s = "🔒" if self.locked else "📝"
        return f"Schema({self.id} | {self.name} | {len(self.questions)}q {s})"
