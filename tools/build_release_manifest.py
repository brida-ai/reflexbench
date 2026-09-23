#!/usr/bin/env python3
"""Rebuild the public ReflexBench release manifest without private tooling."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

SKIP_PARTS={'.git','__pycache__'}
MANIFEST=Path('release/v1-manifest.json')

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=Path('.'))
    ap.add_argument('--release-candidate',help='Override release_candidate metadata, e.g. 1.0.0-rc.3 or 1.0.0')
    args=ap.parse_args(); root=args.root.resolve(); path=root/MANIFEST
    old=json.loads(path.read_text()) if path.exists() else {}
    entries=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(root)
        if rel==MANIFEST or any(part in SKIP_PARTS for part in rel.parts) or p.suffix in {'.pyc','.pyo'}: continue
        entries.append({'path':rel.as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    payload={
      'benchmark_version':old.get('benchmark_version','1.0.0'),
      'files':entries,
      'reflex_registry_sha_at_export':old.get('reflex_registry_sha_at_export'),
      'release_candidate':args.release_candidate or old.get('release_candidate'),
      'schema':'brida.reflexbench.public-release/v1',
      'source_private_monorepo_sha':old.get('source_private_monorepo_sha'),
      'visibility_target':old.get('visibility_target','private-rc-then-public'),
    }
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(f'{path}: {len(entries)} files')
    return 0
if __name__=='__main__': raise SystemExit(main())
