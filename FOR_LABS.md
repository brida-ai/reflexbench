# ReflexBench for model labs and evaluation platforms

ReflexBench is designed to be a low-friction public evaluation target for System One models, typed decision engines and compatible hosted APIs.

## What a lab gets

- a frozen, versioned benchmark contract instead of a moving leaderboard;
- machine-readable task/result formats;
- probability-aware metrics, not only top-1 accuracy;
- completion/failure accounting;
- multilingual, option-order and cardinality evidence;
- explicit hosted-vs-local deployment boundaries;
- an optional Reflex harness ablation that is kept separate from raw model quality;
- public receipts that can be independently inspected and cited.

## Minimal integration contract

1. Pin the benchmark tag/version.
2. Map Binary/Noul, Choice and Score to your engine without changing task semantics.
3. Run the frozen lane and retain failures/retries.
4. Publish the raw receipt.
5. Fill `templates/result-submission-v1.json`.
6. Validate it locally:

```bash
python3 tools/validate_submission.py path/to/result-submission.json
```

7. Open a result submission issue/PR.

The JSON Schema is published at `schemas/result-submission-v1.schema.json` for CI systems that already use a standards-based validator.

## Recommended public result identity

A canonical result should be addressable as:

```text
benchmark version + lane + corpus SHA
+ engine owner/name/revision
+ adapter revision
+ deployment boundary
+ raw receipt(s)
```

Do not submit an ambiguous API alias as model identity.

## Raw model vs model + harness

ReflexBench treats these as separate experimental claims:

- **Raw engine lane:** the engine is evaluated directly under the frozen task contract.
- **Reflex harness lane:** the same engine is evaluated with an explicitly declared deterministic/ensemble policy.
- **Same-response policy lane:** where possible, the model response itself is frozen and only downstream policy changes.

An aggregator may display these next to one another, but should not silently relabel a model+harness result as raw model quality.

## Benchmark contamination

If ReflexBench influenced model training, prompt development, model selection, calibration or thresholds, set `benchmark_used_for_development: true` and describe it. The result can still be useful, but it is development evidence rather than pristine held-out evaluation.

## Partnership / bulk evaluation

Evaluation platforms and labs can contribute adapters, bulk result snapshots or co-published analysis using exactly the same public evidence contract. Public submissions should remain reproducible without privileged Brida infrastructure.
