from __future__ import annotations
import json, re
from openai import OpenAI
from ..core.schema import Schema

class LLMArchitect:
    def __init__(self, base_url: str = "http://localhost:8001/v1"):
        self.client = OpenAI(base_url=base_url, api_key="none")
        try:
            self.model = self.client.models.list().data[0].id
            print(f"🤖 LLM: {self.model}")
        except Exception:
            self.model = "local"

    def seed(self, domain: str, description: str) -> Schema:
        prompt = f"""Design a Laya typed-decision schema for: {domain}
Context: {description}

Return a JSON object with 3-4 questions. ALL questions MUST have an "instructions" field.
Use ONLY these formats:

choice:  {{"type": "choice", "instructions": "Which direction?", "criteria": ["forward", "left", "right", "stop"]}}
score:   {{"type": "score",  "instructions": "How urgent?",      "criteria": ["low", "medium", "high", "critical"]}}
noul:    {{"type": "noul",   "instructions": "Is it safe to move?"}}

Return ONLY valid JSON object, no markdown, no explanation.
Example for robot navigation:
{{
  "direction": {{"type": "choice", "instructions": "Which direction should the robot move?", "criteria": ["forward", "left", "right", "stop"]}},
  "obstacle":  {{"type": "noul",   "instructions": "Is there an obstacle blocking the path?"}},
  "speed":     {{"type": "score",  "instructions": "What speed level is appropriate?", "criteria": ["slow", "normal", "fast"]}}
}}"""
        q = self._call(prompt)
        return Schema(domain=domain, version=1, name=f"{domain} — Seed", questions=self._validate(q))

    def evolve(self, current: Schema, issue: str, log_context: str = "") -> Schema:
        context_section = f"\nDecision history:\n{log_context}\n" if log_context else ""
        prompt = f"""A Laya typed-decision schema for '{current.domain}' has this issue: {issue}
{context_section}
Current questions:
{json.dumps(current.questions, indent=2)}

Add 1-2 NEW questions to address the issue. ALL questions MUST have "instructions" field.
Keep all existing questions unchanged. Return COMPLETE JSON (existing + new).

Formats (instructions is REQUIRED for all):
choice: {{"type": "choice", "instructions": "Question?", "criteria": ["a","b","c"]}}
score:  {{"type": "score",  "instructions": "Question?", "criteria": ["low","high"]}}
noul:   {{"type": "noul",   "instructions": "Yes/no question?"}}

Return ONLY valid JSON, no markdown."""
        q = self._call(prompt)
        q = self._validate(q)
        new_keys = set(q) - set(current.questions)
        label = ", ".join(new_keys) if new_keys else "refined"
        return Schema(
            domain=current.domain, version=current.version + 1,
            name=f"v{current.version+1}: +{label}",
            questions=q, parent_version=current.version,
            issue_that_triggered=issue,
        )

    def _validate(self, questions: dict) -> dict:
        """Ensure all questions have required 'instructions' field."""
        fixed = {}
        for key, q in questions.items():
            if not isinstance(q, dict):
                continue
            if "instructions" not in q:
                # auto-generate instructions from key name
                q["instructions"] = f"What is the {key.replace('_', ' ')}?"
            fixed[key] = q
        return fixed if fixed else {
            "action": {"type": "choice", "instructions": "What action to take?",
                       "criteria": ["proceed", "wait", "stop"]},
            "safe": {"type": "noul", "instructions": "Is it safe to continue?"},
        }

    def _call(self, prompt: str) -> dict:
        try:
            r = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600, temperature=0.2,
            )
            return self._parse(r.choices[0].message.content or "")
        except Exception as e:
            print(f"⚠ LLM error: {e}")
            return {"action": {"type": "choice", "criteria": ["proceed", "wait", "stop"]},
                    "safe": {"type": "noul", "instructions": "Is it safe to continue?"}}

    def _parse(self, text: str) -> dict:
        for pat in [r"```json\s*(\{.*?\})\s*```", r"```\s*(\{.*?\})\s*```", r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})"]:
            m = re.search(pat, text, re.DOTALL)
            if m:
                try: return json.loads(m.group(1))
                except: pass
        try: return json.loads(text.strip())
        except: pass
        print(f"⚠ parse failed:\n{text[:200]}")
        return {"action": {"type": "choice", "criteria": ["proceed", "wait", "stop"]},
                "safe": {"type": "noul", "instructions": "Is it safe?"}}
