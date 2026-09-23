# Web search -> bounded evidence -> Reflex

Search can improve a decision model when the original state is missing current or external facts. The correct architecture is **not** to hide browsing inside Reflex.

```text
user/event
 -> search/retrieval tool
 -> deterministic URL/domain/freshness filters
 -> bounded evidence object
 -> one or more typed Choice / Score / Binary questions
 -> probability result
 -> deterministic policy / human review
 -> authorized action
```

## Example: research claim verification

1. Query a search provider for evidence relevant to a claim.
2. Keep source URL, publication date, publisher and a bounded snippet/summary.
3. Reject stale/disallowed sources deterministically before AI judgment.
4. Ask Reflex a focused question such as:

```json
{
  "state": {
    "claim": "...",
    "evidence": [
      {"source": "publisher", "publishedAt": "...", "summary": "..."}
    ]
  },
  "questions": {
    "support": {
      "type": "binary",
      "instructions": "Does the supplied evidence directly support the claim?"
    },
    "relevance": {
      "type": "score",
      "instructions": "Rate how directly the evidence addresses the claim.",
      "criteria": ["unrelated", "weak", "partial", "direct", "decisive"]
    }
  }
}
```

5. Application code decides whether to continue, search again, request human review, or use the evidence downstream.

## Benchmarking search augmentation

Do not compare `no search` vs `search` and call the delta a model improvement. Report the search provider/query construction, retrieval timestamp, number of sources, deterministic provenance/freshness filters, decision-engine revision, same downstream question contract, accuracy/calibration with and without evidence, and added latency/cost/failure rate.

The public `brida-ai/reflex` registry already includes `retrieval-relevance-gate` and `research-claim-verification` patterns. Search/retrieval remains upstream; Reflex remains the bounded decision layer.
