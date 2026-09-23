#!/usr/bin/env python3
"""Build a frozen Choice-only System One task lane from public Reflex fixtures.

The source fixture corpus intentionally stores state + expected branch only. This builder
rejoins it with the exact frozen custom-reflex recipes so Brida model adapters consume the
real question instructions, criteria, label order and branch mapping.
"""
from __future__ import annotations

import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from typing import Any


def sha256(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()


def build(corpus:Path,manifest_path:Path,registry:Path,*,source_revision:str)->tuple[list[dict[str,Any]],dict[str,Any]]:
    manifest=json.loads(manifest_path.read_text())
    if str(manifest.get('source_revision'))!=source_revision: raise ValueError('source revision mismatch')
    if sha256(corpus)!=manifest.get('corpus_sha256'): raise ValueError('public fixture corpus SHA mismatch')
    recipes={str(x['use_case']):x for x in manifest.get('recipes',[])}
    rows=[json.loads(x) for x in corpus.read_text().splitlines() if x.strip()]
    tasks=[]; cards=Counter(); use_cases=set()
    for row in rows:
        use=str(row['useCase']); meta=recipes.get(use)
        if meta is None: raise ValueError(f'missing manifest recipe for {use}')
        rp=registry/'examples'/'use-cases'/use/'custom-reflex.json'
        if not rp.is_file(): raise ValueError(f'missing recipe file for {use}')
        if sha256(rp)!=meta.get('custom_reflex_sha256'): raise ValueError(f'recipe SHA mismatch for {use}')
        definition=json.loads(rp.read_text()); policy=definition.get('declarative_policy') or {}
        if str(policy.get('type'))!='choice': continue
        qid=str(policy.get('questionId')); question=(definition.get('questions') or {}).get(qid)
        if not isinstance(question,dict) or str(question.get('type'))!='choice': raise ValueError(f'invalid Choice question for {use}')
        criteria=question.get('criteria')
        if not isinstance(criteria,dict) or len(criteria)<2: raise ValueError(f'Choice criteria missing for {use}')
        labels=[str(x) for x in criteria]
        if len(labels)!=len(set(labels)): raise ValueError(f'duplicate Choice labels for {use}')
        expected_branch=str(row['expectedBranch'])
        branches=policy.get('branches') or {}
        gold=[str(label) for label,branch in branches.items() if str(branch)==expected_branch]
        if len(gold)!=1: raise ValueError(f'expected branch must map to one unique Choice label for {use}/{row.get("caseId")}: {gold!r}')
        if gold[0] not in labels: raise ValueError(f'gold label outside criteria for {use}')
        task_id=f'public-choice-v1-{use}-{row["caseId"]}'
        tasks.append({
          'id':task_id,'group':task_id,'family':use,'split':'development','language':'en',
          'labels':labels,'expected':gold[0],'expectedBranch':expected_branch,
          'state':row['state'],'question':question,
          'provenance':{'source':'brida-ai/reflex public fixture','source_revision':source_revision,'use_case':use,'case_id':str(row['caseId']),'recipe_sha256':meta['custom_reflex_sha256'],'claim_class':'product-regression-development'},
        })
        cards[len(labels)]+=1; use_cases.add(use)
    meta={
      'schema':'brida.reflexbench.public-choice-task-manifest/v1alpha1','status':'development',
      'sourceRepository':'brida-ai/reflex','sourceRevision':source_revision,
      'sourceCorpusSha256':sha256(corpus),'sourceManifestSha256':sha256(manifest_path),
      'choiceRows':len(tasks),'choiceUseCases':len(use_cases),'cardinalityCounts':dict(sorted(cards.items())),
      'selection':'all public fixture rows whose frozen declarative policy type is choice; branch must map to one unique Choice label',
      'claimClass':'public-product-fixtures-regression-and-adapter-development-only',
    }
    return tasks,meta


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--corpus',required=True,type=Path); ap.add_argument('--source-manifest',required=True,type=Path); ap.add_argument('--registry',required=True,type=Path); ap.add_argument('--source-revision',required=True); ap.add_argument('--output',required=True,type=Path); ap.add_argument('--manifest-out',required=True,type=Path); a=ap.parse_args()
    tasks,meta=build(a.corpus,a.source_manifest,a.registry,source_revision=a.source_revision)
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in tasks))
    meta={**meta,'taskSha256':sha256(a.output),'taskFile':a.output.name}
    a.manifest_out.parent.mkdir(parents=True,exist_ok=True); a.manifest_out.write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n')
    print(json.dumps(meta,indent=2)); return 0

if __name__=='__main__': raise SystemExit(main())
