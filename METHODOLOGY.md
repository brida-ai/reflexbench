# Methodology

## 1. Freeze before inference

Every confirmatory run starts from an immutable case corpus and manifest containing hashes, selection rule, scorer version and relevant registry/model identities. Retry policy must be declared before the run.

## 2. Provider-neutral semantics

The base System One contract is `state + questions`. Choice criteria/order, Score levels and Noul/Binary semantics are frozen. Model-specific prompt rewrites or semantic adapters are not counted as Reflex Core uplift.

## 3. Raw engine vs Reflex Core

Core v1 reuses the exact same engine response. Raw semantic branch and deterministic operational branch are scored pairwise. No second model call is allowed for the Core uplift claim. Rescues, harms and interventions are retained per case.

## 4. Experimental layers stay explicit

Order averaging, extra inference, calibration fitting, selective review, context reduction, retrieval/search, fallback/routing and engine-specific adapters are separate ablations. Their extra calls/latency and selection data are reported independently.

## 5. Probabilistic scoring

Where the engine returns probability vectors, ReflexBench reports calibration-sensitive metrics in addition to accuracy. A confidence number is not interpreted as probability of correctness unless measured calibration supports that interpretation.

## 6. Paired uncertainty

When two systems or layers score the same cases, deltas use paired evidence and paired bootstrap confidence intervals. Unpaired vendor-reported tables are context, not Brida head-to-head evidence.

## 7. Multilingual pairing

Parallel EN/ES lanes keep aligned semantic items so language-specific accuracy and cross-language prediction consistency can be measured on the same intent/state.

## 8. Capability vs quality

A 255-way exact-code task answers "can this runtime represent and return this label space?" It does not answer "is this model semantically intelligent at 255-way classification?" Capability and semantic quality are separate axes.

## 9. Search/retrieval

Web search, retrieval and browser actions happen upstream. ReflexBench can evaluate the resulting bounded-evidence decision, but search itself is not smuggled into the System One model. Search-augmented results report retrieval procedure separately from model/harness quality.

## 10. Reproducibility receipts

Result artifacts omit secrets and customer payloads while preserving hashes, model/engine identity, runtime/hardware metadata, normalized prediction evidence, failures, retries and scoring summaries.
