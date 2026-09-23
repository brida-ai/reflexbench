# Contributing

Contributions are welcome for reproducible engine adapters, new results on frozen benchmark versions, metrics, documentation and proposed future benchmark versions.

For a new v1 engine result:

1. pin the exact engine/model revision;
2. use the frozen v1 corpus and question semantics;
3. retain failures and retries;
4. include hardware/deployment boundary;
5. do not tune on the benchmark and call it held-out;
6. include machine-readable receipt(s) and the command/procedure used.

Changes to v1 tasks/scoring are not accepted as silent fixes; propose v2 instead.

For the full model/result submission workflow, see [SUBMIT_A_MODEL.md](SUBMIT_A_MODEL.md).
