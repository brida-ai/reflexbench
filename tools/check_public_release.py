#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
bad=[]
path_parts=('private-v2','private-use-case','hidden-gate','brida-b2','models/')
needles=(b'/home/carlos/',b'/Users/navarro/',b'jv_live_',b'gho_',b'sk_live_',b'BEGIN PRIVATE KEY',b'SUPABASE_SERVICE_ROLE_KEY',b'RAILWAY_TOKEN')
for p in root.rglob('*'):
    if not p.is_file() or '.git' in p.parts: continue
    if p.relative_to(root).as_posix() == 'tools/check_public_release.py': continue
    rel=p.relative_to(root).as_posix(); low=rel.lower()
    if any(x in low for x in path_parts): bad.append('forbidden path: '+rel)
    data=p.read_bytes()
    for needle in needles:
        if needle in data: bad.append(f'forbidden content {needle!r}: {rel}')
if bad:
    print(chr(10).join(bad),file=sys.stderr); raise SystemExit(2)
print('public release check: OK')
