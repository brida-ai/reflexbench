"""Provider-neutral normalization helpers for System One benchmark adapters."""
from __future__ import annotations

from typing import Any, Mapping


from system_one_contract_v1 import normalize_questions


def answer_summary(answer: Mapping[str, Any]) -> dict[str, Any]:
    kind = str(answer.get("type", "unknown"))
    out: dict[str, Any] = {"type": kind}
    for key in ("choice", "score", "noul", "probability", "confidence"):
        value = answer.get(key)
        if isinstance(value, (str, int, float, bool)):
            out[key] = value
    probs = answer.get("probabilities")
    if isinstance(probs, Mapping):
        out["probabilities"] = {
            str(k): float(v) for k, v in probs.items() if isinstance(v, (int, float))
        }
    return out


def reverse_choice_question(question: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(question)
    if item.get("type") != "choice":
        return item
    criteria = item.get("criteria")
    if isinstance(criteria, Mapping):
        item["criteria"] = {k: criteria[k] for k in reversed(list(criteria))}
    elif isinstance(criteria, list):
        item["criteria"] = list(reversed(criteria))
    else:
        raise ValueError("choice criteria must be mapping or list")
    return item


def average_choice_answers(first: Mapping[str, Any], second: Mapping[str, Any]) -> dict[str, Any]:
    p1 = first.get("probabilities")
    p2 = second.get("probabilities")
    if not isinstance(p1, Mapping) or not isinstance(p2, Mapping):
        raise ValueError("choice ensemble requires native probability mappings")
    labels = set(map(str, p1)) | set(map(str, p2))
    if set(map(str, p1)) != set(map(str, p2)):
        raise ValueError("choice ensemble probability label sets differ")
    probs = {label: (float(p1[label]) + float(p2[label])) / 2.0 for label in sorted(labels)}
    total = sum(probs.values())
    if total <= 0:
        raise ValueError("choice ensemble probability sum is non-positive")
    probs = {k: v / total for k, v in probs.items()}
    choice = max(probs, key=probs.get)
    return {
        "type": "choice",
        "choice": choice,
        "confidence": probs[choice],
        "probabilities": probs,
    }
