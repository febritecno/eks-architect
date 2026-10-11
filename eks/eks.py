from __future__ import annotations
from .core.permanent_core import PermanentCore
from .core.compare_gate import CompareGate
from .core.reflect_engine import ReflectEngine
from .core.decision_log import DecisionLog
from .llm.architect import LLMArchitect


class EKS:
    """
    Evolutionary Knowledge System.
    - Laya handles runtime decisions (fast, offline)
    - DecisionLog records every decision to SQLite
    - LLM called only on reflect events, with log context
    - New schemas must pass CompareGate before promotion
    """

    def __init__(
        self,
        domain: str,
        description: str,
        laya_model: str = "aac6fef/laya-mlx",
        llm_url: str = "http://localhost:8001/v1",
        storage: str = "./eks_core",
    ):
        self.domain = domain
        self.core    = PermanentCore(storage)
        self.gate    = CompareGate()
        self.reflect = ReflectEngine()
        self.log     = DecisionLog(f"{storage}/decisions.db")
        self.llm     = LLMArchitect(llm_url)

        try:
            import laya_mlx as laya
            self.agent = laya.load(laya_model)
            print("✅ Laya loaded")
        except Exception as e:
            self.agent = None
            print(f"⚠ Laya unavailable: {e}")

        if not self.core.get_current(domain):
            print("🧠 LLM seeding initial schema...")
            s = self.llm.seed(domain, description)
            self.core.lock(s)
            print(f"🔒 Seeded: {s}")

    def decide(self, inp: str) -> dict:
        """Runtime decision. Logs every call. Triggers evolve on issues."""
        schema = self.core.get_current(self.domain)
        if not schema or not self.agent:
            return {}

        result  = self.agent.predict(inp, schema.questions)
        answers = result.get("answers", {})

        # detect issue before logging (so issue is recorded on same row)
        issue = self.reflect.record(inp, answers)

        # log to SQLite
        self.log.record(
            domain=self.domain,
            schema_version=schema.version,
            input_text=inp,
            answers=answers,
            issue_triggered=issue.trigger if issue else None,
        )

        if issue:
            print(f"\n⚡ Issue: {issue.trigger}")
            self._evolve(issue.trigger)

        return answers

    def force_evolve(self, reason: str = "manual") -> None:
        self._evolve(self.reflect.force(reason).trigger)

    def status(self) -> None:
        s = self.core.get_current(self.domain)
        stats = self.log.stats(self.domain)
        print(f"\n{'─'*55}")
        print(f"EKS — {self.domain}")
        print(f"Schema  : {s}")
        print(f"Fields  : {s.question_names() if s else []}")
        print(f"Log     : {stats['total_decisions']} decisions | "
              f"avg_conf={stats['avg_confidence']} | "
              f"issues={stats['total_issues']}")
        print("History :")
        self.core.history(self.domain)
        print(f"{'─'*55}\n")

    def _evolve(self, trigger: str) -> None:
        current = self.core.get_current(self.domain)
        if not current:
            return

        # pass recent decision log as context to LLM
        log_context = self.log.context_for_llm(self.domain, n=15)

        print("🧠 LLM generating evolved schema (with log context)...")
        candidate = self.llm.evolve(current, trigger, log_context=log_context)

        result = self.gate.evaluate(candidate, current)
        print(f"⚖️  Compare Gate: {result.reason}")

        if result.should_promote:
            self.core.lock(candidate)
            print(f"✅ Promoted: {candidate}")
        else:
            print("✗ Rejected — delta too small")
