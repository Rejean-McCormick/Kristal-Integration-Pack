from pathlib import Path
import os, sys, subprocess, socket, time, urllib.request, json, tempfile, argparse, hashlib, re
parser=argparse.ArgumentParser(description='C5 local HTTP read-only smoke test against a real Kompiler 0.8 runtime')
for opt in ('kompiler','framework','zoology'):parser.add_argument('--'+opt, required=True, type=Path)
parser.add_argument('--contract-set-sha256', default=os.environ.get('KOMPILER_KRISTAL_CONTRACT_SET_SHA256'),
                    help='Trusted SHA-256 of the selected Framework contract-set.json; required')
args=parser.parse_args()
if not args.contract_set_sha256 or not re.fullmatch(r'[0-9a-fA-F]{64}', args.contract_set_sha256):
    raise SystemExit('BLOCKED: explicitly trusted --contract-set-sha256 is required')
komp=args.kompiler.resolve();framework=args.framework.resolve();zoo=args.zoology.resolve()
integ=Path(__file__).resolve().parents[1]
for q in (komp/'src/kompiler',framework/'contracts/contract-set.json',zoo/'.kristal/v9/state-snapshot.json'):
 if not q.exists():raise SystemExit('MISSING_REQUIRED_SOURCE: '+str(q))
actual_pin=hashlib.sha256((framework/'contracts/contract-set.json').read_bytes()).hexdigest()
if actual_pin != args.contract_set_sha256.lower():
    raise SystemExit('BLOCKED: Framework contract-set SHA-256 does not match the trusted pin')
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
env=os.environ.copy();env.update(PYTHONPATH=str(komp/'src')+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else ''),KOMPILER_KRISTAL_STANDARD_ROOT=str(framework),KOMPILER_KRISTAL_ROOTS=str(zoo),KOMPILER_KRISTAL_CONTRACT_SET_SHA256=actual_pin,PYTHONDONTWRITEBYTECODE='1')
with tempfile.TemporaryDirectory(prefix='c5-http-') as td:
 proc=subprocess.Popen([sys.executable,'-m','uvicorn','kompiler.api.app:create_app','--factory','--host','127.0.0.1','--port',str(port),'--log-level','warning'],env=env,cwd=td,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  u=f'http://127.0.0.1:{port}/v1/capabilities'; cap=None
  for i in range(70):
   if proc.poll() is not None:
    print('SERVER_EXIT',proc.returncode);print(proc.stderr.read()[-2400:]);raise SystemExit(1)
   try: cap=json.load(urllib.request.urlopen(u,timeout=0.5));break
   except:time.sleep(0.15)
  if cap is None:raise SystemExit('SERVER START TIMEOUT')
  targets=[t['target_id'] for t in cap['targets']]
  print('LIVE_API',cap['protocol'],cap['version'],'targets',len(targets))
  zoo_target=next(t for t in targets if t.startswith('KristalV9:') and 'zoology' in t)
  print('ZOOLOGY_TARGET',zoo_target)
  cli_env=env.copy();cli_env.update(KOMPILER_URL=f'http://127.0.0.1:{port}')
  d=subprocess.run(['node',str(integ/'tools/kristal-bridge.mjs'),'doctor'],env=cli_env,capture_output=True,text=True,timeout=30)
  print('BRIDGE_DOCTOR',d.returncode,'OUTPUT',d.stdout[:230])
  q={'protocol':'kompiler.query','version':'1.1','request_id':'c5-live-http-zoology','topic':'zoology','operations':[{'id':'read-state','target':zoo_target,'operation':'state','params':{}}]}
  (Path(td)/'query.json').write_text(json.dumps(q),encoding='utf8')
  r=subprocess.run(['node',str(integ/'tools/kristal-bridge.mjs'),'run','--query',str(Path(td)/'query.json'),'--out',str(Path(td)/'context-pack.json')],env=cli_env,capture_output=True,text=True,timeout=30)
  print('BRIDGE_RUN',r.returncode,'OUT',r.stdout[:300],'ERR',r.stderr[:1200])
  if r.returncode!=0:raise SystemExit(1)
  pack=json.loads((Path(td)/'context-pack.json').read_text())
  print('CONTEXT_PACK',pack['protocol'],pack['version'],'records',len(pack['records']),'provenance_targets',list(pack['provenance'].get('targets',{}))[:3]);print('STATE_SHA256_REFERENCE_FOUND', '2503493eed8b2515107f9c32eed48286845f5468838ad3ae7b4a8f66a65f2ac8' in json.dumps(pack))
  assert '2503493eed8b2515107f9c32eed48286845f5468838ad3ae7b4a8f66a65f2ac8' in json.dumps(pack)
 finally:
  proc.terminate()
  try:proc.communicate(timeout=4)
  except:proc.kill()
