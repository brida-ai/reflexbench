# Integrating ReflexBench into a benchmark catalog

ReflexBench exposes stable machine-readable discovery and leaderboard surfaces so model labs, benchmark aggregators and evaluation platforms do not need to scrape prose.

## Discovery

- `benchmark.json` — benchmark identity, category, version and canonical integration links.
- `leaderboards/v1.json` — canonical v1 raw leaderboard plus explicitly separate supplemental harness/policy lanes.
- `schemas/result-submission-v1.schema.json` — third-party result envelope.
- `CITATION.cff` — citation metadata.

## Display rules

ReflexBench intentionally distinguishes three result types:

1. **raw engine** — canonical same-corpus model/engine quality;
2. **model + Reflex harness** — explicit harness/ensemble ablation;
3. **same-response policy** — downstream deterministic policy over an unchanged model response.

Do not relabel lanes 2 or 3 as raw model quality. Do not combine hosted/local latency into a hardware-normalized ranking unless you rerun under a normalized environment.

## Recommended catalog fields

At minimum ingest:

- benchmark version and lane;
- corpus row count / hash where supplied;
- engine owner/name/revision;
- semantic accuracy;
- completion rate;
- deployment boundary;
- receipt path/source;
- benchmark-used-for-development disclosure.

## Labs and bulk results

See [`FOR_LABS.md`](../FOR_LABS.md) and [`SUBMIT_A_MODEL.md`](../SUBMIT_A_MODEL.md). Bulk submissions should use the same public result schema and remain reproducible without privileged Brida infrastructure.
