"""Paired statistical comparisons for ReflexBench.

These helpers intentionally operate on aligned per-case outputs. Independent
resampling would discard the within-case pairing and waste statistical power.
"""

from __future__ import annotations

import math
import random
from typing import Any, Mapping, Sequence


def _index(rows: Sequence[Mapping[str, Any]], *, id_field: str) -> dict[str, Mapping[str, Any]]:
    out: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        value = row.get(id_field)
        if value is None:
            raise ValueError(f"row missing {id_field}")
        case_id = str(value)
        if case_id in out:
            raise ValueError(f"duplicate case id: {case_id}")
        out[case_id] = row
    return out


def _aligned(
    rows_a: Sequence[Mapping[str, Any]],
    rows_b: Sequence[Mapping[str, Any]],
    *,
    id_field: str,
    correct_field: str,
) -> list[tuple[str, bool, bool]]:
    a = _index(rows_a, id_field=id_field)
    b = _index(rows_b, id_field=id_field)
    if set(a) != set(b):
        only_a = sorted(set(a) - set(b))
        only_b = sorted(set(b) - set(a))
        raise ValueError(
            "paired comparison requires identical case ids; "
            f"only_a={only_a[:5]!r} only_b={only_b[:5]!r}"
        )
    return [
        (
            case_id,
            bool(a[case_id][correct_field]),
            bool(b[case_id][correct_field]),
        )
        for case_id in sorted(a)
    ]


def paired_accuracy_delta(
    rows_a: Sequence[Mapping[str, Any]],
    rows_b: Sequence[Mapping[str, Any]],
    *,
    id_field: str = "case_id",
    correct_field: str = "correct",
) -> dict[str, Any]:
    pairs = _aligned(
        rows_a,
        rows_b,
        id_field=id_field,
        correct_field=correct_field,
    )
    if not pairs:
        raise ValueError("paired comparison requires at least one case")
    n = len(pairs)
    a_correct = sum(a for _, a, _ in pairs)
    b_correct = sum(b for _, _, b in pairs)
    a_only = sum(a and not b for _, a, b in pairs)
    b_only = sum(b and not a for _, a, b in pairs)
    both = sum(a and b for _, a, b in pairs)
    neither = n - both - a_only - b_only
    accuracy_a = a_correct / n
    accuracy_b = b_correct / n
    return {
        "n": n,
        "accuracy_a": accuracy_a,
        "accuracy_b": accuracy_b,
        "delta_a_minus_b": accuracy_a - accuracy_b,
        "both_correct": both,
        "a_only_correct": a_only,
        "b_only_correct": b_only,
        "both_wrong": neither,
    }


def _percentile(values: Sequence[float], q: float) -> float:
    if not values:
        raise ValueError("percentile requires values")
    if not 0 <= q <= 1:
        raise ValueError("q must be in [0, 1]")
    xs = sorted(float(v) for v in values)
    position = (len(xs) - 1) * q
    lo = math.floor(position)
    hi = math.ceil(position)
    if lo == hi:
        return xs[lo]
    weight = position - lo
    return xs[lo] * (1.0 - weight) + xs[hi] * weight


def paired_bootstrap_accuracy_delta(
    rows_a: Sequence[Mapping[str, Any]],
    rows_b: Sequence[Mapping[str, Any]],
    *,
    iterations: int = 10_000,
    seed: int = 13,
    id_field: str = "case_id",
    correct_field: str = "correct",
) -> dict[str, Any]:
    if iterations < 100:
        raise ValueError("iterations must be >= 100")
    pairs = _aligned(
        rows_a,
        rows_b,
        id_field=id_field,
        correct_field=correct_field,
    )
    if not pairs:
        raise ValueError("paired comparison requires at least one case")

    base = paired_accuracy_delta(
        rows_a,
        rows_b,
        id_field=id_field,
        correct_field=correct_field,
    )
    rng = random.Random(seed)
    n = len(pairs)
    deltas: list[float] = []
    for _ in range(iterations):
        sum_a = 0
        sum_b = 0
        for _ in range(n):
            _, a, b = pairs[rng.randrange(n)]
            sum_a += int(a)
            sum_b += int(b)
        deltas.append((sum_a - sum_b) / n)

    return {
        "n": n,
        "iterations": iterations,
        "seed": seed,
        "point_delta_a_minus_b": base["delta_a_minus_b"],
        "ci95_low": _percentile(deltas, 0.025),
        "ci95_high": _percentile(deltas, 0.975),
        "bootstrap_mean_delta": sum(deltas) / len(deltas),
        "a_only_correct": base["a_only_correct"],
        "b_only_correct": base["b_only_correct"],
    }
