"""Provider-neutral policy helpers for the private ReflexBench research harness.

No product authority lives here. This module mirrors the declarative policy shapes
used by public Custom Reflex examples so benchmark runners can report semantic
engine capability separately from operational threshold behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class PolicyDecision:
    semantic_branch: str
    operational_branch: str
    selected_probability: float | None


def _probabilities(answer: Mapping[str, Any]) -> Mapping[str, float]:
    raw = answer.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, float] = {}
    for key, value in raw.items():
        if isinstance(value, (int, float)):
            out[str(key)] = float(value)
    return out


def _noul_probability(answer: Mapping[str, Any]) -> float:
    for key in ("noul", "probability", "probabilityTrue", "probability_true"):
        value = answer.get(key)
        if isinstance(value, (int, float)):
            return max(0.0, min(1.0, float(value)))
    probs = _probabilities(answer)
    if "true" in probs:
        return max(0.0, min(1.0, probs["true"]))
    raise ValueError("Laya binary/noul answer has no true probability")


def _choice(answer: Mapping[str, Any]) -> tuple[str, float | None]:
    selected = answer.get("choice")
    if not isinstance(selected, str) or not selected:
        probs = _probabilities(answer)
        if not probs:
            raise ValueError("Laya choice answer has no selected choice/probabilities")
        selected = max(probs, key=probs.get)
    probs = _probabilities(answer)
    probability = probs.get(selected)
    return selected, probability


def _score(answer: Mapping[str, Any]) -> float:
    value = answer.get("score")
    if not isinstance(value, (int, float)):
        raise ValueError("Laya score answer has no numeric score")
    return float(value)


def apply_declarative_policy(
    policy: Mapping[str, Any],
    answer: Mapping[str, Any],
) -> PolicyDecision:
    """Return both threshold-free semantic branch and actual operational branch."""

    policy_type = policy.get("type")

    if policy_type == "choice":
        selected, probability = _choice(answer)
        branches = policy.get("branches")
        if not isinstance(branches, Mapping) or selected not in branches:
            raise ValueError(f"Choice {selected!r} is not mapped by policy")
        semantic = str(branches[selected])
        minimum = float(policy.get("minimumSelectedProbability", 0.0))
        operational = semantic
        if probability is None or probability < minimum:
            operational = str(policy["uncertainBranch"])
        return PolicyDecision(semantic, operational, probability)

    if policy_type == "binary":
        p_true = _noul_probability(answer)
        semantic = str(policy["trueBranch"] if p_true >= 0.5 else policy["falseBranch"])
        true_at = float(policy["trueWhenProbabilityAtLeast"])
        false_at = float(policy["falseWhenProbabilityAtMost"])
        if p_true >= true_at:
            operational = str(policy["trueBranch"])
        elif p_true <= false_at:
            operational = str(policy["falseBranch"])
        else:
            operational = str(policy["uncertainBranch"])
        return PolicyDecision(semantic, operational, max(p_true, 1.0 - p_true))

    if policy_type == "score":
        score = _score(answer)
        thresholds = policy.get("thresholds")
        if not isinstance(thresholds, list):
            raise ValueError("Score policy thresholds must be a list")
        branch = str(policy["belowBranch"])
        for threshold in sorted(thresholds, key=lambda item: float(item["atLeast"]), reverse=True):
            if score >= float(threshold["atLeast"]):
                branch = str(threshold["branch"])
                break
        return PolicyDecision(branch, branch, None)

    raise ValueError(f"Unsupported declarative policy type: {policy_type!r}")
