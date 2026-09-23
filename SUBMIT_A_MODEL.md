# Submit a model to ReflexBench

ReflexBench accepts reproducible third-party model results against frozen benchmark versions.

The goal is simple: if you maintain a System One model, typed decision model, probabilistic decision engine, or compatible hosted API, you should be able to run the same public protocol and submit evidence without changing benchmark semantics.

## 1. Pick the frozen benchmark version

For v1, do not edit tasks or scoring. Use the committed v1 corpora/manifests and verify their hashes before running.

```bash
python3 tools/check_public_release.py .
```

A material task/scoring change belongs in a future benchmark version, not a v1 result submission.

## 2. Implement or configure an adapter

A compatible engine must map the canonical ReflexBench task shapes to the engine's public interface without changing task meaning:

- Binary / Noul
- Choice
- Score

Provider-specific transport/authentication is allowed. Provider-specific semantic rewriting that changes the task is not considered a comparable v1 run.

Use the existing provider-neutral HTTP runner as the reference contract:

```bash
PYTHONPATH=reflexbench python3 reflexbench/systemone_reflex_runner.py --help
```

## 3. Pin identity

Every submitted result must identify, when observable:

- model/engine owner;
- canonical model/engine name;
- immutable model/checkpoint revision;
- adapter/runner code revision;
- benchmark version;
- corpus/manifests SHA-256;
- local hardware or hosted deployment boundary;
- date of execution;
- retry/failure behavior.

Do not use an ambiguous wire alias as model identity.

## 4. Keep failures

Do not drop failed rows, unsupported task shapes, timeouts, provider errors or retries from the evidence. Completion rate is part of the result.

## 5. Produce machine-readable receipts

Submit the raw ReflexBench result receipt(s), not only a screenshot or aggregate table. The receipt should preserve per-row outputs/probabilities when the engine exposes them and enough metadata to reproduce the aggregation.

Before submitting:

```bash
python3 tools/check_claims.py .
python3 tools/check_public_release.py .
```

## 6. Open a result PR

A result PR should contain:

1. raw receipt(s) under the appropriate versioned results directory;
2. the exact command/procedure used;
3. adapter code if a new public adapter is required;
4. regenerated public result tables/assets, if applicable;
5. a note describing whether the benchmark was used during model/prompt/threshold development.

If the benchmark influenced model selection, tuning, calibration or thresholds, say so. That result may still be useful development evidence, but should not be represented as pristine held-out evidence.

## 7. Optional verified badge

After a result is accepted, model authors may use:

```markdown
[![Evaluated on ReflexBench v1](https://img.shields.io/badge/ReflexBench-v1-2eaadc)](https://github.com/brida-ai/reflexbench)
```

Use the badge to indicate that a result exists in the public ReflexBench record, not as an endorsement or universal quality ranking.

## Questions / pre-release models

For public questions, open a GitHub issue using the **Model / result submission** template.

For a pre-release model where public disclosure is not yet possible, contact Brida through the public contact surface at https://www.brida.ai/ and reference ReflexBench. Private evaluation does not automatically become a public canonical result.
