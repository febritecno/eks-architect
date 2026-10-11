"""
EKS Core — Decision Log
SQLite-based persistent log of every Laya decision.
Used by Reflect Engine and LLM Architect for context.
"""
from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class DecisionRecord:
    id: int | None
    domain: str
    schema_version: int
    input_text: str
    answers: dict
    avg_confidence: float
    issue_triggered: str | None
    timestamp: datetime


class DecisionLog:
    """
    Persistent SQLite log of every decision made by Laya.
    Append-only — records are never deleted, only queried.
    """

    def __init__(self, db_path: str = "./eks_core/decisions.db"):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain          TEXT NOT NULL,
                    schema_version  INTEGER NOT NULL,
                    input_text      TEXT NOT NULL,
                    answers_json    TEXT NOT NULL,
                    avg_confidence  REAL NOT NULL,
                    issue_triggered TEXT,
                    timestamp       TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_domain ON decisions(domain)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ts    ON decisions(timestamp)")

    def record(
        self,
        domain: str,
        schema_version: int,
        input_text: str,
        answers: dict,
        issue_triggered: str | None = None,
    ) -> int:
        """Append a decision to the log. Returns new row id."""
        confs = [
            float(v.get("confidence", 0))
            for v in answers.values()
            if isinstance(v, dict)
        ]
        avg_conf = sum(confs) / len(confs) if confs else 0.0

        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO decisions
                   (domain, schema_version, input_text, answers_json,
                    avg_confidence, issue_triggered, timestamp)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    domain,
                    schema_version,
                    input_text,
                    json.dumps(answers),
                    round(avg_conf, 4),
                    issue_triggered,
                    datetime.now().isoformat(),
                ),
            )
            return cur.lastrowid

    def recent(self, domain: str, n: int = 20) -> list[DecisionRecord]:
        """Return last N decisions for a domain."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM decisions
                   WHERE domain = ?
                   ORDER BY id DESC LIMIT ?""",
                (domain, n),
            ).fetchall()
        return [self._row_to_record(r) for r in reversed(rows)]

    def stats(self, domain: str) -> dict:
        """Aggregate stats for a domain."""
        with self._conn() as conn:
            row = conn.execute(
                """SELECT
                     COUNT(*)                          AS total,
                     ROUND(AVG(avg_confidence), 3)     AS avg_conf,
                     ROUND(MIN(avg_confidence), 3)     AS min_conf,
                     COUNT(issue_triggered)            AS total_issues,
                     MAX(schema_version)               AS max_schema_v
                   FROM decisions WHERE domain = ?""",
                (domain,),
            ).fetchone()
            issues = conn.execute(
                """SELECT issue_triggered, COUNT(*) as cnt
                   FROM decisions
                   WHERE domain = ? AND issue_triggered IS NOT NULL
                   GROUP BY issue_triggered
                   ORDER BY cnt DESC LIMIT 5""",
                (domain,),
            ).fetchall()
        return {
            "total_decisions": row["total"],
            "avg_confidence":  row["avg_conf"],
            "min_confidence":  row["min_conf"],
            "total_issues":    row["total_issues"],
            "max_schema_v":    row["max_schema_v"],
            "top_issues":      [{"trigger": r["issue_triggered"], "count": r["cnt"]} for r in issues],
        }

    def context_for_llm(self, domain: str, n: int = 10) -> str:
        """
        Format recent decisions as context string for LLM prompts.
        Used by LLMArchitect when evolving schema.
        """
        records = self.recent(domain, n)
        if not records:
            return "No decision history available."

        lines = [f"Last {len(records)} decisions for '{domain}':"]
        for r in records:
            top_answer = next(
                (f"{k}={v.get('answer')}({v.get('confidence', 0):.2f})"
                 for k, v in r.answers.items()),
                "?"
            )
            issue = f" ⚠ {r.issue_triggered}" if r.issue_triggered else ""
            lines.append(
                f"  [{r.timestamp.strftime('%H:%M:%S')}] "
                f"conf={r.avg_confidence:.2f} | {top_answer}{issue}"
            )

        stats = self.stats(domain)
        lines.append(
            f"\nStats: {stats['total_decisions']} total | "
            f"avg_conf={stats['avg_confidence']} | "
            f"issues={stats['total_issues']}"
        )
        return "\n".join(lines)

    def all_for_api(self, domain: str, limit: int = 50) -> list[dict]:
        """Return decisions as plain dicts for API response."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM decisions
                   WHERE domain = ?
                   ORDER BY id DESC LIMIT ?""",
                (domain, limit),
            ).fetchall()
        return [
            {
                "id":             r["id"],
                "schema_version": r["schema_version"],
                "input":          r["input_text"],
                "answers":        json.loads(r["answers_json"]),
                "avg_confidence": r["avg_confidence"],
                "issue":          r["issue_triggered"],
                "timestamp":      r["timestamp"],
            }
            for r in rows
        ]

    def _row_to_record(self, row) -> DecisionRecord:
        return DecisionRecord(
            id=row["id"],
            domain=row["domain"],
            schema_version=row["schema_version"],
            input_text=row["input_text"],
            answers=json.loads(row["answers_json"]),
            avg_confidence=row["avg_confidence"],
            issue_triggered=row["issue_triggered"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )
