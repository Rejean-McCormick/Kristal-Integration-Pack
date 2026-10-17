#!/usr/bin/env python3
"""Inspect or install a version-checked Konstellation overlay; fail closed on drift."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, sys

BASE = pathlib.Path(__file__).resolve().parents[1]
OVERLAY = BASE / 'overlay'
TARGETS = ('server/index.mjs', 'server/config.mjs', 'src/components/Explorer.svelte')
EXTRAS = ('server/integrations/kompiler-bridge.mjs', 'src/components/KompilerPanel.svelte')

def inspect(root: pathlib.Path) -> dict:
    """Read-only compatibility report; never claims runtime or API qualification."""
    manifest_file = root / '.kristal-integration-backup/patched.sha256.json'
    manifest = None
    if manifest_file.is_file():
        try:
            manifest = json.loads(manifest_file.read_text('utf-8'))
        except (OSError, json.JSONDecodeError):
            manifest = None
    version = None
    if (root / 'package.json').is_file():
        try:
            version = json.loads((root / 'package.json').read_text('utf-8')).get('version')
        except (OSError, json.JSONDecodeError):
            pass
    observed = {}
    for name in (*TARGETS, *EXTRAS):
        file = root / name
        data = file.read_bytes() if file.is_file() else None
        recorded = manifest.get(name) if isinstance(manifest, dict) else None
        observed[name] = {
            'present': data is not None,
            'recorded_patch_matches': bool(data is not None and recorded and hashlib.sha256(data).hexdigest() == recorded),
            'matches_pack_overlay': bool(name in EXTRAS and data is not None and data == (OVERLAY/name).read_bytes()),
        }
    integrated = (observed[EXTRAS[0]]['present'] and observed[EXTRAS[1]]['present']
                  and (root/TARGETS[0]).is_file()
                  and 'KompilerBridge' in (root/TARGETS[0]).read_text('utf-8', errors='replace'))
    return {
        'konstellation_version': version,
        'supported_legacy_overlay_base': version == '1.0.0-rc.2',
        'existing_integration': integrated,
        'has_patch_manifest': isinstance(manifest, dict),
        'recorded_patch_matches': bool(manifest and all(v['recorded_patch_matches'] for v in observed.values())),
        'pack_overlay_matches_installed': all(observed[n]['matches_pack_overlay'] for n in EXTRAS),
        'files': observed,
        'recommendation': ('DO_NOT_REINSTALL_EXISTING_INTEGRATION' if integrated else
                           'INSPECT_PARTIAL_INSTALLATION' if any(observed[n]['present'] for n in EXTRAS) else
                           'PREVIEW_ONLY_BEFORE_LEGACY_INSTALL'),
    }

def replace_once(source: str, original: str, replacement: str, destination: str) -> str:
    if replacement in source:  # idempotency even if replacement retains original text
        return source
    if original not in source:
        raise RuntimeError(f'Patch anchor missing in {destination}: {original[:90]}')
    if source.count(original) != 1:
        raise RuntimeError(f'Patch anchor is not unique in {destination}')
    return source.replace(original, replacement)

def patch(root: pathlib.Path, apply: bool = False) -> list[str]:
    if not (root/'package.json').is_file(): raise RuntimeError('Invalid Konstellation checkout root')
    import json
    version = json.loads((root/'package.json').read_text('utf-8')).get('version')
    if version != '1.0.0-rc.2': raise RuntimeError(f'Unsupported Konstellation version: {version}; legacy overlay requires 1.0.0-rc.2')
    targets = [
      'server/index.mjs', 'server/config.mjs', 'src/components/Explorer.svelte',
    ]
    replacements = {
      'server/index.mjs': [
        ("import { SemantikAdapter } from './integrations/semantik.mjs';",
         "import { SemantikAdapter } from './integrations/semantik.mjs';\nimport { KompilerBridge } from './integrations/kompiler-bridge.mjs';"),
        ("async function body(req) {\n  let size = 0;", "async function body(req, maxBytes = 65536) {\n  let size = 0;"),
        ("if (size > 65536)", "if (size > maxBytes)"),
        ("  semantik = new SemantikAdapter(),", "  semantik = new SemantikAdapter(),\n  kompiler = new KompilerBridge(),"),
        ("        if(req.method==='GET' && ['/api/bootstrap','/api/capabilities'].includes(url.pathname)) {",
         "        if(req.method==='GET' && url.pathname==='/api/kompiler/capabilities') {\n          requireScope(principal,'read'); requireScope(principal,'kompiler');\n          return send(await kompiler.capabilities());\n        }\n        if(req.method==='GET' && ['/api/bootstrap','/api/capabilities'].includes(url.pathname)) {"),
        ("        if(url.pathname.startsWith('/api/sa')) requireScope(principal,'sa'); else requireScope(principal,'read');",
         "        if(url.pathname.startsWith('/api/sa')) requireScope(principal,'sa'); else requireScope(principal,'read');\n        if(url.pathname.startsWith('/api/kompiler/')) requireScope(principal,'kompiler');"),
        ("        const b=await body(req); if(!b||typeof b!=='object'||Array.isArray(b)) fail('INVALID_QUERY','Objet JSON requis.');",
         "        const b=await body(req, url.pathname==='/api/kompiler/projection'?1_500_000:65536); if(!b||typeof b!=='object'||Array.isArray(b)) fail('INVALID_QUERY','Objet JSON requis.');"),
        ("        switch(url.pathname){\n          case '/api/query':", "        switch(url.pathname){\n          case '/api/kompiler/validate': return send(await kompiler.validate(b));\n          case '/api/kompiler/run': return send(await kompiler.run(b));\n          case '/api/kompiler/projection': return send(await kompiler.projection(b.context_pack,b.surface_id));\n          case '/api/query':"),
      ],
      'server/config.mjs': [
        ("scopes: ['read','metrics','sa','admin'],", "scopes: ['read','metrics','sa','admin', ...(env.KONSTELLATION_ENABLE_KOMPILER_LOCAL === 'true' ? ['kompiler'] : [])],"),
      ],
      'src/components/Explorer.svelte': [
        ("  import Communication from './Communication.svelte';", "  import Communication from './Communication.svelte';\n  import KompilerPanel from './KompilerPanel.svelte';"),
        ("      <div class=\"workspace\">", "      <KompilerPanel {authToken} />\n      <div class=\"workspace\">"),
      ],
    }
    changed = []
    contents = {}
    for relative in targets:
        s = (root/relative).read_text('utf-8')
        for original,new in replacements[relative]:
            s = replace_once(s, original, new, relative)
        contents[relative] = s
        if s != (root/relative).read_text('utf-8'): changed.append(relative)
    extra = [
      'server/integrations/kompiler-bridge.mjs',
      'src/components/KompilerPanel.svelte',
    ]
    for name in extra:
        p=root/name
        if p.exists() and p.read_bytes() != (OVERLAY/name).read_bytes():
            raise RuntimeError(f'Existing integration file differs: {name}. Do not overwrite; run --status and review upstream.')
        if not p.exists(): changed.append(name)
    if apply:
        backup = root/'.kristal-integration-backup'
        for relative in targets:
            dest = root/relative
            if relative in changed:
                orig=backup/relative; orig.parent.mkdir(parents=True,exist_ok=True)
                if not orig.exists(): shutil.copy2(dest,orig)
                dest.write_text(contents[relative],encoding='utf-8')
        for relative in extra:
            dest=root/relative
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists(): shutil.copy2(OVERLAY/relative,dest)
        hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in targets+extra}
        (backup/'patched.sha256.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf8')
    return changed

def rollback(root: pathlib.Path) -> list[str]:
    backup=root/'.kristal-integration-backup'
    originals=['server/index.mjs','server/config.mjs','src/components/Explorer.svelte']
    extra=['server/integrations/kompiler-bridge.mjs','src/components/KompilerPanel.svelte']
    if not all((backup/n).is_file() for n in originals) or not (backup/'patched.sha256.json').is_file():
        raise RuntimeError('Incomplete backup or patch manifest: cannot roll back automatically')
    hashes=json.loads((backup/'patched.sha256.json').read_text('utf8'))
    for name,expected in hashes.items():
        actual=root/name
        if not actual.is_file() or hashlib.sha256(actual.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('Subsequent changes detected: refusing rollback for '+name)
    for name in extra:
        target=root/name
        if target.exists() and target.read_bytes() != (OVERLAY/name).read_bytes():
            raise RuntimeError('Bridge file changed by another tool; rollback denied: '+name)
    for name in originals:
        current=(root/name).read_text('utf8')
        if name=='server/index.mjs' and "import { KompilerBridge }" not in current:
            raise RuntimeError('Patch missing or file modified: '+name)
        if name=='server/config.mjs' and 'KONSTELLATION_ENABLE_KOMPILER_LOCAL' not in current:
            raise RuntimeError('Patch missing or file modified: '+name)
        if name=='src/components/Explorer.svelte' and '<KompilerPanel' not in current:
            raise RuntimeError('Patch missing or file modified: '+name)
    for name in originals: shutil.copy2(backup/name,root/name)
    for name in extra: (root/name).unlink(missing_ok=True)
    return originals+extra

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('konstellation',type=pathlib.Path)
    parser.add_argument('--apply',action='store_true',help='Apply the legacy overlay (default: preview only)')
    parser.add_argument('--rollback',action='store_true',help='Restore only an unchanged backed-up legacy installation')
    parser.add_argument('--status',action='store_true',help='Inspect current Konstellation integration without modifying it')
    a=parser.parse_args()
    try:
        if sum((a.rollback,a.apply,a.status)) > 1:
            raise RuntimeError('--status, --apply and --rollback are mutually exclusive')
        if a.status:
            print(json.dumps(inspect(a.konstellation.resolve()),indent=2))
            sys.exit(0)
        if a.rollback:
            modified=rollback(a.konstellation.resolve());label='ROLLED_BACK'
        else:
            modified=patch(a.konstellation.resolve(),a.apply);label='INSTALLED' if a.apply else 'PREVIEW'
        print(label + ': ' + (', '.join(modified) if modified else 'already up to date'))
    except Exception as exc:
        print('ERROR:',exc,file=sys.stderr);sys.exit(1)
