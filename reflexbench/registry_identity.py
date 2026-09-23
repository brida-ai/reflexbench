"""Immutable identity for the Custom Reflex registry consumed by a benchmark result."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Iterable


def custom_reflex_manifest_hash(registry: Path, use_cases: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for use_case in sorted(set(map(str, use_cases))):
        path = registry / "examples" / "use-cases" / use_case / "custom-reflex.json"
        data = path.read_bytes()
        digest.update(use_case.encode("utf-8"))
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    return digest.hexdigest()


def registry_identity(registry: Path, use_cases: Iterable[str]) -> dict[str, object]:
    revision = subprocess.run(
        ["git", "-C", str(registry), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if len(revision) != 40:
        raise ValueError("registry revision is not a full Git SHA")
    names = sorted(set(map(str, use_cases)))
    return {
        "revision": revision,
        "custom_reflex_manifest_sha256": custom_reflex_manifest_hash(registry, names),
        "use_cases": len(names),
    }
