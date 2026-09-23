"""Quantify what Reflex policy/harness layers add to an engine's raw semantic decision.

This module deliberately avoids calling every intervention an improvement. It separates
rescues, harms and neutral interventions on paired rows so a policy can only claim a
positive net accuracy delta when rescues exceed harms on the evaluated corpus.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence


def policy_value(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("policy_value requires rows")
    n = len(rows)
    intervened = [r for r in rows if r["operational_branch"] != r["semantic_branch"]]
    preserved = [r for r in rows if r["operational_branch"] == r["semantic_branch"]]
    rescues = sum((not bool(r["semantic_correct"])) and bool(r["operational_correct"]) for r in rows)
    harms = sum(bool(r["semantic_correct"]) and (not bool(r["operational_correct"])) for r in rows)
    both_correct = sum(bool(r["semantic_correct"]) and bool(r["operational_correct"]) for r in rows)
    both_wrong = sum((not bool(r["semantic_correct"])) and (not bool(r["operational_correct"])) for r in rows)
    semantic_accuracy = sum(bool(r["semantic_correct"]) for r in rows) / n
    operational_accuracy = sum(bool(r["operational_correct"]) for r in rows) / n

    def acc(group: Sequence[Mapping[str, Any]], field: str) -> float | None:
        return sum(bool(r[field]) for r in group) / len(group) if group else None

    return {
        "n": n,
        "semantic_accuracy": semantic_accuracy,
        "operational_accuracy": operational_accuracy,
        "net_accuracy_delta": operational_accuracy - semantic_accuracy,
        "rescues": rescues,
        "harms": harms,
        "net_rescues_minus_harms": rescues - harms,
        "both_correct": both_correct,
        "both_wrong": both_wrong,
        "interventions": len(intervened),
        "intervention_rate": len(intervened) / n,
        "preserved": len(preserved),
        "preserved_rate": len(preserved) / n,
        "operational_accuracy_when_intervened": acc(intervened, "operational_correct"),
        "semantic_accuracy_when_intervened": acc(intervened, "semantic_correct"),
        "accuracy_when_preserved": acc(preserved, "semantic_correct"),
    }


def paired_layer_value(
    rows_a: Sequence[Mapping[str, Any]],
    rows_b: Sequence[Mapping[str, Any]],
    *,
    id_fields: tuple[str, ...] = ("use_case", "case_id"),
) -> dict[str, Any]:
    """Compare two harness variants on exactly the same rows.

    A positive semantic/operational delta means variant B is more accurate than A.
    Branch flip counts expose changes hidden by equal aggregate accuracy.
    """
    def key(row: Mapping[str, Any]) -> tuple[str, ...]:
        return tuple(str(row[f]) for f in id_fields)

    a = {key(r): r for r in rows_a}
    b = {key(r): r for r in rows_b}
    if len(a) != len(rows_a) or len(b) != len(rows_b):
        raise ValueError("duplicate row identities")
    if set(a) != set(b):
        raise ValueError("paired layer comparison requires identical row identities")
    keys = sorted(a)
    n = len(keys)
    if not n:
        raise ValueError("paired layer comparison requires rows")

    sem_a = sum(bool(a[k]["semantic_correct"]) for k in keys) / n
    sem_b = sum(bool(b[k]["semantic_correct"]) for k in keys) / n
    op_a = sum(bool(a[k]["operational_correct"]) for k in keys) / n
    op_b = sum(bool(b[k]["operational_correct"]) for k in keys) / n
    return {
        "n": n,
        "semantic_accuracy_a": sem_a,
        "semantic_accuracy_b": sem_b,
        "semantic_delta_b_minus_a": sem_b - sem_a,
        "operational_accuracy_a": op_a,
        "operational_accuracy_b": op_b,
        "operational_delta_b_minus_a": op_b - op_a,
        "semantic_branch_flips": sum(a[k]["semantic_branch"] != b[k]["semantic_branch"] for k in keys),
        "operational_branch_flips": sum(a[k]["operational_branch"] != b[k]["operational_branch"] for k in keys),
        "b_semantic_rescues": sum((not bool(a[k]["semantic_correct"])) and bool(b[k]["semantic_correct"]) for k in keys),
        "b_semantic_harms": sum(bool(a[k]["semantic_correct"]) and (not bool(b[k]["semantic_correct"])) for k in keys),
        "b_operational_rescues": sum((not bool(a[k]["operational_correct"])) and bool(b[k]["operational_correct"]) for k in keys),
        "b_operational_harms": sum(bool(a[k]["operational_correct"]) and (not bool(b[k]["operational_correct"])) for k in keys),
    }


def bootstrap_policy_delta(
    rows: Sequence[Mapping[str, Any]],
    *,
    iterations: int = 20_000,
    seed: int = 20260921,
) -> dict[str, Any]:
    """Paired bootstrap CI for operational minus semantic exact-branch accuracy."""
    import random
    from paired_stats import _percentile
    if not rows:
        raise ValueError("bootstrap_policy_delta requires rows")
    if iterations < 100:
        raise ValueError("iterations must be >= 100")
    diffs = [int(bool(r["operational_correct"])) - int(bool(r["semantic_correct"])) for r in rows]
    rng = random.Random(seed)
    n = len(diffs)
    samples = [sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(iterations)]
    return {
        "n": n,
        "iterations": iterations,
        "seed": seed,
        "point_delta": sum(diffs) / n,
        "ci95_low": _percentile(samples, .025),
        "ci95_high": _percentile(samples, .975),
        "bootstrap_mean_delta": sum(samples) / len(samples),
    }
