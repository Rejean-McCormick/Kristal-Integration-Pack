#!/usr/bin/env python3
"""Deterministically hash and package the Integration Pack sources.

No network, deployment, version rewriting or repository owner operations.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OMIT_DIRS = {'.git','__pycache__','.pytest_cache','.mypy_cache','dist','build','node_modules','.venv'}
OMIT_FILES = {'MANIFEST.sha256.json'}


def files():
    return sorted((p for p in ROOT.rglob('*') if p.is_file() and
                   not OMIT_DIRS.intersection(p.relative_to(ROOT).parts) and
                   p.suffix not in {'.pyc','.pyo','.log'} and p.name not in OMIT_FILES),
                  key=lambda p:p.relative_to(ROOT).as_posix())


def manifest():
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files()}


def build(out):
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for p in sorted([*files(),ROOT/'MANIFEST.sha256.json'],key=lambda x:x.relative_to(ROOT).as_posix()):
            name=p.relative_to(ROOT).as_posix()
            record=zipfile.ZipInfo('Kristal-Integration-Pack/'+name,(2026,10,17,0,0,0))
            record.compress_type=zipfile.ZIP_DEFLATED
            record.external_attr = 0o100644<<16
            z.writestr(record,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=8)


def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'verify'
    if mode=='manifest':
        (ROOT/'MANIFEST.sha256.json').write_text(json.dumps(manifest(),sort_keys=True,indent=2,ensure_ascii=False)+'\n')
        print('manifest refreshed')
    elif mode=='verify':
        stored=json.loads((ROOT/'MANIFEST.sha256.json').read_text())
        if stored!=manifest():
            raise SystemExit('MANIFEST MISMATCH: exact files or hash differ')
        print(f'MANIFEST VERIFIED: {len(stored)} files')
    elif mode=='zip':
        stored=json.loads((ROOT/'MANIFEST.sha256.json').read_text())
        if stored!=manifest():raise SystemExit('Refresh and verify manifest before packaging')
        if len(sys.argv)!=3:raise SystemExit('Usage: release_package.py zip OUTFILE.zip')
        build(Path(sys.argv[2]))
    else:
        raise SystemExit('Usage: release_package.py manifest|verify|zip OUTFILE.zip')

if __name__=='__main__':main()
