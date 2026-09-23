# Versioning

ReflexBench versions benchmark definitions, not marketing snapshots.

- **v1.0.0** freezes the initial public task/corpus/scoring contract.
- **v1.x** may add new engine runs, new hardware measurements, documentation fixes or additional receipts against the unchanged v1 benchmark.
- **v2.0.0** is required when task cases, expected outputs, scoring semantics, primary selection rules or benchmark composition change in a way that breaks direct comparability.

Historical benchmark versions stay available. Newer results do not rewrite old receipts.

A case that has been inspected/tuned against remains development evidence even if a later ReflexBench version reuses it. A new pristine gate requires new uninspected cases.
