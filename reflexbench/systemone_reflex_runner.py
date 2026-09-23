#!/usr/bin/env python3
"""Provider-neutral HTTP evaluation of engines inside/outside the Reflex policy harness.

The runner reports threshold-free semantic capability, declarative policy behavior,
question-set interference, and an optional two-order Choice probability ensemble.
It is research-only and deliberately omits raw states/questions from result artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import statistics
import time
from pathlib import Path
from typing import Any, Callable, Mapping, TypeVar

from reflexbench_policy import apply_declarative_policy
from registry_identity import registry_identity
from systemone_helpers import answer_summary, average_choice_answers, normalize_questions, reverse_choice_question
from systemone_http import SystemOneHttpClient, SystemOneHttpError


T = TypeVar("T")


def _retryable_transport_error(exc: BaseException) -> tuple[bool, int | None]:
    if isinstance(exc, SystemOneHttpError):
        status = int(exc.status)
        return status == 429 or 500 <= status <= 599, status
    if isinstance(exc, (ConnectionError, OSError, http.client.HTTPException)):
        return True, None
    return False, None


def call_with_transport_retries(
    fn: Callable[[], T],
    *,
    max_retries: int,
    backoff_ms: float,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[T, dict[str, Any]]:
    """Retry transport/provider failures only; never retry semantic/client 4xx.

    The returned metadata preserves retry status codes without raw provider bodies.
    Defaults are supplied by the CLI as zero retries, preserving historical runs.
    """
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")
    if backoff_ms < 0:
        raise ValueError("backoff_ms must be >= 0")
    retry_statuses: list[int | None] = []
    attempts = 0
    while True:
        attempts += 1
        try:
            result = fn()
            return result, {
                "attempts": attempts,
                "retries_used": attempts - 1,
                "retry_statuses": retry_statuses,
            }
        except Exception as exc:
            retryable, status = _retryable_transport_error(exc)
            if not retryable or attempts > max_retries:
                meta = {
                    "attempts": attempts,
                    "retries_used": max(0, attempts - 1),
                    "retry_statuses": retry_statuses + ([status] if retryable and status is not None else []),
                }
                try:
                    setattr(exc, "reflexbench_transport_meta", meta)
                except Exception:
                    pass
                raise
            retry_statuses.append(status)
            if backoff_ms:
                sleep_fn(backoff_ms / 1000.0)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    return xs[min(len(xs) - 1, max(0, round((len(xs) - 1) * q)))]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    latencies = [float(r["latency_ms"]) for r in rows]
    return {
        "n": n,
        "semantic_correct": sum(bool(r["semantic_correct"]) for r in rows),
        "semantic_accuracy": sum(bool(r["semantic_correct"]) for r in rows) / n if n else None,
        "operational_correct": sum(bool(r["operational_correct"]) for r in rows),
        "operational_accuracy": sum(bool(r["operational_correct"]) for r in rows) / n if n else None,
        "review_or_uncertain": sum(r["operational_branch"] != r["semantic_branch"] for r in rows),
        "latency_ms": {
            "mean": statistics.fmean(latencies) if latencies else None,
            "p50": percentile(latencies, .50),
            "p95": percentile(latencies, .95),
            "p99": percentile(latencies, .99),
        },
    }


def grouped(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return {v: summarize([r for r in rows if str(r[key]) == v]) for v in sorted({str(r[key]) for r in rows})}


def source_row_metadata(row: Mapping[str, Any], index: int) -> dict[str, str]:
    """Normalize corpus metadata without changing request semantics.

    Older ReflexBench corpora used `caseId`/`difficulty`; Core-v1 blind workflow
    gates use `id`/`caseClass` and add language/evidenceClass. This helper affects
    result metadata only: state/questions sent to the engine are untouched.
    """
    case_id = row.get("caseId", row.get("id", index))
    difficulty = row.get("difficulty", row.get("caseClass", "unspecified"))
    language = row.get("language", "unspecified")
    evidence_class = row.get("evidenceClass", "unspecified")
    return {
        "case_id": str(case_id),
        "difficulty": str(difficulty),
        "language": str(language),
        "evidence_class": str(evidence_class),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--registry", required=True, type=Path)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--endpoint", default="/v1/systemone")
    ap.add_argument("--auth-mode", choices=("none", "bearer", "x-api-key"), default="none")
    ap.add_argument("--api-key")
    ap.add_argument("--model")
    ap.add_argument("--native-permutations", type=int)
    ap.add_argument("--inter-request-delay-ms", type=float, default=0.0)
    ap.add_argument("--transport-retries", type=int, default=0)
    ap.add_argument("--transport-retry-backoff-ms", type=float, default=0.0)
    ap.add_argument("--engine", required=True)
    ap.add_argument("--engine-revision", required=True)
    ap.add_argument("--question-mode", choices=("all", "policy-only"), default="all")
    ap.add_argument("--choice-ensemble", choices=("none", "reverse"), default="none")
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    if args.inter_request_delay_ms < 0:
        raise SystemExit("--inter-request-delay-ms must be >= 0")
    if args.transport_retries < 0:
        raise SystemExit("--transport-retries must be >= 0")
    if args.transport_retry_backoff_ms < 0:
        raise SystemExit("--transport-retry-backoff-ms must be >= 0")

    source_rows = [json.loads(line) for line in args.corpus.read_text().splitlines() if line.strip()]
    definitions: dict[str, dict[str, Any]] = {}
    for row in source_rows:
        use_case = str(row["useCase"])
        if use_case not in definitions:
            definitions[use_case] = json.loads((args.registry / "examples" / "use-cases" / use_case / "custom-reflex.json").read_text())

    registry_info = registry_identity(args.registry, definitions.keys())

    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    http_requests = 0
    transport_retry_requests = 0
    with SystemOneHttpClient(args.base_url, endpoint=args.endpoint, auth_mode=args.auth_mode, api_key=args.api_key) as client:
        def request(state, questions, *, count_run: bool = True):
            nonlocal http_requests, transport_retry_requests
            def one_call():
                return client.request(state, questions, model=args.model, permutations=args.native_permutations)
            try:
                result, retry_meta = call_with_transport_retries(
                    one_call,
                    max_retries=args.transport_retries,
                    backoff_ms=args.transport_retry_backoff_ms,
                )
            except Exception as exc:
                retry_meta = getattr(exc, "reflexbench_transport_meta", {"attempts": 1, "retries_used": 0, "retry_statuses": []})
                if count_run:
                    http_requests += int(retry_meta.get("attempts", 1))
                    transport_retry_requests += int(retry_meta.get("retries_used", 0))
                raise
            if count_run:
                http_requests += int(retry_meta["attempts"])
                transport_retry_requests += int(retry_meta["retries_used"])
            if args.inter_request_delay_ms:
                time.sleep(args.inter_request_delay_ms / 1000.0)
            return result, retry_meta

        # Warm using exactly the selected question mode.
        first = source_rows[0]
        d0 = definitions[str(first["useCase"])]
        p0 = d0["declarative_policy"]
        q0 = normalize_questions(d0["questions"])
        if args.question_mode == "policy-only":
            q0 = {str(p0["questionId"]): q0[str(p0["questionId"])]}
        warmup: dict[str, Any] = {"attempted": True, "ok": False}
        try:
            warmed, warm_retry = request(first["state"], q0, count_run=False)
            warmup.update({"ok": True, "latency_ms": warmed.latency_ms, "transport": warm_retry})
        except Exception as exc:
            warmup.update({"error_type": type(exc).__name__, "error": str(exc)[:500]})

        for index, row in enumerate(source_rows):
            use_case = str(row["useCase"])
            metadata = source_row_metadata(row, index)
            definition = definitions[use_case]
            policy = definition["declarative_policy"]
            question_id = str(policy["questionId"])
            questions = normalize_questions(definition["questions"])
            if args.question_mode == "policy-only":
                questions = {question_id: questions[question_id]}
            try:
                primary, primary_retry = request(row["state"], questions)
                answers = primary.payload.get("answers")
                if not isinstance(answers, Mapping) or not isinstance(answers.get(question_id), Mapping):
                    raise ValueError(f"missing answers.{question_id}")
                answer: Mapping[str, Any] = answers[question_id]
                latency_ms = primary.latency_ms
                ensemble_used = False

                if args.choice_ensemble == "reverse" and policy.get("type") == "choice":
                    reversed_questions = {qid: dict(q) for qid, q in questions.items()}
                    reversed_questions[question_id] = reverse_choice_question(questions[question_id])
                    secondary, secondary_retry = request(row["state"], reversed_questions)
                    secondary_answers = secondary.payload.get("answers")
                    if not isinstance(secondary_answers, Mapping) or not isinstance(secondary_answers.get(question_id), Mapping):
                        raise ValueError(f"secondary response missing answers.{question_id}")
                    answer = average_choice_answers(answer, secondary_answers[question_id])
                    latency_ms += secondary.latency_ms
                    ensemble_used = True

                decision = apply_declarative_policy(policy, answer)
                expected = str(row["expectedBranch"])
                results.append({
                    "index": index,
                    "use_case": use_case,
                    **metadata,
                    "policy_type": str(policy["type"]),
                    "expected_branch": expected,
                    "semantic_branch": decision.semantic_branch,
                    "operational_branch": decision.operational_branch,
                    "semantic_correct": decision.semantic_branch == expected,
                    "operational_correct": decision.operational_branch == expected,
                    "selected_probability": decision.selected_probability,
                    "ensemble_used": ensemble_used,
                    "latency_ms": latency_ms,
                    "answer": answer_summary(answer),
                    "transport": {
                        "primary": primary_retry,
                        "secondary": secondary_retry if ensemble_used else None,
                    },
                })
            except Exception as exc:
                failure_transport = getattr(exc, "reflexbench_transport_meta", None)
                failures.append({
                    "index": index,
                    "use_case": use_case,
                    **metadata,
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:500],
                    "transport": failure_transport,
                })

    payload = {
        "schema": "brida.reflexbench.reflex-http-result/v1alpha1",
        "visibility": "private",
        "corpus": {"path_name": args.corpus.name, "sha256": sha256_file(args.corpus), "rows": len(source_rows)},
        "registry": registry_info,
        "engine": {"id": args.engine, "revision": args.engine_revision, "model": args.model},
        "ablation": {
            "question_mode": args.question_mode,
            "choice_ensemble": args.choice_ensemble,
            "native_permutations": args.native_permutations,
            "inter_request_delay_ms": args.inter_request_delay_ms,
            "transport_retries": args.transport_retries,
            "transport_retry_backoff_ms": args.transport_retry_backoff_ms,
        },
        "warmup": warmup,
        "completion": {"completed": len(results), "failed": len(failures), "rate": len(results) / len(source_rows) if source_rows else None},
        "run": {
            "http_requests": http_requests,
            "transport_retry_requests": transport_retry_requests,
            "successful_decisions": len(results),
        },
        "summary": summarize(results),
        "by_difficulty": grouped(results, "difficulty"),
        "by_case_class": grouped(results, "difficulty"),
        "by_language": grouped(results, "language"),
        "by_evidence_class": grouped(results, "evidence_class"),
        "by_policy_type": grouped(results, "policy_type"),
        "by_use_case": grouped(results, "use_case"),
        "failures": failures,
        "rows": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: payload[k] for k in ("engine", "ablation", "completion", "run", "summary")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
