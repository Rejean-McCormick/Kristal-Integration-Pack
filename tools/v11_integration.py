#!/usr/bin/env python3
"""Pinned Kristal Framework v11 read-only integration bridge.

Uses the *real* Framework draft.4 validators, diK coverage implementation,
and lexical resolver contracts. Never writes canonical input or rewrites ids.
No network, host installation, or publisher behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / 'contracts/v11-framework-pin.json'


class IntegrationError(ValueError):
    pass


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_framework(root: Path, pin_path: Path = PIN) -> dict:
    """Reject unreviewed schema/code drift; never run unpinned Framework scripts."""
    pin = json.loads(pin_path.read_text('utf-8'))
    if pin.get('profile') != 'kristal-integration-framework-pin/v11.0-draft.4':
        raise IntegrationError('Unrecognized Framework pin profile')
    root = Path(root).resolve()
    if not root.is_dir() or not (root / 'VERSION').is_file():
        raise IntegrationError('Framework checkout missing or invalid')
    if (root / 'VERSION').read_text('utf-8').strip() != pin['version']:
        raise IntegrationError('Framework version does not match reviewed v11 draft.4 pin')
    for name, digest in pin['files'].items():
        if name.startswith('/') or '..' in Path(name).parts:
            raise IntegrationError('Unsafe path in Framework pin')
        f = root / name
        if not f.is_file() or sha(f) != digest:
            raise IntegrationError('Framework pinned file digest mismatch: ' + name)
    return pin


def load_framework(root: Path):
    """Import only after verifying the exact referenced Framework scripts."""
    root = Path(root).resolve()
    verify_framework(root)
    directory = root / 'tools/v11'
    # Use a scope restricted to the reviewed scripts and their existing imports.
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    import validate_v11  # noqa: PLC0415 -- verified via SHA-256 above
    import dictionaries  # noqa: PLC0415
    import dik_coverage  # noqa: PLC0415
    for module in (validate_v11, dictionaries, dik_coverage):
        expected = (directory / (module.__name__ + '.py')).resolve()
        if Path(module.__file__).resolve() != expected:
            raise IntegrationError('Untrusted Framework module already imported: ' + module.__name__)
    return validate_v11, dictionaries, dik_coverage


def read_input(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise IntegrationError('Input must be a JSON object: ' + str(path))
    return value


def verify_bundle(args, modules=None):
    """Full framework structural/semantic check + audit of all lexical layers."""
    validator, dictionary, coverage = modules or load_framework(args.framework)
    registry = read_input(args.registry)
    graph = read_input(args.graph)
    crosswalk = read_input(args.crosswalk)
    catalog = read_input(args.catalog)
    validator.validate_documents(registry=registry, graph=graph, crosswalk=crosswalk, lexicons=[])
    dictionary.audit(args.catalog, args.crosswalk, args.registry)
    if catalog['namespace_id'] != graph['namespace_id']:
        raise IntegrationError('Graph and dictionary catalog namespaces differ')
    return registry, graph, crosswalk, catalog


def _needed_identities(graph):
    return sorted(set(graph['entities']) | set(graph['properties']))


def indexed_labels(*, graph, catalog, catalog_path, locale, dictionary):
    """One pass over each relevant file, NOT one pass per ID × layer.

    Literal terms are returned separately from graph ids. Never interprets a
    term or an alias as a new semantic identity.
    """
    languages = {v['tag']: v for v in catalog['languages']}
    if locale not in languages:
        raise IntegrationError('Locale not declared in catalog: ' + locale)
    needed = set(_needed_identities(graph))
    root = Path(catalog_path).resolve().parent
    selected = [locale] + languages[locale]['fallbacks']
    labels = {}
    for effective_locale in selected:
        if effective_locale not in languages:
            raise IntegrationError('Undeclared locale fallback: ' + effective_locale)
        winners = {}
        for layer in languages[effective_locale]['layers']:
            layer_path = dictionary.safe_file(root, layer['path'])
            for entry, _parent in dictionary.layer_records(layer_path, layer['kind']):
                kid = entry['semantic_id']
                if kid not in needed:
                    continue
                old = winners.get(kid)
                candidate = (layer['priority'], entry['preferred_term'], layer['layer_id'])
                if old is None or candidate[0] > old[0]:
                    winners[kid] = candidate
                elif candidate[0] == old[0] and candidate[1] != old[1]:
                    raise IntegrationError('Conflicting same-priority label: ' + kid)
        for kid, (_priority, term, layer_id) in winners.items():
            if kid not in labels:
                labels[kid] = {
                    'status': 'direct' if effective_locale == locale else 'fallback',
                    'term': term,
                    'effective_locale': effective_locale,
                    'layer_id': layer_id,
                }
    for kid in sorted(needed):
        labels.setdefault(kid, {'status': 'missing'})
    return {kid: labels[kid] for kid in sorted(labels)}


def make_read_view(args, bundle=None, dictionary=None):
    """Derived reading envelope; canonical graph preserved as immutable ID references."""
    if dictionary is None:
        _, dictionary, _ = load_framework(args.framework)
    _registry, graph, crosswalk, catalog = bundle or verify_bundle(args)
    labels = indexed_labels(graph=graph, catalog=catalog, catalog_path=args.catalog,
                            locale=args.locale, dictionary=dictionary)
    exact = {}
    for mapping in crosswalk['mappings']:
        if (mapping['status'] == 'accepted' and mapping['relation'] == 'exactMatch'
                and mapping['local_ref']['namespace_id'] == graph['namespace_id']):
            exact[mapping['local_ref']['id']] = mapping['external_ref']
    display = []
    for kid, label in labels.items():
        ref = {'semantic_id': kid, 'kind': 'entity' if kid.startswith('KQ') else 'property',
               'lexical': label}
        if kid in exact:
            ref['accepted_external_exact'] = exact[kid]
        display.append(ref)
    counts = {status: sum(x['lexical']['status'] == status for x in display)
              for status in ('direct', 'fallback', 'missing')}
    return {
        'profile': 'kristal.integration.read-view/v11.0-draft.1',
        'derived_only': True,
        'source': {
            'namespace_id': graph['namespace_id'], 'graph_id': graph['graph_id'],
            'graph_sha256': sha(args.graph), 'registry_sha256': sha(args.registry),
            'crosswalk_sha256': sha(args.crosswalk), 'catalog_sha256': sha(args.catalog),
            'framework_version': '11.0.0-draft.4',
        },
        'requested_locale': args.locale,
        'coverage_counts': counts,
        'presentation': display,
        # All endpoints remain KQ/KP/KA/KS; quotations and literal values remain values.
        'assertions': graph['assertions'],
        'limits': ('Non-canonical derived read view, not proof of complete translation, '
                   'identity authority, semantic migration or publication.'),
    }


def emit(result, out=None):
    serialized = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    if out is None:
        print(serialized, end='')
    else:
        out = Path(out).resolve()
        # Exclusive-create prevents modification of any existing artifact or report.
        with out.open('x', encoding='utf-8', newline='\n') as f:
            f.write(serialized)
        print(json.dumps({'saved': str(out), 'sha256': sha(out)}))


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['check', 'coverage', 'view'])
    ap.add_argument('--framework', type=Path, required=True, help='Exact pinned Framework 11.0.0-draft.4 checkout')
    for name in ('registry', 'graph', 'crosswalk', 'catalog'):
        ap.add_argument('--' + name, required=True, type=Path)
    ap.add_argument('--locale', help='Single declared locale for view (e.g. fr-CA)')
    ap.add_argument('--locales', help='Comma-separated declared locales for coverage (default: all)')
    ap.add_argument('--out', type=Path, help='Create a new output file; existing files are never overwritten')
    args = ap.parse_args(argv)
    if args.command == 'view' and (not args.locale or args.locales):
        ap.error('view requires --locale and forbids --locales')
    if args.command == 'coverage' and args.locale:
        ap.error('coverage uses --locales, not --locale')
    if args.command == 'check' and (args.locale or args.locales):
        ap.error('check does not accept locale selection')
    if args.out and args.out.resolve() in {Path(getattr(args, x)).resolve() for x in ('registry','graph','crosswalk','catalog')}:
        ap.error('Output may not replace an input')
    return args


def main(argv=None):
    args = parse(argv)
    modules = load_framework(args.framework)
    registry, graph, crosswalk, catalog = verify_bundle(args, modules)
    if args.command == 'view':
        result = make_read_view(args, (registry, graph, crosswalk, catalog), modules[1])
    elif args.command == 'coverage':
        if args.locales is not None and (not args.locales or any(not x for x in args.locales.split(','))):
            raise IntegrationError('Invalid empty locale in --locales')
        result = modules[2].make_report(graph_path=args.graph, catalog_path=args.catalog,
                     registry_path=args.registry, crosswalk_path=args.crosswalk,
                     locales=args.locales.split(',') if args.locales else None)
    else:
        result = {'profile': 'kristal.integration.v11-check/v1', 'valid': True,
                  'framework_version': '11.0.0-draft.4',
                  'namespace_id': graph['namespace_id'], 'graph_id': graph['graph_id'],
                  'source_sha256': {k: sha(getattr(args, k)) for k in ('registry','graph','crosswalk','catalog')},
                  'language_count': len(catalog['languages'])}
    emit(result, args.out)


if __name__ == '__main__':
    try:
        main()
    except (IntegrationError, ValueError, OSError, RuntimeError, KeyError, ImportError) as exc:
        print('Kristal Integration v11: FAIL: ' + str(exc), file=sys.stderr)
        sys.exit(1)
