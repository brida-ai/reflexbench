#!/usr/bin/env python3
"""Freeze the next Reflex Core v1 workflow-level gate before case authoring/inference."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from system_one_contract_v1 import validate_recipe

WORKFLOWS = (
    "sales-lead-fit",
    "customer-support-ticket-triage",
    "software-issue-triage",
    "content-quality-gate",
    "semantic-data-consistency",
)
CASE_CLASSES = ("clear", "boundary", "ambiguous")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def operational_branches(policy: dict[str, Any]) -> list[str]:
    kind = str(policy["type"])
    branches: set[str] = set()
    if kind == "binary":
        for key in ("trueBranch", "falseBranch", "uncertainBranch"):
            if policy.get(key): branches.add(str(policy[key]))
    elif kind == "choice":
        branches.update(str(v) for v in policy.get("branches", {}).values())
        if policy.get("uncertainBranch"): branches.add(str(policy["uncertainBranch"]))
    elif kind == "score":
        branches.update(str(x["branch"]) for x in policy.get("thresholds", []))
        if policy.get("belowBranch"): branches.add(str(policy["belowBranch"]))
    else:
        raise ValueError(f"unsupported policy type {kind!r}")
    if not branches:
        raise ValueError(f"policy {kind!r} exposes no operational branches")
    return sorted(branches)


def freeze(
    registry: Path,
    source_revision: str,
    contract: Path,
    *,
    workflows: tuple[str, ...] = WORKFLOWS,
    transport_retries: int = 0,
    transport_retry_backoff_ms: float = 0.0,
    gate_identity: str | None = None,
) -> dict[str, Any]:
    if len(workflows) != 5 or len(set(workflows)) != 5:
        raise ValueError("workflow gate requires exactly five unique workflows")
    if transport_retries < 0:
        raise ValueError("transport_retries must be >= 0")
    if transport_retry_backoff_ms < 0:
        raise ValueError("transport_retry_backoff_ms must be >= 0")
    selected=[]
    for workflow in workflows:
        path=registry/'examples'/'use-cases'/workflow/'custom-reflex.json'
        if not path.exists(): raise ValueError(f"missing workflow recipe {workflow}")
        recipe=json.loads(path.read_text())
        validate_recipe(recipe)
        selected.append({
            "id":workflow,
            "recipe_sha256":sha256(path),
            "policy_type":str(recipe['declarative_policy']['type']),
            "authority_question_id":str(recipe['declarative_policy']['questionId']),
            "question_count":len(recipe['questions']),
            "operational_branches":operational_branches(recipe['declarative_policy']),
            "minimum_cases":30,
            "minimum_cases_per_class":10,
        })
    payload = {
        "schema":"brida.reflexbench.core-v1-workflow-gate-procedure/v1alpha1",
        "status":"frozen-before-case-pack-and-engine-inference",
        "contract":{
            "name":"Reflex System One Contract v1",
            "file":contract.as_posix(),
            "sha256":sha256(contract),
        },
        "recipe_registry":{
            "repository":"brida-ai/reflex",
            "revision":source_revision,
        },
        "selected_workflows":selected,
        "case_pack_rules":{
            "minimum_total_cases":150,
            "case_classes":list(CASE_CLASSES),
            "languages":["en","es"],
            "minimum_cases_per_language_per_workflow":15,
            "required_case_fields":["id","useCase","language","caseClass","evidenceClass","state","expectedBranch","provenance"],
            "forbidden_case_fields":[
                "questions","question","prompt","systemPrompt","model","engine","provider","adapter","temperature",
                "answer","answers","probabilities","confidence","semanticBranch","operationalBranch","selectedProbability",
            ],
            "expected_branch_locked_before_any_engine_inference":True,
            "case_pack_sha_locked_before_any_engine_inference":True,
            "public110_case_reuse_forbidden":True,
            "private_v2_case_reuse_forbidden":True,
            "model_output_guided_case_authoring_forbidden":True,
            "deterministic_facts_rule":"Arithmetic, dates, permissions, exact comparisons and other host-computable facts must be precomputed/represented as facts; cases must test the remaining bounded semantic judgment rather than ask the model to replace deterministic code.",
        },
        "evaluation":{
            "engine_request":"canonical Core v1 state + frozen recipe questions",
            "raw_layer":"semantic branch derived from the authority question response without confidence intervention",
            "core_layer":"same authority-question response passed through the frozen declarative policy",
            "same_response_required":True,
            "extra_model_calls_for_core":0,
            "model_specific_prompt_rewrite_forbidden":True,
            "model_specific_semantic_adapter_forbidden":True,
            "primary_metrics":[
                "raw_exact_branch_accuracy","core_exact_branch_accuracy","paired_delta","rescues","harms","interventions",
                "bootstrap_delta_ci95","automation_coverage","direct_action_accuracy","review_rate",
            ],
            "required_slices":["workflow","policy_type","language","caseClass","evidenceClass"],
        },
        "predeclared_gate":{
            "completion_rate":1.0,
            "core_exact_branch_delta_must_be_positive":True,
            "bootstrap_ci95_lower_bound_must_be_nonnegative":True,
            "harms_must_not_exceed_rescues":True,
            "same_response_invariant_must_hold":True,
            "note":"A failed gate remains authoritative evidence; thresholds/templates/cases may not be changed and rerun under the same gate identity.",
        },
        "publication_boundary":"Internal blind product gate. Passing does not imply model SOTA or authorize public release/production route changes.",
    }
    if gate_identity is not None:
        payload["gate_identity"] = gate_identity
    if transport_retries:
        payload["evaluation"]["transport_retry_policy"] = {
            "max_retries": transport_retries,
            "backoff_ms": float(transport_retry_backoff_ms),
            "retryable_http_statuses": ["429", "500-599"],
            "retryable_connection_errors": True,
            "semantic_client_4xx_retried": False,
            "request_semantics_must_be_identical": True,
            "preserve_retry_ledger": True,
        }
    return payload


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--registry',required=True,type=Path)
    ap.add_argument('--source-revision',required=True)
    ap.add_argument('--contract',type=Path,default=Path('docs/research/reflex/reflexbench/system-one-contract-v1.md'))
    ap.add_argument('--workflow',dest='workflows',action='append')
    ap.add_argument('--transport-retries',type=int,default=0)
    ap.add_argument('--transport-retry-backoff-ms',type=float,default=0.0)
    ap.add_argument('--gate-identity')
    ap.add_argument('--output',required=True,type=Path)
    a=ap.parse_args(); payload=freeze(
        a.registry,a.source_revision,a.contract,
        workflows=tuple(a.workflows) if a.workflows else WORKFLOWS,
        transport_retries=a.transport_retries,
        transport_retry_backoff_ms=a.transport_retry_backoff_ms,
        gate_identity=a.gate_identity,
    )
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':payload['status'],'workflows':[x['id'] for x in payload['selected_workflows']],'minimum_total_cases':payload['case_pack_rules']['minimum_total_cases'],'contract_sha256':payload['contract']['sha256']},indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
