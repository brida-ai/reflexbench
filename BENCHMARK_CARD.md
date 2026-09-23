# Benchmark card — ReflexBench v1.0.0

## Scope

ReflexBench evaluates System One / typed decision models that map bounded state plus typed questions to probability distributions. v1 covers Choice, Score and Noul/Binary primitives, operational policy value, calibration, option-order behavior, multilingual consistency and capability boundaries.

## Intended use

- compare decision engines on the same frozen semantic contract;
- regression-test a pinned engine version;
- measure whether deterministic workflow policy adds value to the same model response;
- study calibration/selective review/order sensitivity as separate axes;
- document provider failures and deployment boundaries.

## Not intended for

- ranking chat/generative quality;
- claiming one universal "best model" from a composite score;
- treating synthetic capability lanes as semantic intelligence tests;
- converting local-vs-hosted p50 into a normalized speed ranking;
- tuning on a held-out cohort and continuing to call it untouched;
- authorizing automatic protected actions.

## v1 evidence families

1. Brida-authored public Reflex product fixtures.
2. Blind Brida-authored workflow gates, frozen before inference.
3. Public external hard-cohort results, treated as development evidence after inspection.
4. Multilingual public-dataset development lanes with manifests/provenance.
5. Synthetic Choice cardinality/capability lane.

## Metrics

Accuracy, macro-F1 where appropriate, NLL, Brier, ECE, Score error, completion/failure rate, option-order flip rate, EN/ES paired consistency, selective risk/coverage, paired rescues/harms and paired bootstrap intervals.

## Contamination rule

Once an item influences architecture, prompt/schema design, threshold/calibration fitting, model training or candidate selection, it is development evidence for that lineage and cannot later be called pristine held-out evidence.

## Failure policy

Failures are retained. Provider/transport failure, unsupported schema/cardinality and wrong semantic prediction are different outcomes and must not be collapsed into one number.

## Latency policy

Every latency claim carries its deployment boundary. Hosted-provider latency and local GPU latency are not directly ranked unless hardware/network are normalized by a separate protocol.

## Governance

The benchmark contract is frozen by version. Task/scoring changes to v1 require a new major benchmark version; engine-result additions against identical frozen v1 may be added under v1.x.
