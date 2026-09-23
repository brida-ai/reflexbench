"""Provider-neutral metrics for ReflexBench research results.

The definitions in this file are intentionally explicit. In particular, multiclass
Brier is the *sum* of squared probability error across classes per decision, then
averaged across decisions. This avoids silently comparing against libraries that
use a binary or class-normalized convention.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

_EPS = 1e-12


def _normalize(values: Sequence[float]) -> list[float]:
    clean = [float(v) if math.isfinite(float(v)) and float(v) >= 0 else 0.0 for v in values]
    total = sum(clean)
    if not clean:
        raise ValueError("probability vector must not be empty")
    if total <= 0:
        return [1.0 / len(clean)] * len(clean)
    return [v / total for v in clean]


def _argmax(values: Sequence[float]) -> int:
    if not values:
        raise ValueError("values must not be empty")
    return max(range(len(values)), key=lambda i: values[i])


def decision_record(probabilities: Sequence[float], gold_index: int, **metadata: Any) -> dict[str, Any]:
    probs = _normalize(probabilities)
    if gold_index < 0 or gold_index >= len(probs):
        raise ValueError("gold_index outside probability vector")
    predicted = _argmax(probs)
    return {
        "probabilities": probs,
        "gold_index": int(gold_index),
        "predicted_index": predicted,
        "correct": predicted == gold_index,
        "confidence": max(probs),
        **metadata,
    }


def accuracy(rows: Sequence[Mapping[str, Any]]) -> float | None:
    if not rows:
        return None
    return sum(bool(r["correct"]) for r in rows) / len(rows)


def macro_f1(rows: Sequence[Mapping[str, Any]]) -> float | None:
    if not rows:
        return None
    labels = sorted({int(r["gold_index"]) for r in rows} | {int(r["predicted_index"]) for r in rows})
    scores: list[float] = []
    for label in labels:
        tp = sum(int(r["gold_index"]) == label and int(r["predicted_index"]) == label for r in rows)
        fp = sum(int(r["gold_index"]) != label and int(r["predicted_index"]) == label for r in rows)
        fn = sum(int(r["gold_index"]) == label and int(r["predicted_index"]) != label for r in rows)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(scores) / len(scores) if scores else None


def brier_hard(rows: Sequence[Mapping[str, Any]]) -> float | None:
    """Mean multiclass Brier: sum_k (p_k - y_k)^2 per decision."""
    if not rows:
        return None
    total = 0.0
    for row in rows:
        probs = _normalize(row["probabilities"])
        gold = int(row["gold_index"])
        total += sum((p - (1.0 if i == gold else 0.0)) ** 2 for i, p in enumerate(probs))
    return total / len(rows)


def nll(rows: Sequence[Mapping[str, Any]]) -> float | None:
    if not rows:
        return None
    return -sum(math.log(max(_EPS, _normalize(r["probabilities"])[int(r["gold_index"])])) for r in rows) / len(rows)


def ece(rows: Sequence[Mapping[str, Any]], bins: int = 15) -> float | None:
    if not rows:
        return None
    if bins <= 0:
        raise ValueError("bins must be positive")
    total = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        selected = [r for r in rows if float(r["confidence"]) > lo and float(r["confidence"]) <= hi]
        if not selected:
            continue
        mean_conf = sum(float(r["confidence"]) for r in selected) / len(selected)
        mean_acc = sum(bool(r["correct"]) for r in selected) / len(selected)
        total += len(selected) / len(rows) * abs(mean_conf - mean_acc)
    return total


def _score_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [r for r in rows if str(r.get("question_type", "")).lower() == "score" or r.get("score_error") is not None]


def score_mae(rows: Sequence[Mapping[str, Any]]) -> float | None:
    values = [float(r["score_error"]) for r in _score_rows(rows) if r.get("score_error") is not None]
    return sum(values) / len(values) if values else None


def score_argmax_exact_accuracy(rows: Sequence[Mapping[str, Any]]) -> float | None:
    selected = _score_rows(rows)
    return accuracy(selected) if selected else None


def score_argmax_within_one_accuracy(rows: Sequence[Mapping[str, Any]]) -> float | None:
    selected = _score_rows(rows)
    if not selected:
        return None
    return sum(abs(int(r["predicted_index"]) - int(r["gold_index"])) <= 1 for r in selected) / len(selected)


def score_argmax_mae(rows: Sequence[Mapping[str, Any]]) -> float | None:
    selected = _score_rows(rows)
    if not selected:
        return None
    return sum(abs(int(r["predicted_index"]) - int(r["gold_index"])) for r in selected) / len(selected)


def selective_accuracy(rows: Sequence[Mapping[str, Any]], coverages: Iterable[float] = (1.0, .9, .75, .5, .25)) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda r: float(r["confidence"]), reverse=True)
    out: list[dict[str, Any]] = []
    for coverage in coverages:
        c = float(coverage)
        if not 0 < c <= 1:
            raise ValueError("coverage must be in (0, 1]")
        if not ordered:
            out.append({"coverage": c, "n": 0, "accuracy": None, "risk": None})
            continue
        n = max(1, math.ceil(len(ordered) * c))
        actual = ordered[:n]
        acc = accuracy(actual)
        out.append({"coverage": n / len(ordered), "requested_coverage": c, "n": n, "accuracy": acc, "risk": None if acc is None else 1.0 - acc})
    return out


def _label_space_status(rows: Sequence[Mapping[str, Any]]) -> tuple[bool, int | None, str | None]:
    present = [r.get("labels") for r in rows if r.get("labels") is not None]
    if not present:
        return True, None, None
    if len(present) != len(rows):
        return False, None, "mixed presence of label-space metadata"
    spaces = {tuple(str(x) for x in labels) for labels in present}
    if len(spaces) == 1:
        return True, 1, None
    return False, len(spaces), "aggregate class indices refer to heterogeneous label spaces"


def summarize(rows: Sequence[Mapping[str, Any]], *, bins: int = 15) -> dict[str, Any]:
    f1_valid, label_space_count, f1_reason = _label_space_status(rows)
    return {
        "n": len(rows),
        "accuracy": accuracy(rows),
        "macro_f1": macro_f1(rows) if f1_valid else None,
        "macro_f1_valid": f1_valid,
        "macro_f1_unavailable_reason": f1_reason,
        "label_space_count": label_space_count,
        "brier_hard_sum_classes": brier_hard(rows),
        "nll": nll(rows),
        "ece": ece(rows, bins=bins),
        "score_rows": len(_score_rows(rows)),
        "score_mae": score_mae(rows),
        "score_argmax_exact_accuracy": score_argmax_exact_accuracy(rows),
        "score_argmax_within_one_accuracy": score_argmax_within_one_accuracy(rows),
        "score_argmax_mae": score_argmax_mae(rows),
        "selective_accuracy": selective_accuracy(rows),
        "gold_label_counts": dict(sorted(Counter(int(r["gold_index"]) for r in rows).items())),
    }
