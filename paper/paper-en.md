# The Architect and the Executor: Evolutionary Knowledge Systems for Edge AI

**Febrian Dwi Putra** · [LinkedIn](https://id.linkedin.com/in/febrian-dwi-putra)

*Draft v0.1 — October 2026* · 🇬🇧 English

---

## Abstract

This paper proposes the **Evolutionary Knowledge System (EKS)** architecture — a system that cleanly separates the roles of a Large Language Model (LLM) and a typed decision model (Laya). The LLM acts as a costly but accurate *knowledge architect*, while Laya serves as a fast, cheap, and deterministic *decision executor*. Proven knowledge is permanently locked (*immutable core*), and every candidate schema must pass a *comparison gate* before promotion. Repeated outputs signal a *reflect event* — invoking the LLM for deliberate review and schema evolution.

---

## 1. Background

### 1.1 The Problem with LLMs as Runtime Decision Makers

Generative LLMs (GPT, Claude, DeepSeek, Qwen, etc.) are highly capable but poorly suited for high-throughput runtime decisions:

- **High latency**: 3–10 seconds per response for 27B+ models
- **Token cost**: every inference incurs a fee
- **Non-determinism**: identical inputs can produce different outputs
- **Overkill**: for simple decisions ("which category is this?"), an LLM is excessive

### 1.2 Laya as an Alternative for Structured Decisions

Laya ([mizorewww/laya-mlx](https://github.com/mizorewww/laya-mlx)) is a typed decision model built on a bidirectional encoder (ModernBERT) that:

- Answers structured questions in **7–14 ms** on Apple Silicon M3 Max
- Performs no token generation — only a forward pass → probabilities
- Supports three answer types: `choice`, `score`, `noul` (true/false probability)
- Runs **locally, offline, free**, with unlimited throughput
- Model size ~1 GB (vs. 15 GB for a 27B LLM)

### 1.3 The Gap to Bridge

Laya is powerful but requires a well-designed **schema** — the structured set of questions it answers. That schema is the system's "knowledge." The key question: **who designs and updates it?**

The answer: the LLM — but only once per evolutionary cycle, not on every request.

---

## 2. EKS Architecture

### 2.1 Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                   EVOLUTIONARY KNOWLEDGE SYSTEM              │
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │  LLM LAYER   │     │  COMPARE     │     │  LAYA LAYER │  │
│  │  (Architect) │────▶│  GATE        │────▶│  (Executor) │  │
│  │              │     │              │     │             │  │
│  │ - Design     │     │ - Evaluate   │     │ - Runtime   │  │
│  │   schema     │     │ - Promote    │     │   decision  │  │
│  │ - Review     │     │ - Reject     │     │ - 7–14 ms   │  │
│  │ - Deliberate │     │              │     │ - Offline   │  │
│  └──────┬───────┘     └──────────────┘     └──────┬──────┘  │
│         │                                         │         │
│         │          ┌──────────────────┐           │         │
│         └─────────▶│  PERMANENT CORE  │◀──────────┘         │
│                    │  (Immutable)     │                      │
│                    │ - Proven schemas │                      │
│                    │ - Locked version │                      │
│                    │ - Audit trail    │                      │
│                    └────────┬─────────┘                      │
│                             │                                │
│                    ┌────────▼─────────┐                      │
│                    │  REFLECT ENGINE  │                      │
│                    │ - Monitor output │                      │
│                    │ - Detect repeat  │                      │
│                    │ - Trigger LLM    │                      │
│                    └──────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Three Core Principles

#### Principle 1: Immutable Core
Proven knowledge **must not be changed arbitrarily**. Every promoted schema receives a version lock and audit trail. Changes can only occur through a strict promotion process.

#### Principle 2: Comparison Gate
Every new knowledge candidate must **outperform** the current one by a measurable margin before promotion. No automatic updates — all changes must be justified by data.

```
new_schema vs current_schema
        ↓
  [Evaluation Metrics]
  - accuracy score
  - confidence distribution
  - edge case coverage
        ↓
  new > current + threshold?
  ↓ YES              ↓ NO
PROMOTE          REJECT + LOG
→ permanent      → discard
```

#### Principle 3: Reflect Event
When Laya shows signs of **distribution shift** — repeated outputs, confidence drops, or rising error rates — the system fires a reflect event, invoking the LLM for deliberate review.

```
Monitor signals:
  - same_decision(last_N) → repeat detected
  - avg_confidence < threshold → uncertainty spike
        ↓
  REFLECT EVENT → LLM review → new schema candidate
        ↓
  → Comparison Gate
```

---

## 3. Knowledge Lifecycle

```
Phase 1: SEED (LLM)
  LLM designs the initial schema from domain knowledge.
  No training required — runtime instructions are sufficient.

Phase 2: DEPLOY (Laya)
  Schema deployed to Laya. Runtime operates without LLM.
  7 ms per decision, unlimited throughput, fully offline.

Phase 3: MONITOR (Reflect Engine)
  System continuously monitors Laya outputs.
  Anomaly detected → reflect event triggered.

Phase 4: EVOLVE (LLM + Compare Gate)
  LLM called for review, produces a candidate schema.
  Only schemas that improve over the current one are promoted.

Phase 5: LOCK
  Promoted schema is locked. Cannot be changed without
  passing through the full evolution cycle again.
```

---

## 4. Implementation

Reference implementation available at:
**[github.com/febritecno/eks-architect](https://github.com/febritecno/eks-architect)**

Stack: Python 3.13 · DeepSeek Coder V2 Lite · Laya MLX · FastAPI · Apple Silicon

---

## 5. Use Case: Robot Navigation

```python
eks = EKS(
    domain="robot_navigation",
    description="Warehouse robot with ultrasonic sensors. Needs direction & speed decisions."
)

# Phase 1: LLM seeds schema (once only)
# → schema: {direction, speed, safety, battery}

# Phase 2: Runtime loop — no LLM
while robot.is_running():
    sensor_data = robot.read_sensors()
    decision = eks.decide(sensor_data)
    # → {direction: "left", speed: "slow", safety: True} — 7 ms
    robot.execute(decision)
    # Reflect engine monitors in background
    # → if repeat/stuck → LLM evolves schema automatically
```

---

## 6. System Properties

| Property | Value |
|---|---|
| Runtime latency (Laya) | 7–14 ms |
| LLM invocation frequency | Only on reflect events |
| Schema mutability | Immutable after promotion |
| Offline capability | ✅ Full (after seed) |
| Throughput (Laya) | ~395 decisions/second |
| Model size (Laya) | ~1 GB |

---

## 7. Limitations and Future Work

**Current limitations:**
1. Laya does not support fine-tuning — inference only
2. The comparison gate requires an eval dataset for valid scoring
3. Schemas are limited to choice/score/noul — no free-form output

**Future work:**
- Automatic eval dataset generation via LLM synthetic data
- Multi-domain routing within a single EKS instance
- Confidence-based LLM escalation when Laya is uncertain
- Fine-tunable decision model as a Laya replacement

---

## 8. Conclusion

EKS separates two roles that have traditionally been combined in a single LLM:

- **Reasoning** → LLM (expensive, but called rarely)
- **Execution** → Laya (cheap, fast, deterministic, offline)

The key insight is **immutability** combined with a **comparison gate** — knowledge does not evolve arbitrarily, but through controlled, data-justified steps. Repeated outputs become a natural signal that the system needs a fresh perspective from the LLM — not on every request, but precisely when needed.

> *"The LLM is the engineer who writes the procedure.  
> Laya is the operator who executes it perfectly, every time."*

---

## References

- [laya-mlx](https://github.com/mizorewww/laya-mlx) — Native MLX runtime for Laya typed decision models
- [Laya upstream](https://github.com/NandhaKishorM/laya) — Original Laya by Convai Innovations
- [ModernBERT](https://huggingface.co/answerdotai/ModernBERT-large) — Encoder backbone
- [MLX](https://github.com/ml-explore/mlx) — Apple Silicon ML framework
- Hinton et al., *Distilling the Knowledge in a Neural Network*, 2015
- Constitutional AI, Anthropic, 2022

---

*This draft is the result of architectural exploration. The reference implementation is a proof-of-concept.*
