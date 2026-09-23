#!/usr/bin/env python3
"""Evaluate the frozen Reflex Core-v1 workflow gate from same-response engine evidence.

The procedure and case pack must predate engine inference. This evaluator does not tune
thresholds, rewrite expected branches, or rerun the engine. Gate failure is evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from harness_value import bootstrap_policy_delta, policy_value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def fallback_branch(recipe: Mapping[str, Any]) -> str | None:
    policy = recipe["declarative_policy"]
    if policy["type"] in {"binary", "choice"}:
        value = policy.get("uncertainBranch")
        return str(value) if value is not None else None
    return None


def slice_summary(rows: list[dict[str, Any]], fallback_by_workflow: Mapping[str, str | None]) -> dict[str, Any]:
    n = len(rows)
    raw_correct = sum(bool(row["semantic_correct"]) for row in rows)
    core_correct = sum(bool(row["operational_correct"]) for row in rows)
    rescues = sum((not row["semantic_correct"]) and row["operational_correct"] for row in rows)
    harms = sum(row["semantic_correct"] and (not row["operational_correct"]) for row in rows)
    interventions = sum(row["semantic_branch"] != row["operational_branch"] for row in rows)
    reviewed = sum(
        fallback_by_workflow.get(str(row["use_case"])) is not None
        and row["operational_branch"] == fallback_by_workflow[str(row["use_case"])]
        for row in rows
    )
    direct = [
        row for row in rows
        if fallback_by_workflow.get(str(row["use_case"])) is None
        or row["operational_branch"] != fallback_by_workflow[str(row["use_case"])]
    ]
    direct_correct = sum(bool(row["operational_correct"]) for row in direct)
    return {
        "n": n,
        "raw_correct": raw_correct,
        "raw_exact_branch_accuracy": raw_correct / n if n else None,
        "core_correct": core_correct,
        "core_exact_branch_accuracy": core_correct / n if n else None,
        "paired_delta": (core_correct - raw_correct) / n if n else None,
        "rescues": rescues,
        "harms": harms,
        "interventions": interventions,
        "intervention_rate": interventions / n if n else None,
        "review_count": reviewed,
        "review_rate": reviewed / n if n else None,
        "direct_count": len(direct),
        "automation_coverage": len(direct) / n if n else None,
        "direct_action_accuracy": direct_correct / len(direct) if direct else None,
    }


def grouped(rows: list[dict[str, Any]], key: str, fallback_by_workflow: Mapping[str, str | None]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[key])].append(row)
    return {name: slice_summary(group, fallback_by_workflow) for name, group in sorted(groups.items())}


def same_response_invariant(
    procedure: Mapping[str, Any],
    result: Mapping[str, Any],
    completed_rows: int,
) -> dict[str, Any]:
    ablation = result.get("ablation")
    run = result.get("run")
    if not isinstance(ablation, Mapping) or not isinstance(run, Mapping):
        return {"holds": False, "mode": "invalid-result-shape"}

    no_semantic_extra_pass = (
        ablation.get("choice_ensemble") == "none"
        and ablation.get("native_permutations") is None
    )
    http_requests = int(run.get("http_requests", -1))
    retry_policy = procedure.get("evaluation", {}).get("transport_retry_policy")

    if not isinstance(retry_policy, Mapping):
        holds = no_semantic_extra_pass and http_requests == completed_rows
        return {
            "holds": holds,
            "mode": "legacy-no-retry",
            "http_requests": http_requests,
            "result_rows": completed_rows,
            "choice_ensemble": ablation.get("choice_ensemble"),
            "native_permutations": ablation.get("native_permutations"),
            "prompt_rewrite": False,
            "model_specific_semantic_adapter": False,
        }

    expected_retries = int(retry_policy["max_retries"])
    expected_backoff = float(retry_policy["backoff_ms"])
    configured_retries = int(ablation.get("transport_retries", -1))
    configured_backoff = float(ablation.get("transport_retry_backoff_ms", -1.0))
    retry_requests = int(run.get("transport_retry_requests", -1))
    successful_decisions = int(run.get("successful_decisions", -1))
    failed_decisions = int(result.get("completion", {}).get("failed", 0))
    request_accounting = (
        retry_requests >= 0
        and http_requests == completed_rows + failed_decisions + retry_requests
    )
    config_matches = (
        configured_retries == expected_retries
        and abs(configured_backoff - expected_backoff) < 1e-9
    )
    holds = (
        no_semantic_extra_pass
        and config_matches
        and successful_decisions == completed_rows
        and request_accounting
        and retry_requests <= expected_retries * (completed_rows + failed_decisions)
    )
    return {
        "holds": holds,
        "mode": "predeclared-transport-retry",
        "http_requests": http_requests,
        "result_rows": completed_rows,
        "successful_decisions": successful_decisions,
        "failed_decisions": failed_decisions,
        "transport_retry_requests": retry_requests,
        "transport_retry_policy_match": config_matches,
        "request_accounting_match": request_accounting,
        "choice_ensemble": ablation.get("choice_ensemble"),
        "native_permutations": ablation.get("native_permutations"),
        "prompt_rewrite": False,
        "model_specific_semantic_adapter": False,
    }


def evaluate(
    procedure: dict[str, Any],
    case_manifest: dict[str, Any],
    cases_path: Path,
    result: dict[str, Any],
    registry: Path,
) -> dict[str, Any]:
    case_rows = load_jsonl(cases_path)
    if sha256(cases_path) != case_manifest["case_pack_sha256"]:
        raise ValueError("case pack SHA does not match frozen case manifest")
    if len(case_rows) != int(case_manifest["rows"]):
        raise ValueError("case pack row count mismatch")
    if result["corpus"]["sha256"] != case_manifest["case_pack_sha256"]:
        raise ValueError("engine result does not reference frozen case pack")
    if int(result["corpus"]["rows"]) != len(case_rows):
        raise ValueError("engine result corpus count mismatch")

    selected = {item["id"] for item in procedure["selected_workflows"]}
    fallback_by_workflow: dict[str, str | None] = {}
    for workflow in selected:
        recipe = json.loads(
            (registry / "examples" / "use-cases" / workflow / "custom-reflex.json").read_text()
        )
        fallback_by_workflow[workflow] = fallback_branch(recipe)

    result_rows = result.get("rows")
    failures = result.get("failures")
    if not isinstance(result_rows, list):
        raise ValueError("engine result rows missing")
    if not isinstance(failures, list):
        raise ValueError("engine result failures missing")
    if len(result_rows) + len(failures) != len(case_rows):
        raise ValueError("completed + failed rows do not cover frozen case pack")
    by_id = {str(row["id"]): row for row in case_rows}
    if len(by_id) != len(case_rows):
        raise ValueError("case pack ids are not unique")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for row in result_rows:
        case_id = str(row["case_id"])
        if case_id not in by_id:
            raise ValueError(f"result contains unknown case {case_id!r}")
        if case_id in seen:
            raise ValueError(f"duplicate result case {case_id!r}")
        seen.add(case_id)
        case = by_id[case_id]
        if str(row["expected_branch"]) != str(case["expectedBranch"]):
            raise ValueError(f"expected branch drift for {case_id}")
        if str(row["use_case"]) != str(case["useCase"]):
            raise ValueError(f"workflow drift for {case_id}")
        if str(row.get("language")) != str(case["language"]):
            raise ValueError(f"language metadata drift for {case_id}")
        if str(row.get("difficulty")) != str(case["caseClass"]):
            raise ValueError(f"caseClass metadata drift for {case_id}")
        normalized.append(row)
    failed_ids: set[str] = set()
    for failure in failures:
        case_id = str(failure["case_id"])
        if case_id not in by_id:
            raise ValueError(f"failure contains unknown case {case_id!r}")
        if case_id in seen or case_id in failed_ids:
            raise ValueError(f"duplicate completed/failed case {case_id!r}")
        failed_ids.add(case_id)
    if seen | failed_ids != set(by_id):
        raise ValueError("completed + failed evidence does not cover every frozen case")

    completion = result["completion"]
    same_response_info = same_response_invariant(procedure, result, len(normalized))
    same_response = bool(same_response_info["holds"])
    overall = slice_summary(normalized, fallback_by_workflow)
    bootstrap = bootstrap_policy_delta(normalized, iterations=20_000, seed=20260922)
    rules = procedure["predeclared_gate"]
    checks = {
        "completion_rate": float(completion["rate"]) == float(rules["completion_rate"]),
        "core_exact_branch_delta_positive": (
            overall["paired_delta"] is not None and overall["paired_delta"] > 0
        ) if rules["core_exact_branch_delta_must_be_positive"] else True,
        "bootstrap_ci95_lower_nonnegative": (
            float(bootstrap["ci95_low"]) >= 0
        ) if rules["bootstrap_ci95_lower_bound_must_be_nonnegative"] else True,
        "harms_not_exceed_rescues": (
            int(overall["harms"]) <= int(overall["rescues"])
        ) if rules["harms_must_not_exceed_rescues"] else True,
        "same_response_invariant": same_response if rules["same_response_invariant_must_hold"] else True,
    }
    return {
        "schema": "brida.reflexbench.core-v1-workflow-gate-result/v1alpha1",
        "claim_class": "authoritative-first-blind-product-gate",
        "candidate": "Reflex Core v1 on TypeSafe Jev",
        "procedure": {
            "status": procedure["status"],
            "selected_workflows": [item["id"] for item in procedure["selected_workflows"]],
        },
        "case_pack": {
            "sha256": case_manifest["case_pack_sha256"],
            "rows": case_manifest["rows"],
            "paired_scenarios": case_manifest["paired_scenarios"],
            "model_outputs_observed_before_freeze": case_manifest["model_outputs_observed_before_freeze"],
        },
        "engine": result["engine"],
        "same_response_invariant": same_response_info,
        "completion": completion,
        "overall": overall,
        "bootstrap_delta": bootstrap,
        "by_workflow": grouped(normalized, "use_case", fallback_by_workflow),
        "by_policy_type": grouped(normalized, "policy_type", fallback_by_workflow),
        "by_language": grouped(normalized, "language", fallback_by_workflow),
        "by_case_class": grouped(normalized, "difficulty", fallback_by_workflow),
        "gate_checks": checks,
        "gate_pass": all(checks.values()),
        "boundary": (
            "First blind synthetic workflow gate for frozen Core v1. Passing proves paired product-policy "
            "value on this pre-inference case pack only; it is not model SOTA, real-customer evidence, or "
            "production-route authorization. Failure remains authoritative and may not be tuned away under "
            "this gate identity."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procedure", required=True, type=Path)
    ap.add_argument("--case-manifest", required=True, type=Path)
    ap.add_argument("--cases", required=True, type=Path)
    ap.add_argument("--result", required=True, type=Path)
    ap.add_argument("--registry", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    payload = evaluate(
        json.loads(args.procedure.read_text()),
        json.loads(args.case_manifest.read_text()),
        args.cases,
        json.loads(args.result.read_text()),
        args.registry,
    )
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "completion": payload["completion"],
        "overall": payload["overall"],
        "bootstrap_delta": payload["bootstrap_delta"],
        "gate_checks": payload["gate_checks"],
        "gate_pass": payload["gate_pass"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
