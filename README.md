# ReflexBench

**Open benchmark and evaluation harness for System One models, typed decision models, and probabilistic decision engines.**

ReflexBench measures engines such as **TypeSafe Jev, Laya, Reflex/Qwen, Kev, jeff and Verdict** on typed **Choice, Score and Noul/Binary** decisions. It also measures a separate question: how much operational value can a small deterministic **Reflex Core** policy add without changing the model response?

This repository contains **ReflexBench v1.0.0**, the first stable public benchmark release. The benchmark is provider-neutral; Brida Reflex is one consumer of the methodology.

> ReflexBench does not publish a single "best model" score. Semantic quality, calibration, language consistency, option-order robustness, cardinality, failures, latency boundaries and harness/policy value are reported separately.

## v1 headline: same-corpus raw engine quality

The canonical launch leaderboard uses the frozen **111-case public-hard cohort** and reports raw semantic accuracy on identical rows. It does not blend latency, calibration or Reflex policy effects into the headline.

| Engine | Raw semantic accuracy |
|---|---:|
| TypeSafe Jev | **73.0%** |
| upstream Reflex / Qwen3.5-2B | 41.4% |
| frozen Qwen3.5-0.8B readout control | 39.6% |
| jeff / GLiFormer ~400M | 37.8% |
| openJev Verdict 1.4 / 151M | 36.9% |
| Laya base / 421M | 35.1% |
| Kev-0.8B | 32.4% |

These are same-corpus Brida measurement receipts, not a universal model ranking. Hosted and local latency are different deployment boundaries and are reported separately in [RESULTS.md](RESULTS.md).

### Supplemental Reflex Core evidence

ReflexBench also retains policy/harness ablations as a **separate research lane**, not part of the raw-engine leaderboard:

- TypeSafe Jev same-response public fixtures: **96.4% raw -> 100.0% Core**, 4 rescues / 0 harms, 0 extra model calls.
- Independent blind workflow Gate v2: **76.7% raw -> 82.0% Core** on 150/150 completed cases; +5.3 pp, bootstrap 95% +1.3..+10.0 pp.
- Gate v1 remains a formal **FAIL** at 149/150 after one provider 503. Failures stay in the evidence ledger.

## Why this exists

System One models expose fast typed probabilistic decisions instead of generated prose. That changes what a useful benchmark should measure. Accuracy alone is insufficient when software consumes probability vectors and operational policies act on them.

ReflexBench therefore freezes and reports:

- exact corpus/manifests and hashes;
- engine/model identity and revision;
- completion and provider failures;
- semantic accuracy / macro-F1 where appropriate;
- NLL, Brier and ECE;
- Score error;
- option-order stability;
- multilingual consistency;
- Choice cardinality/capability;
- paired bootstrap intervals;
- raw engine vs deterministic policy from the **same response**;
- deployment/hardware boundary for latency claims.

## Reflex Core v1

Core v1 deliberately stays tiny:

```text
bounded state + canonical typed questions
        -> decision engine
        -> same probability response
        -> deterministic workflow-owned policy
        -> branch / review recommendation
```

A model-specific prompt rewrite, semantic adapter or extra inference pass is **not** counted as Core uplift. See [docs/system-one-contract-v1.md](docs/system-one-contract-v1.md).

## Benchmark your model

Maintaining a System One or typed-decision model? Run the frozen protocol and submit a reproducible result. See **[SUBMIT_A_MODEL.md](SUBMIT_A_MODEL.md)** for the adapter contract, identity/provenance requirements, receipt rules and result-PR workflow.

Accepted public results may use the **Evaluated on ReflexBench v1** badge; acceptance records reproducible evidence and is not an endorsement or universal ranking.

For model labs, evaluation platforms and bulk integrations, see **[FOR_LABS.md](FOR_LABS.md)**. ReflexBench also publishes a versioned [result-submission JSON Schema](schemas/result-submission-v1.schema.json), [template](templates/result-submission-v1.json) and dependency-free validator so benchmark evidence can be produced directly from CI.

## Quick start

Requires Python 3.11+ for the core harness. Core v1 uses only the standard library.

```bash
PYTHONPATH=reflexbench python -m unittest discover -s tests -p 'test_*.py' -v
```

Run a System One-compatible HTTP endpoint:

```bash
PYTHONPATH=reflexbench python reflexbench/systemone_reflex_runner.py --help
```

Validate a Reflex recipe registry against the same provider-neutral contract:

```bash
PYTHONPATH=reflexbench python reflexbench/validate_reflex_registry_v1.py --help
```

## Web search / retrieval augmentation

Search stays **outside** the decision model. Fetch current evidence first, apply deterministic freshness/provenance filters, pass a bounded evidence state to a typed decision, then keep action authority in normal code:

```text
web/search/retrieval
 -> deterministic provenance + freshness checks
 -> bounded evidence state
 -> System One model
 -> Reflex policy / review
 -> authorized application action
```

See [examples/web-search-evidence-gate/README.md](examples/web-search-evidence-gate/README.md). Search can improve decision quality by improving the evidence supplied to the same typed judgment; it is not counted as a model improvement unless measured as a separate retrieval-augmented ablation.

## Repository layout

- `reflexbench/` — provider-neutral core harness and reproducibility tools.
- `tests/` — Core v1 contract and evaluation tests.
- `corpora/` — Brida-authored public synthetic fixtures/gates for v1.
- `manifests/` — frozen corpus/procedure identities.
- `results/v1/` — machine-readable reference receipts.
- `docs/` — benchmark card, methodology, Core contract and research reports.
- `release/v1-manifest.json` — hashes for the exported RC.

## What is deliberately not open here

ReflexBench is open; Brida's hosted execution/control plane is not. This repository contains no customer data, provider credentials, private evaluation corpora, hidden future gates, Brida model weights/training corpora, hosted routing, tenant authorization, billing/metering or production activation logic.

The public [`brida-ai/reflex`](https://github.com/brida-ai/reflex) registry and [`brida-ai/sdk`](https://github.com/brida-ai/sdk) are separate OSS projects. Hosted Brida Reflex remains a separately operated service.

## Versioning

`v1.0.0` freezes the benchmark definition. New engine results on the exact same frozen benchmark may land in `v1.x`. Changes to tasks, corpora or scoring that alter comparability require a new major benchmark version. See [VERSIONING.md](VERSIONING.md).

## Status

**ReflexBench v1.0.0 is stable.** The separately operated hosted Brida Reflex service remains availability/release-gated and this benchmark release does not imply hosted GA.

## License

Apache-2.0 for Brida-authored code, docs and fixtures in this repository. Third-party datasets/models retain their own licenses; raw third-party benchmark datasets are not redistributed here unless their license explicitly permits it. See [THIRD_PARTY.md](THIRD_PARTY.md).
