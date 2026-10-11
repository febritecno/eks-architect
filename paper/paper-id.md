# Evolutionary Knowledge System: LLM sebagai Arsitek, Laya sebagai Executor

**The Architect and the Executor — Evolutionary Knowledge Systems for Edge AI**

**Febrian Dwi Putra** · [LinkedIn](https://id.linkedin.com/in/febrian-dwi-putra)

*Draft v0.1 — Oktober 2026* · 🇮🇩 Bahasa Indonesia

---

## Abstrak

Paper ini mengusulkan arsitektur **Evolutionary Knowledge System (EKS)** — sebuah sistem yang memisahkan peran antara Large Language Model (LLM) dan typed decision model (Laya) secara tegas. LLM berperan sebagai *arsitek pengetahuan* yang mahal namun akurat, sementara Laya berperan sebagai *executor keputusan* yang cepat, murah, dan deterministik. Pengetahuan yang telah terbukti baik dikunci secara permanen (*immutable core*), dan setiap kandidat pengetahuan baru harus melewati *comparison gate* sebelum dipromosikan. Repetisi output menjadi sinyal untuk memicu *reflect event* — memanggil LLM untuk deliberate review dan pembaruan schema.

---

## 1. Latar Belakang

### 1.1 Masalah LLM sebagai Runtime Decision Maker

LLM generatif (GPT, Claude, DeepSeek, Qwen, dll.) sangat kapabel namun memiliki karakteristik yang kurang ideal untuk keputusan runtime skala tinggi:

- **Latency tinggi**: 3–10 detik per respons untuk model 27B+
- **Biaya token**: setiap inference mengeluarkan biaya
- **Non-deterministik**: respons yang sama bisa berbeda antar run
- **Overkill**: untuk keputusan sederhana ("kategori apa ini?"), LLM terlalu berat

### 1.2 Laya sebagai Alternatif untuk Keputusan Terstruktur

Laya ([mizorewww/laya-mlx](https://github.com/mizorewww/laya-mlx)) adalah typed decision model berbasis encoder bidirectional (ModernBERT) yang:

- Menjawab pertanyaan terstruktur dalam **7–14 ms** di Apple Silicon M3 Max
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

### 2.2 Tiga Prinsip Inti

#### Prinsip 1: Immutable Core
Pengetahuan yang sudah terbukti baik **tidak boleh diubah sembarangan**. Setiap schema yang telah dipromosikan mendapat version lock dan audit trail. Perubahan hanya bisa terjadi melalui proses promote yang ketat.

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
PROMOTE          REJECT + LOG
→ permanent      → discard
```

#### Prinsip 3: Reflect Event
Ketika Laya menunjukkan tanda-tanda **distribusi shift** — output berulang, confidence drop, atau error rate naik — sistem memicu reflect event untuk memanggil LLM melakukan deliberate review.

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
  LLM merancang schema awal. Tidak perlu training.
  Output: schema JSON dengan choice/score/noul definitions.

Phase 2: DEPLOY (Laya)
  Schema di-deploy. Runtime berjalan tanpa LLM.
  7 ms per keputusan, unlimited throughput, offline.

Phase 3: MONITOR (Reflect Engine)
  Sistem memantau output Laya secara kontinu.
  Anomali → trigger reflect event.

Phase 4: EVOLVE (LLM + Compare Gate)
  LLM dipanggil untuk review dan menghasilkan schema kandidat.
  Hanya schema yang lebih baik yang dipromosikan.

Phase 5: LOCK
  Schema yang dipromosikan dikunci. Tidak bisa diubah
  tanpa melewati proses evolusi lengkap dari awal.
```

---

## 4. Implementasi

Implementasi referensi tersedia di:
**[github.com/febriandwi/eks-architect](https://github.com/febriandwi/eks-architect)** *(coming soon)*

Stack: Python 3.13 · DeepSeek Coder V2 Lite · Laya MLX · FastAPI · Apple Silicon

---

## 5. Contoh Use Case: Robot Navigasi

```python
eks = EKS(
    domain="robot_navigation",
    description="Robot warehouse, sensor ultrasonik, perlu keputusan arah & kecepatan."
)

# Phase 1: LLM seed schema (sekali saja)
# → schema: {direction, speed, safety, battery}

# Phase 2: Runtime loop tanpa LLM
while robot.is_running():
    sensor_data = robot.read_sensors()
    decision = eks.decide(sensor_data)
    # → {direction: "left", speed: "slow", safety: True} — 7 ms
    robot.execute(decision)
    # Reflect engine monitor di background
    # → kalau repeat/stuck → LLM evolve schema otomatis
```

---

## 6. Properti Sistem

| Properti | Nilai |
|---|---|
| Runtime latency (Laya) | 7–14 ms |
| Frekuensi panggil LLM | Hanya saat reflect event |
| Schema mutability | Immutable setelah promote |
| Offline capability | ✅ Penuh (setelah seed) |
| Throughput (Laya) | ~395 decisions/detik |
| Ukuran model (Laya) | ~1 GB |

---

## 7. Batasan dan Future Work

**Batasan saat ini:**
1. Laya tidak support fine-tuning — hanya inference
2. Comparison gate butuh eval dataset untuk scoring yang valid
3. Schema hanya bisa jawab choice/score/noul, tidak free-form

**Future work:**
- Automatic eval dataset generation via LLM synthetic data
- Multi-domain routing dalam satu EKS instance
- Confidence-based escalation ke LLM saat Laya tidak yakin
- Fine-tunable decision model sebagai pengganti Laya

---

## 8. Kesimpulan

EKS memisahkan dua peran yang selama ini digabung dalam satu LLM:

- **Reasoning** → LLM (mahal, tapi jarang dipanggil)
- **Execution** → Laya (murah, cepat, deterministik, offline)

Kuncinya adalah **immutability** dan **comparison gate** — pengetahuan tidak berkembang sembarangan, tapi evolusi terkontrol. Repetisi output menjadi sinyal alami bahwa sistem butuh perspektif baru dari LLM — bukan setiap request, hanya saat benar-benar dibutuhkan.

---

## Referensi

- [laya-mlx](https://github.com/mizorewww/laya-mlx) — Native MLX runtime for Laya typed decision models
- [Laya upstream](https://github.com/NandhaKishorM/laya) — Original Laya by Convai Innovations
- [ModernBERT](https://huggingface.co/answerdotai/ModernBERT-large) — Encoder backbone
- [MLX](https://github.com/ml-explore/mlx) — Apple Silicon ML framework
- Hinton et al., *Distilling the Knowledge in a Neural Network*, 2015

---

*Draft ini merupakan hasil eksplorasi arsitektur. Implementasi referensi bersifat proof-of-concept.*
