# EKS Architect

> **The Architect and the Executor: Evolutionary Knowledge Systems for Edge AI**
>
> **Febrian Dwi Putra** · [LinkedIn](https://id.linkedin.com/in/febrian-dwi-putra)

---

## What is EKS?

EKS separates two roles that have traditionally been combined in a single LLM:

| Component | Role | Latency | Cost |
|---|---|---|---|
| **LLM** (DeepSeek Coder) | Architect — designs & evolves schemas | Seconds | Called rarely |
| **Laya MLX** | Executor — runtime decisions | 7–14 ms | Free, offline |
| **Compare Gate** | Filter — only promotes better schemas | — | — |
| **Reflect Engine** | Monitor — detects issues, triggers LLM | — | — |

```
Issue detected
      ↓
LLM generates new schema candidate
      ↓
Compare Gate: new > current + 5%?
      ↓ YES
Permanent Core — schema locked forever
      ↓
Laya executes at runtime (zero LLM calls)
```

---

## Prerequisites

**Hardware:**
- Apple Silicon Mac (M1/M2/M3/M4) — required for MLX
- Minimum **24 GB unified memory** (model weights: DeepSeek 8.2 GB + Laya 1 GB)

**System:**
- macOS 14 Sonoma or later
- Python 3.11+

**Install required tools:**

```bash
# 1. Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. uv — Python package manager
brew install uv

# 3. rapid-mlx — local LLM server for Apple Silicon
brew install rapid-mlx

# 4. Pull DeepSeek Coder model (~8.2 GB, one-time download)
rapid-mlx pull deepseek-coder-v2-lite-16b-4bit
```

**Install Python dependencies:**

```bash
cd eks-architect
uv sync
```

That's it. Laya MLX and all other dependencies are installed automatically via `uv sync`.

---

- **DeepSeek Coder V2 Lite 16B 4-bit** — schema architect (via rapid-mlx, port 8001)
- **Laya MLX** (`aac6fef/laya-mlx`) — typed decision executor
- **FastAPI** — OpenAI-compatible bridge API (port 8002)
- **Python 3.13** + **uv**

---

## Quick Start

```bash
# Start everything at once
./run.sh
```

Or manually:

```bash
# 1. Start DeepSeek
rapid-mlx serve deepseek-coder-v2-lite-16b-4bit --port 8001

# 2. Start EKS API
uv run python api.py

# 3. Open simulation
open index.html
```

---

## Project Structure

```
eks-architect/
├── index.html          Visual simulation — integrated with real model
├── api.py              FastAPI backend (DeepSeek + Laya bridge)
├── demo_robot.py       CLI demo — robot navigation
├── run.sh              Start everything + live logs
├── README.md
└── eks/
    ├── eks.py              Main EKS runtime
    ├── core/
    │   ├── schema.py           Knowledge unit (immutable)
    │   ├── permanent_core.py   Append-only schema storage
    │   ├── compare_gate.py     Promotion filter (+5% threshold)
    │   └── reflect_engine.py   Issue detector (repeat / low confidence)
    └── llm/
        └── architect.py        LLM schema generator (DeepSeek)
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/seed` | Seed a new domain schema via LLM |
| `POST` | `/decide` | Send sensor input → get Laya decision |
| `GET`  | `/status` | Current schema + evolution history |
| `GET`  | `/logs?limit=50` | Full decision log (SQLite) |
| `GET`  | `/logs/stats` | Aggregate stats (confidence, issue counts) |
| `POST` | `/reset` | Reset to initial state |

**Example `/decide`:**

```bash
curl -X POST http://localhost:8002/decide \
  -H "Content-Type: application/json" \
  -d '{"input": "Front: 45cm obstacle. Left: 120cm. Battery: 87%."}'
```

```json
{
  "answers": {
    "direction": {"answer": "left",  "confidence": 0.82},
    "speed":     {"answer": "slow",  "confidence": 0.76},
    "safety":    {"answer": true,    "confidence": 0.91}
  },
  "evolved": false,
  "schema_version": 1,
  "schema_name": "robot_navigation — Seed",
  "fields": ["direction", "speed", "safety", "battery"]
}
```

**Example `/logs/stats`:**

```json
{
  "total_decisions": 142,
  "avg_confidence": 0.731,
  "min_confidence": 0.082,
  "total_issues": 3,
  "max_schema_v": 3,
  "top_issues": [
    {"trigger": "repeat '?' 100%", "count": 3}
  ]
}
```

---

## Memory & Logging

EKS has two layers of persistent memory:

**1. Schema Memory (`eks_core/*.json`)** — immutable, append-only  
Every promoted schema is saved as a JSON file. Survives restarts. Never deleted.

```
eks_core/
├── robot_navigation-v1.json   ← seed: direction, speed, safety
├── robot_navigation-v2.json   ← +obstacle, load  (triggered by: repeat)
├── robot_navigation-v3.json   ← +battery, target (triggered by: repeat)
└── decisions.db               ← SQLite decision log
```

**2. Decision Log (`decisions.db`)** — SQLite, append-only  
Every call to `/decide` is logged with: input, answers, confidence, schema version, and any issue triggered.

```bash
# View recent decisions
curl http://localhost:8002/logs?limit=20

# View stats
curl http://localhost:8002/logs/stats
```

**LLM Context Memory:**  
When a reflect event fires and the LLM is asked to evolve the schema, the last 15 decisions are included in the prompt as context — so DeepSeek understands *why* the issue occurred, not just that it did.

```
LLM prompt includes:
  "Last 15 decisions for 'robot_navigation':
    [12:03:44] conf=0.08 | direction=?(0.08) ⚠ repeat '?' 100%
    [12:03:43] conf=0.08 | direction=?(0.08)
    ...
  Stats: 142 total | avg_conf=0.73 | issues=3"
```

---

## How Evolution Works

1. Laya makes decisions → Reflect Engine monitors outputs
2. If `repeat > 80%` or `confidence < 52%` → **Issue detected**
3. LLM (DeepSeek) is called: analyzes the issue, adds new questions to schema
4. Compare Gate: if new accuracy > old + 5% → **PROMOTE**
5. New schema locked to Permanent Core (`./eks_core/*.json`)
6. Robot uses a richer schema — no restart needed

---

## Demo Output

```
🤖 LLM: mlx-community/DeepSeek-Coder-V2-Lite-Instruct-4bit-mlx
✅ Laya loaded
🧠 LLM seeding initial schema...
🔒 Seeded: Schema(robot_navigation-v1 | 4q 🔒)
   Fields: [direction, speed, safety, battery]

[Tick 10] Unknown terrain. Sensor noise...
⚡ Issue: repeat '?' 100%
🧠 LLM generating evolved schema...
⚖️  Compare Gate: +8.0% → PROMOTE ✓
✅ Schema(robot_navigation-v2 | +obstacle, terrain | 6q 🔒)

History:
  robot_navigation-v1   Seed
  robot_navigation-v2   +obstacle, terrain  ← [repeat '?' 100%]
  robot_navigation-v3   +target, priority   ← [repeat '?' 100%]
```

---

## Paper

Full concept: [paper-en.md](../paper/paper-en.md) · [paper-id.md](../paper/paper-id.md)

---

*Apache 2.0 — free to use for research and development.*
