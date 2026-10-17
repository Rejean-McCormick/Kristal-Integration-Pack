#!/usr/bin/env python3
"""Read-only, pinned Framework draft.4 preflight for diK -> Authoring Kit v11.

This tool never registers, selects, activates, publishes or rewrites artifacts.
It refuses unknown diK job receipts rather than inferring identity from labels.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import json
from pathlib import Path
import subprocess
import sys

from v11_integration import IntegrationError, emit, read_input, sha, verify_framework

PROFILE = 'kristal.integration.dik-authoring-handoff/0.3-candidate'
JOB_PROFILE = 'dik.large-import/1.0-candidate'
FRAMEWORK_SCRIPT = 'tools/v11/interop_preflight.py'


def check_job(*, job_file: Path, catalog: Path, registry: Path, crosswalk: Path) -> dict:
    """Confirm an alpha.7 local import's receipt binds to the exact catalog.

    This is not an upstream Wikidata signature, proof of reviewer approval, or
    validation of source dump bytes (which may be unavailable to the reader).
    """
    job_file = Path(job_file).resolve()
    catalog = Path(catalog).resolve()
    if job_file.parent != catalog.parent or job_file.name != 'dik-job.json':
        raise IntegrationError('diK job receipt must sit beside catalog.json')
    if catalog.name != 'catalog.json':
        raise IntegrationError('Expected an immutable diK catalog.json')
    record = read_input(job_file)
    pins = record.get('source_pins')
    if record.get('profile') != JOB_PROFILE or not isinstance(pins, dict):
        raise IntegrationError('Unsupported or incomplete diK alpha.7 job receipt')
    if record.get('catalog_sha256') != sha(catalog):
        raise IntegrationError('diK catalog digest mismatch')
    if pins.get('registry_sha256') != sha(registry) or pins.get('crosswalk_sha256') != sha(crosswalk):
        raise IntegrationError('diK receipt registry/crosswalk digest mismatch')
    cat = read_input(catalog)
    if pins.get('namespace') != cat.get('namespace_id'):
        raise IntegrationError('diK job namespace mismatch')
    langs = [entry['tag'] for entry in cat['languages']]
    if pins.get('locales') != langs:
        raise IntegrationError('diK job locale list mismatch')
    if pins.get('snapshot') is None or cat.get('catalog_id') != 'wikidata-import-' + pins['snapshot']:
        raise IntegrationError('diK job snapshot mismatch')
    if record.get('upstream_verified') != pins.get('upstream_verified'):
        raise IntegrationError('diK receipt checksum attestation mismatch')
    if pins.get('transform') != 'wikidata-large-import-1.0.0-alpha.7':
        raise IntegrationError('Unsupported diK import transformation')
    if not isinstance(pins.get('dump_sha256'), str) or not re.fullmatch('[0-9a-f]{64}',pins['dump_sha256']):
        raise IntegrationError('diK receipt missing source digest')
    key=hashlib.sha256(json.dumps(pins,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
    if record.get('idempotency_key') != key or job_file.parent.name != key:
        raise IntegrationError('diK receipt idempotency key or snapshot directory mismatch')
    return {
        'profile': record['profile'],
        'sha256': sha(job_file),
        'catalog_sha256': record['catalog_sha256'],
        'source_dump_sha256': pins['dump_sha256'],
        'upstream_sha256_independently_pinned': pins['upstream_verified'],
        'note': 'Digest binding only. A source SHA-256 is not proof of origin or semantic equivalence.',
    }


def run(*, framework: Path, catalog: Path, registry: Path, crosswalk: Path,
        graph: Path | None = None, locales: list[str] | None = None,
        kit_import_candidate: bool = False, dik_job: Path | None = None) -> dict:
    fw = Path(framework).resolve()
    verify_framework(fw)
    if locales and graph is None:
        raise IntegrationError('Requested locales require --graph')
    if dik_job is not None and not kit_import_candidate:
        raise IntegrationError('A diK import receipt is valid only with --kit-import-candidate')
    receipt = None
    if dik_job is not None:
        receipt = check_job(job_file=dik_job,catalog=catalog,registry=registry,crosswalk=crosswalk)
    args = [sys.executable, str(fw/FRAMEWORK_SCRIPT), '--catalog', str(Path(catalog).resolve()),
            '--registry',str(Path(registry).resolve()),'--crosswalk',str(Path(crosswalk).resolve())]
    if graph is not None:args += ['--graph',str(Path(graph).resolve())]
    if locales:args += ['--locales',','.join(locales)]
    if kit_import_candidate:args.append('--kit-import-candidate')
    result = subprocess.run(args, capture_output=True, text=True, timeout=120, check=False)
    if result.returncode:
        raise IntegrationError('Pinned Framework interop preflight REFUSED: '+result.stderr.strip()[:1500])
    try:
        report = json.loads(result.stdout)
    except (ValueError,TypeError) as exc:
        raise IntegrationError('Invalid Framework preflight report') from exc
    if report.get('profile') != 'kristal.v11-dik-authoring-preflight/1.0-candidate' or report.get('status') != 'preflight_pass':
        raise IntegrationError('Unexpected Framework interop preflight profile/status')
    if (report.get('input_sha256',{}).get('catalog') != sha(catalog) or
        report.get('input_sha256',{}).get('registry') != sha(registry) or
        report.get('input_sha256',{}).get('crosswalk') != sha(crosswalk)):
        raise IntegrationError('Framework report input hash mismatch')
    return {'profile': PROFILE, 'status': 'preflight_pass',
            'framework_version':'11.0.0-draft.4', 'framework_preflight':report,
            'dik_job':receipt,
            'read_only':True, 'registered':False,'selected':False,'activated':False,
            'warning':'Reader-side validation only; Kit authoring, governance, diK import and canon remain separate authorities.'}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('framework','catalog','registry','crosswalk'):
        ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--graph',type=Path)
    ap.add_argument('--locales',help='Comma-separated locales, requires --graph')
    ap.add_argument('--dik-job',type=Path,help='Optional alpha.7 job receipt for an incoming Kit candidate')
    ap.add_argument('--kit-import-candidate',action='store_true')
    ap.add_argument('--out',type=Path,help='Create a new report (never overwrite)')
    args=ap.parse_args(argv)
    if args.locales is not None and (not args.locales or any(not x for x in args.locales.split(','))):
        ap.error('Invalid --locales')
    if args.out and args.out.resolve() in {Path(getattr(args,n)).resolve() for n in ('framework','catalog','registry','crosswalk','graph','dik_job') if getattr(args,n)}:
        ap.error('Output may not replace an input')
    try:
        result=run(framework=args.framework,catalog=args.catalog,registry=args.registry,
                   crosswalk=args.crosswalk,graph=args.graph,
                   locales=args.locales.split(',') if args.locales else None,
                   kit_import_candidate=args.kit_import_candidate,dik_job=args.dik_job)
        emit(result,args.out)
    except (IntegrationError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        raise SystemExit('Integration Pack v11 handoff REFUSED: '+str(exc)) from exc


if __name__=='__main__': main()
