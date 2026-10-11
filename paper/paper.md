# Evolutionary Knowledge System: LLM sebagai Arsitek, Laya sebagai Executor

**The Architect and the Executor — Evolutionary Knowledge Systems for Edge AI**

**Febrian Dwi Putra** · [LinkedIn](https://id.linkedin.com/in/febrian-dwi-putra)

*Draft v0.1 — Oktober 2026*

> Tersedia dalam dua bahasa:
> - 🇮🇩 [paper-id.md](./paper-id.md) — Bahasa Indonesia
> - 🇬🇧 [paper-en.md](./paper-en.md) — English

---

## Abstract

Paper ini mengusulkan arsitektur **Evolutionary Knowledge System (EKS)** — sebuah sistem yang memisahkan peran antara Large Language Model (LLM) dan typed decision model (Laya) secara tegas. LLM berperan sebagai *arsitek pengetahuan* yang mahal namun akurat, sementara Laya berperan sebagai *executor keputusan* yang cepat, murah, dan deterministik. Pengetahuan yang telah terbukti baik dikunci secara permanen (*immutable core*), dan setiap kandidat pengetahuan baru harus melewati *comparison gate* sebelum dipromosikan. Repetisi output menjadi sinyal untuk memicu *reflect event* — memanggil LLM untuk deliberate review dan pembaruan schema.

---

## 1. Latar Belakang

### 1.1 Masalah LLM sebagai Runtime Decision Maker

LLM generatif (GPT, Claude, DeepSeek, Qwen, dll.) sangat kapabel namun memiliki karakteristik yang kurang ideal untuk keputusan runtime skala tinggi:

- **Latency tinggi**: 3-10 detik per respons untuk model 27B+
- **Biaya token**: setiap inference mengeluarkan biaya
- **Non-deterministik**: respons yang sama bisa berbeda antar run
- **Overkill**: untuk keputusan sederhana ("kategori apa ini?"), LLM terlalu berat

### 1.2 Laya sebagai Alternatif untuk Keputusan Terstruktur

Laya ([mizorewww/laya-mlx](https://github.com/mizorewww/laya-mlx)) adalah typed decision model berbasis encoder bidirectional (ModernBERT) yang:

- Menjawab pertanyaan terstruktur dalam **7-14ms** di Apple Silicon M3 Max
- Tidak melakukan token generation — hanya forward pass → probabilitas
- Mendukung tipe jawaban: `choice`, `score`, `noul` (true/false probability)
- Berjalan **lokal, offline, gratis**, tanpa batas throughput
- Ukuran model ~1 GB (vs 15 GB untuk LLM 27B)

### 1.3 Gap yang Ingin Dijembatani

Laya powerful tapi membutuhkan **schema** yang dirancang dengan baik. Schema inilah yang menjadi "pengetahuan" sistem. Pertanyaannya: **siapa yang merancang dan memperbarui schema tersebut?**

Jawaban: LLM — tapi hanya sekali per siklus evolusi, bukan setiap request.

---

## 2. Arsitektur Evolutionary Knowledge System

### 2.1 Komponen Utama

```
┌─────────────────────────────────────────────────────────────┐
│                   EVOLUTIONARY KNOWLEDGE SYSTEM              │
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │  LLM LAYER   │     │  COMPARE     │     │  LAYA LAYER │  │
│  │  (Arsitek)   │────▶│  GATE        │────▶│  (Executor) │  │
│  │              │     │              │     │             │  │
│  │ - Merancang  │     │ - Evaluate   │     │ - Runtime   │  │
│  │   schema     │     │ - Promote    │     │   decision  │  │
│  │ - Review     │     │ - Reject     │     │ - 7-14ms    │  │
│  │ - Deliberate │     │              │     │ - Offline   │  │
│  └──────┬───────┘     └──────────────┘     └──────┬──────┘  │
│         │                                         │         │
│         │          ┌──────────────────┐           │         │
│         └─────────▶│  PERMANENT CORE  │◀──────────┘         │
│                    │  (Immutable)     │                      │
│                    │                  │                      │
│                    │ - Proven schemas │                      │
│                    │ - Locked version │                      │
│                    │ - Audit trail    │                      │
│                    └────────┬─────────┘                      │
│                             │                                │
│                    ┌────────▼─────────┐                      │
│                    │  REFLECT ENGINE  │                      │
│                    │                  │                      │
│                    │ - Monitor output │                      │
│                    │ - Detect repeat  │                      │
│                    │ - Trigger LLM    │                      │
│                    └──────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Tiga Prinsip Inti

#### Prinsip 1: Immutable Core
Pengetahuan yang sudah terbukti baik **tidak boleh diubah sembarangan**. Setiap schema yang telah dipromosikan ke permanent core mendapat version lock dan audit trail. Perubahan hanya bisa terjadi melalui proses promote yang ketat.

#### Prinsip 2: Comparison Gate
Setiap kandidat pengetahuan baru harus **mengalahkan** yang lama secara terukur sebelum dipromosikan. Tidak ada update otomatis — semua perubahan harus justified.

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
    PROMOTE            REJECT + LOG
    → permanent        → discard
```

#### Prinsip 3: Reflect Event
Ketika Laya menunjukkan tanda-tanda **distribusi shift** — output berulang, confidence drop, atau error rate naik — sistem memicu reflect event: memanggil LLM untuk deliberate review.

```
Monitor signals:
  - same_decision(last_N_outputs) → repeat detected
  - avg_confidence < threshold → uncertainty spike
  - error_rate > baseline → performance degradation
        ↓
  REFLECT EVENT triggered
        ↓
  LLM reviews:
  - "Kenapa Laya stuck?"
  - "Apa yang berubah di input distribution?"
  - "Schema apa yang lebih tepat?"
        ↓
  New schema candidate
        ↓
  → Comparison Gate
```

---

## 3. Knowledge Lifecycle

```
Phase 1: SEED (LLM)
─────────────────────
LLM merancang schema awal berdasarkan domain knowledge.
Tidak perlu training — instruksi runtime sudah cukup.

    LLM: "Untuk navigasi robot, parameter keputusan apa?"
    Output: schema JSON dengan choice/score/noul definitions

Phase 2: DEPLOY (Laya)
──────────────────────
Schema di-deploy ke Laya. Runtime berjalan tanpa LLM.
7ms per keputusan, unlimited throughput, offline.

    sensor_data → Laya + schema → decision → action

Phase 3: MONITOR (Reflect Engine)
──────────────────────────────────
System terus memantau output Laya.
Anomali → trigger reflect event.

    if repeat_detected or confidence_drop:
        trigger_reflect_event()

Phase 4: EVOLVE (LLM + Compare Gate)
──────────────────────────────────────
LLM dipanggil untuk review. Menghasilkan schema kandidat baru.
Kandidat masuk comparison gate. Hanya yang lebih baik dipromosikan.

    LLM → new_schema_candidate
    compare(new_schema, current_schema)
    if new > current: promote → permanent_core

Phase 5: LOCK
─────────────
Schema yang dipromosikan dikunci. Tidak bisa diubah tanpa
melewati proses evolusi lengkap dari awal.
```

---

## 4. Implementasi Skeleton

### 4.1 Struktur Data

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import hashlib
import json

@dataclass
class Schema:
    """Unit pengetahuan dalam EKS."""
    id: str
    version: int
    domain: str
    questions: dict[str, Any]          # Laya question definitions
    created_at: datetime
    promoted_at: datetime | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    locked: bool = False
    parent_id: str | None = None       # lineage tracking

    def fingerprint(self) -> str:
        """Hash deterministik dari schema content."""
        content = json.dumps(self.questions, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:12]


@dataclass 
class ReflectEvent:
    """Dipicu saat anomali terdeteksi."""
    trigger: str                        # "repeat" | "confidence_drop" | "error_rate"
    context: list[dict]                 # recent inputs/outputs
    timestamp: datetime
    resolved: bool = False
    new_schema_id: str | None = None
```

### 4.2 Permanent Core

```python
class PermanentCore:
    """Immutable storage untuk schema yang sudah proven."""
    
    def __init__(self, storage_path: str):
        self.path = storage_path
        self._schemas: dict[str, Schema] = {}
        self._load()
    
    def lock(self, schema: Schema) -> Schema:
        """Kunci schema ke permanent core. Tidak bisa di-unlock."""
        if schema.id in self._schemas:
            raise ValueError(f"Schema {schema.id} already locked")
        
        schema.locked = True
        schema.promoted_at = datetime.now()
        self._schemas[schema.id] = schema
        self._persist()
        return schema
    
    def get_current(self, domain: str) -> Schema | None:
        """Ambil schema aktif untuk domain tertentu."""
        domain_schemas = [
            s for s in self._schemas.values() 
            if s.domain == domain and s.locked
        ]
        if not domain_schemas:
            return None
        return max(domain_schemas, key=lambda s: s.version)
    
    def _persist(self):
        # Simpan ke disk — append only, tidak ada delete
        ...
    
    def _load(self):
        ...
```

### 4.3 Comparison Gate

```python
class ComparisonGate:
    """Evaluasi kandidat schema vs current. Hanya promote yang lebih baik."""
    
    PROMOTION_THRESHOLD = 0.05          # new harus 5% lebih baik
    
    def evaluate(
        self, 
        candidate: Schema, 
        current: Schema,
        eval_dataset: list[dict]
    ) -> tuple[bool, dict]:
        """
        Returns: (should_promote, metrics_comparison)
        """
        candidate_score = self._score(candidate, eval_dataset)
        current_score = self._score(current, eval_dataset)
        
        delta = candidate_score["accuracy"] - current_score["accuracy"]
        should_promote = delta > self.PROMOTION_THRESHOLD
        
        return should_promote, {
            "candidate": candidate_score,
            "current": current_score,
            "delta": delta,
            "promoted": should_promote
        }
    
    def _score(self, schema: Schema, dataset: list[dict]) -> dict:
        """Jalankan schema di Laya, ukur akurasi vs ground truth."""
        import laya_mlx as laya
        agent = laya.load("aac6fef/laya-mlx")
        
        correct = 0
        confidences = []
        
        for item in dataset:
            result = agent.predict(item["input"], schema.questions)
            confidences.append(
                max(a["confidence"] for a in result["answers"].values())
            )
            if result["answers"].get(item["target_key"], {}).get("answer") == item["expected"]:
                correct += 1
        
        return {
            "accuracy": correct / len(dataset),
            "avg_confidence": sum(confidences) / len(confidences),
            "n_samples": len(dataset)
        }
```

### 4.4 Reflect Engine

```python
from collections import deque

class ReflectEngine:
    """Monitor output Laya, deteksi anomali, trigger reflect event."""
    
    REPEAT_WINDOW = 10                  # cek N output terakhir
    REPEAT_THRESHOLD = 0.8             # 80% sama = repeat
    CONFIDENCE_FLOOR = 0.55            # di bawah ini = uncertainty spike
    
    def __init__(self, llm_client, core: PermanentCore, gate: ComparisonGate):
        self.llm = llm_client
        self.core = core
        self.gate = gate
        self._output_history: deque = deque(maxlen=self.REPEAT_WINDOW)
        self._events: list[ReflectEvent] = []
    
    def record(self, input_data: str, output: dict):
        """Catat setiap output Laya."""
        key_answer = list(output["answers"].values())[0].get("answer")
        self._output_history.append({
            "input": input_data,
            "answer": key_answer,
            "confidence": list(output["answers"].values())[0].get("confidence", 1.0)
        })
        self._check_anomaly()
    
    def _check_anomaly(self):
        if len(self._output_history) < self.REPEAT_WINDOW:
            return
        
        recent = list(self._output_history)
        
        # Cek repetisi
        answers = [r["answer"] for r in recent]
        most_common_ratio = answers.count(max(set(answers), key=answers.count)) / len(answers)
        
        if most_common_ratio >= self.REPEAT_THRESHOLD:
            self._trigger_reflect("repeat", recent)
            return
        
        # Cek confidence drop
        avg_conf = sum(r["confidence"] for r in recent) / len(recent)
        if avg_conf < self.CONFIDENCE_FLOOR:
            self._trigger_reflect("confidence_drop", recent)
    
    def _trigger_reflect(self, trigger: str, context: list[dict]):
        event = ReflectEvent(
            trigger=trigger,
            context=context,
            timestamp=datetime.now()
        )
        self._events.append(event)
        
        print(f"[REFLECT] Triggered: {trigger}")
        
        # Minta LLM untuk review dan generate schema baru
        new_schema = self._llm_review(event)
        
        if new_schema:
            current = self.core.get_current(new_schema.domain)
            if current:
                should_promote, metrics = self.gate.evaluate(
                    new_schema, current, eval_dataset=[]  # inject eval data
                )
                if should_promote:
                    self.core.lock(new_schema)
                    event.resolved = True
                    event.new_schema_id = new_schema.id
                    print(f"[REFLECT] Resolved: new schema promoted (delta={metrics['delta']:.3f})")
                else:
                    print(f"[REFLECT] Candidate rejected (delta={metrics['delta']:.3f})")
    
    def _llm_review(self, event: ReflectEvent) -> Schema | None:
        """Kirim context ke LLM, minta schema baru."""
        prompt = f"""
        Sistem deteksi anomali: {event.trigger}
        
        Recent outputs:
        {json.dumps(event.context, indent=2)}
        
        Analisis mengapa sistem stuck/tidak akurat dan 
        rancang schema Laya yang lebih baik untuk konteks ini.
        Return JSON schema dengan format Laya (choice/score/noul).
        """
        
        response = self.llm.complete(prompt)
        # Parse response → Schema object
        ...
```

### 4.5 Main Runtime

```python
class EvolutionaryKnowledgeSystem:
    """Entrypoint utama EKS."""
    
    def __init__(self, domain: str, llm_client, storage_path: str = "./eks_core"):
        import laya_mlx as laya
        
        self.domain = domain
        self.agent = laya.load("aac6fef/laya-mlx")
        self.core = PermanentCore(storage_path)
        self.gate = ComparisonGate()
        self.reflect = ReflectEngine(llm_client, self.core, self.gate)
    
    def decide(self, input_data: str) -> dict:
        """Runtime decision — tanpa LLM, 7ms."""
        schema = self.core.get_current(self.domain)
        if not schema:
            raise RuntimeError("No schema available. Run seed() first.")
        
        result = self.agent.predict(input_data, schema.questions)
        
        # Monitor untuk anomali
        self.reflect.record(input_data, result)
        
        return result["answers"]
    
    def seed(self, description: str):
        """Bootstrap: minta LLM rancang schema awal."""
        # LLM generate schema → lock ke core
        ...
```

---

## 5. Contoh Use Case: Robot Navigasi

```python
# Setup
eks = EvolutionaryKnowledgeSystem(
    domain="robot_navigation",
    llm_client=openai_client
)

# Phase 1: Seed schema dari LLM (sekali saja)
eks.seed("Robot navigasi warehouse, perlu keputusan gerak real-time")

# Phase 2: Runtime loop (tanpa LLM)
while robot.is_running():
    sensor_data = robot.read_sensors()
    
    decision = eks.decide(sensor_data)
    # → {"direction": "left", "urgency": "medium", "safe": True}
    # → 7ms, offline, gratis
    
    robot.execute(decision)
    # Reflect engine monitor otomatis di background
```

---

## 6. Properti Sistem

| Properti | Nilai |
|----------|-------|
| Runtime latency (Laya) | 7–14 ms |
| LLM invocation frequency | Hanya saat reflect event |
| Schema mutability | Immutable setelah promote |
| Knowledge evolution | Incremental, version-tracked |
| Offline capability | ✅ Penuh (setelah seed) |
| Throughput (Laya) | ~395 decisions/detik |
| Model size (Laya) | ~1 GB |
| False positive protection | Comparison gate + threshold |

---

## 7. Batasan dan Future Work

### Batasan Saat Ini

1. **Laya tidak support fine-tuning** — hanya inference, schema design bukan weight update
2. **Comparison gate butuh eval dataset** — perlu ground truth untuk scoring yang valid
3. **LLM dependency** — untuk reflect event tetap butuh LLM akses (meski jarang)
4. **Schema expressiveness** — hanya bisa jawab choice/score/noul, tidak bisa free-form

### Future Work

- **Automatic eval dataset generation** — LLM generate synthetic test cases saat seeding
- **Multi-domain routing** — satu EKS mengelola banyak domain dengan schema berbeda
- **Schema composition** — kombinasi beberapa schema untuk keputusan kompleks
- **Confidence-based escalation** — kalau Laya tidak yakin, otomatis escalate ke LLM
- **Fine-tunable decision model** — extend ke model yang bisa dilatih ulang dengan data baru

---

## 8. Kesimpulan

Evolutionary Knowledge System memisahkan dua peran yang selama ini digabung dalam satu LLM:

- **Reasoning** → tetap di LLM (mahal, tapi jarang dipanggil)
- **Execution** → pindah ke Laya (murah, cepat, deterministik)

Kuncinya adalah **immutability** dan **comparison gate** — pengetahuan tidak berkembang sembarangan, tapi evolusi terkontrol. Repetisi output menjadi sinyal alami bahwa sistem butuh perspektif baru dari LLM.

Hasilnya: sistem yang bisa berjalan offline, murah di runtime, tapi tetap punya mekanisme untuk tumbuh dan menyesuaikan diri dengan dunia yang berubah — tanpa keluar dari kendali.

---

## Referensi

- [laya-mlx](https://github.com/mizorewww/laya-mlx) — Native MLX runtime for Laya typed decision models
- [Laya upstream](https://github.com/NandhaKishorM/laya) — Original Laya implementation by Convai Innovations
- [ModernBERT](https://huggingface.co/answerdotai/ModernBERT-large) — Encoder backbone untuk Laya English checkpoint
- [MLX](https://github.com/ml-explore/mlx) — Apple Silicon ML framework
- Hinton et al., "Distilling the Knowledge in a Neural Network", 2015
- Constitutional AI, Anthropic, 2022

---

*Draft ini merupakan hasil diskusi eksplorasi arsitektur. Implementasi skeleton bersifat illustrative dan belum production-ready.*
