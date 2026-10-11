from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Issue:
    trigger: str
    context: list[dict]
    timestamp: datetime = field(default_factory=datetime.now)

class ReflectEngine:
    WINDOW = 10
    REPEAT_THRESH = 0.80
    CONF_FLOOR = 0.52

    def __init__(self):
        self._buf: deque = deque(maxlen=self.WINDOW)

    def record(self, inp: str, answers: dict) -> Issue | None:
        first = next(iter(answers.values()), {})
        self._buf.append({
            "input": inp[:60],
            "answer": str(first.get("answer", "?")),
            "conf": float(first.get("confidence", 1.0)),
        })
        return self._check()

    def force(self, reason: str = "manual") -> Issue:
        return Issue(trigger=reason, context=list(self._buf))

    def _check(self) -> Issue | None:
        if len(self._buf) < self.WINDOW:
            return None
        recent = list(self._buf)
        answers = [r["answer"] for r in recent]
        top = max(set(answers), key=answers.count)
        ratio = answers.count(top) / len(answers)
        if ratio >= self.REPEAT_THRESH:
            return Issue(trigger=f"repeat '{top}' {ratio:.0%}", context=recent)
        avg_conf = sum(r["conf"] for r in recent) / len(recent)
        if avg_conf < self.CONF_FLOOR:
            return Issue(trigger=f"low_confidence {avg_conf:.2f}", context=recent)
        return None
