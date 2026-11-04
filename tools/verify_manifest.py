#!/usr/bin/env python3
import hashlib, json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'MANIFEST.sha256.json').read_text('utf8'))
for name,digest in manifest.items():
    if not (root/name).is_file() or hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
        raise SystemExit('INTEGRITY ERROR: '+name)
from release_package import files
actual={p.relative_to(root).as_posix() for p in files()}
missing=actual-set(manifest)
if missing: raise SystemExit('UNTRACKED FILES: '+str(sorted(missing)))
print(f'INTEGRITY OK: {len(manifest)} fichiers')
