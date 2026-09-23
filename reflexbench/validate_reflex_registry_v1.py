#!/usr/bin/env python3
"""Validate a Reflex recipe registry against System One Contract v1 without rewriting it."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from system_one_contract_v1 import validate_recipe


def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_registry(registry:Path,source_revision:str)->dict[str,Any]:
    root=registry/'examples'/'use-cases'
    paths=sorted(root.glob('*/custom-reflex.json'),key=lambda p:p.as_posix())
    if not paths: raise ValueError(f'no recipes under {root}')
    recipes=[]; qtypes=Counter(); qcounts=Counter(); failures=[]
    for path in paths:
        rel=path.relative_to(registry).as_posix()
        raw=path.read_bytes()
        try:
            d=json.loads(raw); validate_recipe(d)
            questions=d['questions']; qcounts[len(questions)]+=1
            for q in questions.values():
                t=str(q['type']).lower(); qtypes['noul' if t=='binary' else t]+=1
            recipes.append({'id':path.parent.name,'file':rel,'sha256':hashlib.sha256(raw).hexdigest(),'question_count':len(questions),'policyType':d['declarative_policy']['type']})
        except Exception as exc:
            failures.append({'id':path.parent.name,'file':rel,'error_type':type(exc).__name__,'error':str(exc)[:500]})
    return {
      'schema':'brida.reflexbench.system-one-contract-v1-registry-validation/v1alpha1',
      'contract':'Reflex System One Contract v1',
      'source_repository':'brida-ai/reflex',
      'source_revision':source_revision,
      'recipes_total':len(paths),
      'recipes_valid':len(recipes),
      'recipes_failed':len(failures),
      'question_count_histogram':{str(k):v for k,v in sorted(qcounts.items())},
      'question_type_counts':dict(sorted(qtypes.items())),
      'recipes':recipes,
      'failures':failures,
      'all_valid':not failures,
      'boundary':'Schema/contract compatibility only. This does not measure engine quality or policy correctness.',
    }


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--registry',required=True,type=Path); ap.add_argument('--source-revision',required=True); ap.add_argument('--output',required=True,type=Path)
    a=ap.parse_args(); payload=validate_registry(a.registry,a.source_revision); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n'); print(json.dumps({k:payload[k] for k in ['source_revision','recipes_total','recipes_valid','recipes_failed','question_count_histogram','question_type_counts','all_valid']},indent=2)); return 0 if payload['all_valid'] else 2

if __name__=='__main__': raise SystemExit(main())
