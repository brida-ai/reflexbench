# Reflex System One Contract v1

**Status:** frozen ReflexBench v1 provider-neutral request contract.

## Product rule

Reflex v1 does **not** improve an engine by rewriting the task for that engine.

Every admitted engine receives the same semantic request:

```json
{
  "state": {"...": "bounded facts"},
  "questions": {
    "decision": {
      "type": "choice",
      "instructions": "Which supplied outcome best matches the bounded evidence?",
      "criteria": {
        "a": "Meaning of A",
        "b": "Meaning of B"
      }
    }
  }
}
```

`binary` is a product-facing alias and is normalized mechanically to System One `noul` on the wire. State, instructions, criteria, label order and Score levels are otherwise preserved.

The question contract contains no provider/model/prompt/temperature/adapter configuration. Those fields are rejected by the validator.

## Three canonical templates

### Binary / Noul

```json
{
  "type": "binary",
  "instructions": "Does the bounded evidence satisfy the stated condition?",
  "criteria": {
    "true": "Evidence sufficient for true.",
    "false": "Evidence sufficient for false."
  }
}
```

Use deterministic code first for facts that can be computed exactly. Binary is for the remaining bounded semantic judgment.

### Choice

```json
{
  "type": "choice",
  "instructions": "Which supplied outcome best matches the bounded evidence?",
  "criteria": {
    "routine": "Low semantic risk.",
    "focused": "Targeted review is warranted.",
    "specialist": "Protected or high-impact review is warranted."
  }
}
```

Choice labels and criteria are explicit. Reflex does not rename, chunk, reorder or paraphrase them per engine in the canonical lane.

### Score

```json
{
  "type": "score",
  "instructions": "Rate the bounded evidence against these ordered levels.",
  "criteria": [
    "Lowest level",
    "Low level",
    "Middle level",
    "High level",
    "Highest level"
  ]
}
```

The ordered rubric belongs to the workflow contract. Thresholds that turn the score into operational branches belong to deterministic policy, not the model prompt.

## What Reflex adds

For v1 the core comparison is deliberately small:

```text
same state + same questions
        |
        v
      engine
        |
        +--> raw semantic branch
        |
        +--> deterministic Reflex policy --> operational branch / review
```

Optional mechanisms such as order averaging, engine-specific calibration or selective review are separate ablations. They are never silently folded into the base engine score and are admitted only when paired evidence shows value.

**Confidence/review thresholds are workflow-owned policy, not engine-global calibration.** Core v1 has no universal Jev/Choice threshold. A future engine-global threshold proposal is a separate experimental layer and must beat the raw engine on disjoint evidence while preserving declared compatibility lanes before it can be admitted.

## What stays outside the model

- arithmetic, dates and exact comparisons;
- authorization and permissions;
- deterministic preconditions/guards;
- action execution;
- branch thresholds and review policy;
- billing/customer identity;
- provider routing.

The engine supplies probabilistic evidence. The application remains the authority.

## Benchmark invariant

A `raw engine -> Reflex` uplift claim must reuse the **same engine response on the same case** whenever the layer being measured is post-processing/policy. If a layer makes another inference call (for example order stabilization), the extra call and latency must be reported explicitly.

No model-specific prompt or semantic adapter may be called "Reflex uplift".
