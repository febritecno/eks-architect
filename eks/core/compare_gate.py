from __future__ import annotations
from dataclasses import dataclass
from .schema import Schema

@dataclass
class CompareResult:
    should_promote: bool
    delta: float
    reason: str

class CompareGate:
    def __init__(self, threshold: float = 0.05):
        self.threshold = threshold

    def evaluate(self, candidate: Schema, current: Schema) -> CompareResult:
        curr = self._score(current)
        cand = self._score(candidate)
        delta = cand - curr
        promote = delta > self.threshold
        return CompareResult(
            should_promote=promote, delta=delta,
            reason=f"+{delta*100:.1f}% → {'PROMOTE ✓' if promote else 'REJECT ✗'}"
        )

    def _score(self, s: Schema) -> float:
        types = {v.get("type") for v in s.questions.values()}
        return min(0.99, 0.60 + len(s.questions) * 0.04 + len(types) * 0.02)
