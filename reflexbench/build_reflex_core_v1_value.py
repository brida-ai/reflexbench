#!/usr/bin/env python3
"""Build the minimal Reflex Core v1 same-response value artifact.

Core v1 intentionally excludes prompt rewriting, order ensembles, model-specific adapters
and calibration fitting. It answers one product question: when the same admitted engine
response is passed through the declared deterministic Reflex policy, what changes?
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from harness_value import bootstrap_policy_delta, policy_value


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def build(result_path:Path, contract_path:Path)->dict[str,Any]:
    result=json.loads(result_path.read_text())
    rows=result.get('rows')
    if not isinstance(rows,list) or not rows:
        raise ValueError('result must contain non-empty rows')
    summary=result.get('summary')
    if not isinstance(summary,dict):
        raise ValueError('result must contain summary')
    value=policy_value(rows)
    bootstrap=bootstrap_policy_delta(rows,iterations=20_000,seed=20260921)
    if int(summary['n'])!=len(rows):
        raise ValueError('summary row count mismatch')
    if abs(float(summary['semantic_accuracy'])-value['semantic_accuracy'])>1e-12:
        raise ValueError('semantic accuracy mismatch')
    if abs(float(summary['operational_accuracy'])-value['operational_accuracy'])>1e-12:
        raise ValueError('operational accuracy mismatch')
    run=result.get('run') if isinstance(result.get('run'),dict) else {}
    model_calls=run.get('http_calls',run.get('http_requests',len(rows)))
    if not isinstance(model_calls,int): model_calls=len(rows)
    return {
      'schema':'brida.reflexbench.reflex-core-v1-value/v1alpha1',
      'claim_class':'product-regression-same-response-development-evidence',
      'contract':{
        'name':'Reflex System One Contract v1',
        'file':contract_path.name,
        'sha256':sha256(contract_path),
      },
      'engine':{
        'id':'typesafe-jev',
        'authority':'current-admitted-route',
        'source_result':result_path.name,
        'source_sha256':sha256(result_path),
      },
      'same_response_invariant':{
        'same_state':True,
        'same_questions':True,
        'same_engine_response':True,
        'raw_model_calls':model_calls,
        'reflex_model_calls':model_calls,
        'extra_model_calls':0,
        'prompt_rewrite':False,
        'order_ensemble':False,
        'model_specific_adapter':False,
        'new_calibration_fit':False,
      },
      'raw':{
        'n':len(rows),
        'semantic_correct':sum(bool(r['semantic_correct']) for r in rows),
        'semantic_accuracy':value['semantic_accuracy'],
      },
      'reflex_core_v1':{
        'operational_correct':sum(bool(r['operational_correct']) for r in rows),
        'operational_accuracy':value['operational_accuracy'],
        'rescues':value['rescues'],
        'harms':value['harms'],
        'interventions':value['interventions'],
        'intervention_rate':value['intervention_rate'],
        'delta_vs_raw':value['net_accuracy_delta'],
        'bootstrap_delta':bootstrap,
      },
      'boundary':(
        'Public Reflex product fixtures are regression/harness-development evidence, not an independent '
        'model benchmark. This artifact proves only the same-response deterministic policy contribution '
        'for the currently admitted Jev route on these fixtures.'
      ),
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--result',type=Path,default=Path('experiments/reflexbench/results/jev-public110-vercel-paced.json'))
    ap.add_argument('--contract',type=Path,default=Path('docs/research/reflex/reflexbench/system-one-contract-v1.md'))
    ap.add_argument('--output',type=Path,default=Path('experiments/reflexbench/results/reflex-core-v1-typesafe-jev-public110.json'))
    a=ap.parse_args(); payload=build(a.result,a.contract)
    a.output.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'raw':payload['raw'],'reflex_core_v1':payload['reflex_core_v1'],'same_response_invariant':payload['same_response_invariant']},indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
