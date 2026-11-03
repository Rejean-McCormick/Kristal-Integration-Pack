"""Coordinated, read-only Spek ecosystem acceptance preflight.

The command exercises the *actual* CLIs from separate local repository roots.
It performs no GF compilation, networking, Git operations, approval or write to
any Kristal. A private Spek lock is written only to a temporary directory.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def _run(argv: list[str], repo: Path, extra_pythonpath: str | None = None) -> dict:
    env=os.environ.copy()
    if extra_pythonpath:
        env['PYTHONPATH']=str(repo/extra_pythonpath)+os.pathsep+env.get('PYTHONPATH','')
    else:
        env['PYTHONPATH']=str(repo)+os.pathsep+env.get('PYTHONPATH','')
    try:
        proc=subprocess.run([sys.executable,*argv],cwd=repo,env=env,text=True,
                            capture_output=True,encoding='utf-8',errors='replace',timeout=90,check=False)
    except (OSError,subprocess.TimeoutExpired):
        return {'status':'BLOCKED','diagnostic':'process_missing_or_timed_out'}
    # Avoid exposing raw private JSON and assertion IDs in reports.
    return {'status':'PASS' if proc.returncode==0 else 'BLOCKED',
            'exit_code':proc.returncode,
            'diagnostic': ('ok' if proc.returncode==0 else _safe_reason(proc.stderr or proc.stdout))}


def _safe_reason(raw: str) -> str:
    from re import search
    # Known lock failures, without exposing private path/identifiers in report.
    low=raw.lower()
    if 'ancré' in low or 'assertion' in low and 'source' in low:return 'source_binding_incomplete_or_mismatch'
    if 'pgf' in low or 'runtime' in low:return 'runtime_unavailable_or_unqualified'
    if 'verrou' in low or 'lock' in low:return 'private_lock_failed'
    if 'obligation' in low:return 'semantik_obligation_invalid'
    if 'relation' in low:return 'rhetorical_relation_not_supported'
    return 'contract_or_environment_rejected'


def audit(*,spek:Path, manager:Path, semantik:Path, runtime:Path, arketype:Path,
          framework:Path, public:Path, instance:Path, requests:Path,
          graph:Path, identity_map:Path, runtime_root:Path,
          language:str='fr',profile:str='agriculture-reference-1') -> dict:
    repos={'spek':spek,'manager':manager,'semantik':semantik,'runtime':runtime,
           'arketype':arketype,'framework':framework,'public':public}
    repos={k:Path(v).resolve() for k,v in repos.items()}
    steps={}
    for key,root in repos.items():
        if not root.is_dir():
            steps[key+'_presence']={'status':'BLOCKED','diagnostic':'repository_directory_missing'}
    with tempfile.TemporaryDirectory(prefix='spek-private-interop-') as td:
        lock_path=Path(td)/'private-lock.json'
        if not steps:
            steps['spek_lock']=_run(['-m','spek','compose-lock',
                        '--instance',str(Path(instance).resolve()),'--library-root',str(repos['spek']),
                        '--requests-dir',str(Path(requests).resolve()),
                        '--language',language,'--source-graph',str(Path(graph).resolve()),
                        '--identity-map',str(Path(identity_map).resolve()),
                        '--out',str(lock_path)],repos['spek'])
            if steps['spek_lock']['status']=='PASS':
                steps['spek_verify']=_run(['-m','spek','compose-verify-lock','--lock',str(lock_path),
                            '--instance',str(Path(instance).resolve()),'--library-root',str(repos['spek']),
                            '--requests-dir',str(Path(requests).resolve()),
                            '--source-graph',str(Path(graph).resolve()),'--identity-map',str(Path(identity_map).resolve())],repos['spek'])
                steps['manager_intake']=_run(['-m','kristal_manager.private_spek_intake',
                            '--lock',str(lock_path),'--graph',str(Path(graph).resolve()),
                            '--identity-map',str(Path(identity_map).resolve())],repos['manager'])
                steps['semantik_requests']=_run(['tools/verify_spek_handoff.py',
                            '--lock',str(lock_path),'--requests-dir',str(Path(requests).resolve())],
                            repos['semantik'],extra_pythonpath='src')
            else:
                for key in ('spek_verify','manager_intake','semantik_requests'):
                    steps[key]={'status':'NOT_RUN','diagnostic':'blocked_by_spek_private_lock'}
        if 'runtime_presence' not in steps:
            steps['runtime_artifact_readiness']=_run(['-m','semantik_runtime_orchestrator.cli','inspect-profile',
                        '--runtime-root',str(Path(runtime_root).resolve()),'--language',language,
                        '--profile',profile],repos['runtime'],extra_pythonpath='src')
        if 'arketype_presence' not in steps:
            steps['arketype_suggestions']=_run(['spek_guidance.py','--spek-inventory',
                        str(repos['spek']/'template_library/rhetorical/research-inventory.json')],
                        repos['arketype'])
        if 'framework_presence' not in steps:
            p=repos['framework']/'profiles/spek/private-editorial-handoff.schema.json'
            steps['framework_schema']={'status':'PASS' if p.is_file() and not p.is_symlink() else 'BLOCKED',
                                       'diagnostic':'schema_present' if p.is_file() else 'schema_missing'}
        if 'public_presence' not in steps:
            p=repos['public']/'tools/wiki_deploy.py'
            steps['public_gate_present']={'status':'PASS' if p.is_file() and not p.is_symlink() else 'BLOCKED',
                                          'diagnostic':'gate_present_not_invoked' if p.is_file() else 'gate_missing'}
    return {'format':'kristal.spek-ecosystem-readiness/1.0',
            'status':'PASS_CONTRACT_PREFLIGHT_ONLY' if all(x['status']=='PASS' for x in steps.values()) else 'BLOCKED',
            'steps':steps,'real_gf_pgf_article_produced':False,
            'publication_approved':False,'git_or_network_operations':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Audit coordonné des huit dépôts, sans publication')
    for key in ('spek','manager','semantik','runtime','arketype','framework','public','instance',
                'requests','graph','identity-map','runtime-root'):
        parser.add_argument('--'+key,required=True,type=Path)
    parser.add_argument('--language',default='fr')
    parser.add_argument('--profile',default='agriculture-reference-1')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args(argv)
    kwargs={key.replace('-','_'):getattr(args,key.replace('-','_')) for key in (
        'spek','manager','semantik','runtime','arketype','framework','public','instance',
        'requests','graph','identity-map','runtime-root','language','profile')}
    report=audit(**kwargs)
    data=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    if args.out:
        if args.out.is_symlink() or args.out.exists():parser.error('No existing output may be overwritten')
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(data,encoding='utf-8')
    print(data)
    return 0 if report['status']=='PASS_CONTRACT_PREFLIGHT_ONLY' else 2

if __name__=='__main__':raise SystemExit(main())
