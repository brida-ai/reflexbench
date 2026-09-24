# ReflexBench v1 results

All numbers below are frozen Brida measurement receipts unless explicitly marked as external context. Hosted and local latency are different deployment boundaries and are **not** normalized into a speed ranking.

## Primary raw-engine lane: same-corpus public hard cohort (111 cases)

| Engine | Accuracy | ECE ↓ | Score MAE ↓ | p50 | Boundary |
|---|---:|---:|---:|---:|---|
| TypeSafe Jev | **73.0%** | 0.088 | 0.410 | 345.8 ms | hosted route |
| upstream Reflex / Qwen3.5-2B | 41.4% | 0.271 | 0.898 | 124.0 ms | local RTX 3070 HTTP |
| frozen Qwen3.5-0.8B readout control | 39.6% | 0.215 | 0.711 | excluded | reference kernels |
| jeff / GLiFormer ~400M | 37.8% | 0.232 | 0.581 | 57.6 ms | local RTX 3070 HTTP |
| openJev Verdict 1.4 / 151M | 36.9% | 0.124 | 0.662 | 64.0 ms | local RTX 3070 HTTP |
| Laya base / 421M | 35.1% | 0.236 | 0.602 | 70.9 ms | local RTX 3070 HTTP |
| Kev-0.8B | 32.4% | 0.440 | 0.603 | 109.6 ms | local RTX 3070 HTTP |

The 111 public-hard rows are now development evidence for Brida and may not later be presented as an untouched Brida model gate.

## Supplemental research: Reflex Core v1 same-response value

| Evidence | Raw engine | Reflex Core | Delta | Rescues / harms | Completion |
|---|---:|---:|---:|---:|---:|
| Public product fixtures (Jev) | 96.4% | **100.0%** | +3.6 pp | 4 / 0 | 110/110 |
| Blind workflow Gate v1 (Jev) | 45.0% | **64.4%** | +19.5 pp | 29 / 0 | 149/150 — **FAIL** |
| Blind workflow Gate v2 (Jev) | 76.7% | **82.0%** | +5.3 pp | 10 / 2 | 150/150 — **PASS** |

Gate v1 remains failed because one provider 503 prevented 100% completion. Gate v2 was independently frozen before inference, used a different case pack, completed 150/150 and used zero transport retries. Gate v2 proves positive net same-response harness value; it does **not** prove automatic-action safety or global policy optimality.

## Multilingual Choice

### Common 20-way lane (200 EN/ES decisions)

| Engine | Raw accuracy | EN | ES | EN↔ES same prediction |
|---|---:|---:|---:|---:|
| TypeSafe Jev | **79.5%** | 81.0% | 78.0% | 91.0% |
| upstream Reflex / Qwen3.5-2B | 65.0% | 70.0% | 60.0% | 80.0% |
| jeff | 62.5% | 71.0% | 54.0% | 71.0% |
| Kev-0.8B | 60.5% | 69.0% | 52.0% | 70.0% |
| Laya base | 60.5% | 72.0% | 49.0% | 54.0% |
| Laya multilingual | 60.0% | 64.0% | 56.0% | 75.0% |
| Laya typed | 59.5% | 71.0% | 48.0% | 54.0% |
| Verdict 1.4 | 39.0% | 60.0% | 18.0% | 48.0% |

### High-cardinality 60-way lane (118 EN/ES decisions)

| Engine | Accuracy | EN | ES | EN↔ES same prediction | Capability |
|---|---:|---:|---:|---:|---|
| TypeSafe Jev | **75.4%** | 76.3% | 74.6% | 94.9% | ≥60 observed |
| jeff | 61.9% | 69.5% | 54.2% | 74.6% | ≥60 observed |
| Kev-0.8B | 56.8% | 59.3% | 54.2% | 64.4% | ≥60 observed |
| Laya multilingual | 43.2% | 45.8% | 40.7% | 52.5% | ≥60 observed |
| Laya typed | 43.2% | 49.2% | 37.3% | 42.4% | ≥60 observed |
| Laya base | 41.5% | 42.4% | 40.7% | 47.5% | ≥60 observed |
| upstream Reflex / Qwen3.5-2B | — | — | — | — | unsupported: max 26 |
| Verdict 1.4 | — | — | — | — | unsupported: max 24 |

Unsupported capability is not scored as 0% accuracy.

## Choice cardinality

The exact-code lane tests **representation capacity only**, not semantic intelligence.

- TypeSafe Jev: complete/correct through K=255 after explicit provider retry ledger.
- Kev-0.8B: complete through K=255 locally.
- Laya base: complete through K=100; K=255 fails on the tested shared-head `head_max_len=192` boundary.

## Methodology notes

- Failures stay in the evidence ledger.
- Probabilities are scored, not just argmax labels.
- Order-reversal ensembles are experimental layers and reported separately because they add calls/latency.
- Global confidence thresholds are not assumed portable across engines/workflows.
- Public product fixtures and blind synthetic workflow gates are harness/product evidence, not independent model-superiority evidence.
- Third-party full benchmark results are context only unless Brida reproduced them on the same frozen corpus/protocol.

Machine-readable artifacts under `results/v1/` are the source of truth.
