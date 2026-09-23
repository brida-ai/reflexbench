#!/usr/bin/env python3
"""Materialize the public Reflex product-fixture lane from a frozen brida-ai/reflex checkout.

Product fixtures are regression/harness-development evidence only. They are not an independent
model-quality benchmark. Output bytes are deterministic for a given registry checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from system_one_contract_v1 import validate_recipe


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build(registry: Path, source_revision: str) -> tuple[bytes, dict[str, Any]]:
    recipes: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    use_cases_root = registry / "examples" / "use-cases"
    paths = sorted(use_cases_root.glob("*/custom-reflex.json"), key=lambda p: p.as_posix())
    if not paths:
        raise ValueError(f"no custom-reflex.json files under {use_cases_root}")

    for path in paths:
        raw = path.read_bytes()
        definition = json.loads(raw)
        validate_recipe(definition)
        use_case = path.parent.name
        policy = definition.get("declarative_policy")
        if not isinstance(policy, dict) or not isinstance(policy.get("type"), str):
            raise ValueError(f"missing declarative_policy.type: {path}")
        fixtures = definition.get("fixtures")
        if not isinstance(fixtures, list):
            raise ValueError(f"fixtures must be a list: {path}")
        recipes.append({
            "use_case": use_case,
            "policy_type": policy["type"],
            "fixtures": len(fixtures),
            "custom_reflex_sha256": sha256_bytes(raw),
        })
        for index, fixture in enumerate(fixtures):
            if not isinstance(fixture, dict):
                raise ValueError(f"fixture must be an object: {path} #{index}")
            state = fixture.get("state")
            expected = fixture.get("expectedBranch", fixture.get("expected_branch"))
            if state is None or expected is None:
                raise ValueError(f"fixture missing state/expectedBranch: {path} #{index}")
            case_id = str(
                fixture.get("id")
                or fixture.get("caseId")
                or fixture.get("name")
                or f"fixture-{index + 1}"
            )
            rows.append({
                "useCase": use_case,
                "caseId": case_id,
                "difficulty": str(fixture.get("difficulty") or "fixture"),
                "state": state,
                "expectedBranch": str(expected),
            })

    payload = "".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows
    ).encode("utf-8")
    policy_fixture_counts = Counter()
    policy_by_case = {r["use_case"]: r["policy_type"] for r in recipes}
    for row in rows:
        policy_fixture_counts[policy_by_case[row["useCase"]]] += 1
    manifest = {
        "schema": "brida.reflexbench.fixture-manifest/v1alpha1",
        "source_repository": "brida-ai/reflex",
        "source_revision": source_revision,
        "corpus_sha256": sha256_bytes(payload),
        "rows": len(rows),
        "use_cases": len(recipes),
        "policy_fixture_counts": dict(sorted(policy_fixture_counts.items())),
        "recipes": recipes,
        "claim_class": "public-product-fixtures-regression-and-harness-development-only",
    }
    return payload, manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True, type=Path)
    ap.add_argument("--source-revision", required=True)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    args = ap.parse_args()
    payload, manifest = build(args.registry, args.source_revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    manifest = {**manifest, "corpus_path": args.output.name}
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: manifest[k] for k in ("source_revision", "rows", "use_cases", "policy_fixture_counts", "corpus_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
