# Reflex Core v1 — blind workflow gates

**Status:** frozen ReflexBench v1 harness evidence. This does not authorize automatic protected actions or imply model SOTA.

## Question

Does the **same decision-engine response** become more useful when Reflex Core v1 applies the frozen declarative policy, without prompt rewriting, model-specific semantic adapters, option-order ensembling, or extra semantic inference?

## Gate history

| Gate | Rows complete | Raw exact | Core exact | Delta | Rescues / harms | Same response | Formal result |
|---|---:|---:|---:|---:|---:|---:|---|
| v1 | 149/150 | 45.0% | 64.4% | +19.5 pp | 29 / 0 | yes | **FAIL — completion** |
| v2 | 150/150 | 76.7% | 82.0% | +5.3 pp | 10 / 2 | yes | **PASS** |

Gate v1 is retained as authoritative failed evidence: its semantic signal was positive, but one provider 503 left it at 149/150 completion. It was not retroactively repaired under the same gate identity.

Gate v2 was frozen as an independent replication **before its case pack and before inference**, with five different workflows, 75 new paired EN/ES scenarios (150 rows), zero exact state+expected-branch collisions with prior corpora, and a predeclared transport-only retry policy. The authoritative run completed 150/150 and used **zero retries**.

## Gate v2 result

Jev raw is **76.7%** (115/150); the same Jev responses under Reflex Core v1 are **82.0%** (123/150): **+5.3 pp**, 10 rescues / 2 harms. Paired bootstrap 95% CI is **+1.3 pp..+10.0 pp**.

The invariant holds: 150 HTTP requests for 150 completed decisions, 0 retry requests, no option ensemble, no native permutations, no prompt rewrite, and no model-specific semantic adapter.

### Language

| Language | Raw | Core | Delta | Rescues / harms |
|---|---:|---:|---:|---:|
| EN | 76.0% | 81.3% | +5.3 pp | 5 / 1 |
| ES | 77.3% | 82.7% | +5.3 pp | 5 / 1 |

EN and ES each improve by exactly +5.33 pp in this gate; the gain is not coming from only one language.

### Primitive/policy type

| Type | Raw | Core | Delta | Rescues / harms | Review rate |
|---|---:|---:|---:|---:|---:|
| binary | 100.0% | 100.0% | +0.0 pp | 0 / 0 | 86.7% |
| choice | 73.3% | 82.2% | +8.9 pp | 10 / 2 | 53.3% |
| score | 63.3% | 63.3% | +0.0 pp | 0 / 0 | 0.0% |

The net uplift is concentrated in **Choice**. Binary is already perfect on this replication lane and Score receives no same-response policy uplift.

### Case class

| Class | Raw | Core | Delta | Rescues / harms |
|---|---:|---:|---:|---:|
| clear | 100.0% | 96.0% | -4.0 pp | 0 / 2 |
| boundary | 70.0% | 80.0% | +10.0 pp | 5 / 0 |
| ambiguous | 60.0% | 70.0% | +10.0 pp | 5 / 0 |

This is the important limitation: boundary and ambiguous rows each gain +10 pp with zero harms, while clear rows move 100% -> 96% because two already-correct change-review-risk predictions are sent to review by the existing confidence threshold.

## Operational interpretation

The v2 gate proves **positive net exact-branch value** for Core v1, but not production-ready automatic action. Automation coverage is 50.7%, review rate is 49.3%, and observed direct-action accuracy is 67.1%. Those are separate product objectives and must not be hidden behind the passing exact-branch gate.

The next policy work should therefore target a better risk/coverage frontier and removal of clear-case harms on **new** development/calibration evidence. Gate v2 is now consumed evidence and must not be tuned against.

## Conclusion

The simplified product hypothesis survives an independent blind replication: **same model, same request, same response; deterministic Reflex policy adds statistically positive net branch value.** That is a useful Reflex claim. It is not evidence that Reflex makes every primitive better, that the current thresholds are universally optimal, or that any Brida-owned model is SOTA.
