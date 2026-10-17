#!/usr/bin/env node
/** Read-only-by-default Kompiler -> Konstellation bridge CLI; Node 22+. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const knownCommands = new Set(['doctor','run','project','author','v11','v11-handoff']);
const SUPPORTED_PROTOCOL_VERSIONS = new Set(['1.0', '1.1']);
function requireContextPack(pack) {
  if (!pack || pack.protocol !== 'kompiler.context-pack' || !SUPPORTED_PROTOCOL_VERSIONS.has(pack.version)
    || typeof pack.context_pack_id !== 'string' || !pack.context_pack_id
    || !Array.isArray(pack.records) || !pack.execution || typeof pack.execution !== 'object')
    throw Error('Unrecognized Kompiler Context Pack (protocol 1.0/1.1 required)');
  return pack;
}
function requireCapabilities(cap) {
  if (!cap || cap.protocol !== 'kompiler.capabilities' || !SUPPORTED_PROTOCOL_VERSIONS.has(cap.version)
    || !Array.isArray(cap.targets)) throw Error('Incompatible Kompiler capabilities (protocol 1.0/1.1 required)');
  if(cap.targets.some(t => !t || typeof t.target_id !== 'string' || !t.target_id))
    throw Error('Invalid Kompiler target identifier in capabilities');
  return cap;
}
function options(argv) {
  const [command,...rest] = argv;
  if (!knownCommands.has(command)) throw Error('Usage: doctor | run --query FILE --out FILE | project --pack FILE --out DIR [--surface ID] | author ... | v11 --operation check|coverage|view ... | v11-handoff --framework DIR --registry FILE --crosswalk FILE --catalog FILE [--graph FILE --locales TAGS] [--kit-candidate yes] [--dik-job FILE] [--out FILE]');
  const flags={};
  for(let i=0;i<rest.length;i+=2) {
    const key=rest[i];
    if(!key?.startsWith('--') || rest[i+1]===undefined || rest[i+1].startsWith('--')) throw Error('Invalid option: '+key);
    if (Object.hasOwn(flags,key.slice(2))) throw Error('Repeated option: '+key);
    flags[key.slice(2)]=rest[i+1];
  }
  const allowed={doctor:[],run:['query','out'],project:['pack','out','surface'],author:['action','tool','workspace','confirm'],v11:['operation','framework','registry','graph','crosswalk','catalog','locale','locales','out'],
    'v11-handoff':['framework','registry','graph','crosswalk','catalog','locales','kit-candidate','dik-job','out']};
  for(const key of Object.keys(flags))if(!allowed[command].includes(key))throw Error('Unsupported option for '+command+': --'+key);
  return {command,flags};
}
function baseUrl() {
  const raw=process.env.KOMPILER_URL||'http://127.0.0.1:7788';
  const u=new URL(raw);
  if(u.protocol!=='http:' || !['127.0.0.1','localhost','[::1]'].includes(u.hostname) || u.username || u.password || u.search || u.hash || !['/',''].includes(u.pathname))
    throw Error('KOMPILER_URL must be local loopback HTTP without a URL path or credentials.');
  return u.origin;
}
async function api(method,endpoint,data) {
  const headers={Accept:'application/json'};
  if(data!==undefined)headers['Content-Type']='application/json';
  if(process.env.KOMPILER_TOKEN)headers.Authorization='Bearer '+process.env.KOMPILER_TOKEN;
  const res=await fetch(baseUrl()+endpoint,{method,headers,signal:AbortSignal.timeout(30000),redirect:'error',...(data===undefined?{}:{body:JSON.stringify(data)})});
  const limit=8_000_000;
  if(Number(res.headers.get('content-length')||0)>limit)throw Error('Oversized Kompiler response');
  if(!res.headers.get('content-type')?.includes('application/json'))throw Error('Kompiler returned an invalid content type');
  let chunks=[],total=0;
  for await (const chunk of res.body) {total+=chunk.length;if(total>limit) throw Error('Kompiler response exceeds 8 MB');chunks.push(chunk);}
  const json=JSON.parse(Buffer.concat(chunks).toString('utf8'));
  if(!res.ok) throw Error(`Kompiler HTTP ${res.status}, code ${String(json?.code||'UNKNOWN')}`);
  return json;
}
function ensureJson(p) {return JSON.parse(fs.readFileSync(path.resolve(p),'utf8'));}
function jsonfile(p,x) {fs.writeFileSync(p,JSON.stringify(x,null,2)+'\n',{encoding:'utf8',flag:'wx'});}
function snapshotState(state) {
  if(!state || state.schema_version!=='6.0' || state.artifact_type!=='kristal_state'
    || !Array.isArray(state.assertions) || !Array.isArray(state.provenance))
    throw Error('Projection is not a compatible v6 state.');
  const refs=state.extensions?.kristal_v7?.generated_from?.source_state_refs;
  return Array.isArray(refs)?refs:[];
}
async function main() {
  const {command,flags}=options(process.argv.slice(2));
  if(command==='doctor') {
    const cap=requireCapabilities(await api('GET','/v1/capabilities'));
    console.log(JSON.stringify({kompilerProtocol:cap.protocol,version:cap.version,
      targetIds:(cap.targets||[]).map(x=>x.target_id),
      note:'Legacy Kompiler protocol 1.0/1.1; not a v11 semantic graph projection. Use the separate v11 command.'},null,2));return;
  }
  if(command==='run') {
    if(!flags.query || !flags.out)throw Error('run requires --query and --out');
    const query=ensureJson(flags.query);
    const valid=await api('POST','/v1/queries/validate',query);
    if(valid.valid!==true)throw Error('Kompiler rejected the query plan');
    const pack=await api('POST','/v1/runs',query);
    requireContextPack(pack);
    const output=path.resolve(flags.out);
    fs.mkdirSync(path.dirname(output),{recursive:true});jsonfile(output,pack);
    console.log(JSON.stringify({file:output,context_pack_id:pack.context_pack_id,recordCount:pack.records.length},null,2));return;
  }
  if(command==='project') {
    if(!flags.pack||!flags.out)throw Error('project requires --pack and --out');
    const original=fs.readFileSync(path.resolve(flags.pack));
    const pack=JSON.parse(original.toString('utf8'));
    requireContextPack(pack);
    const state=await api('POST','/v1/projections/v6',{context_pack:pack,...(flags.surface?{surface_id:flags.surface}:{}),recipe_id:'recipe:konstellation-bridge'});
    const refs=snapshotState(state);
    const output=path.resolve(flags.out);
    if(fs.existsSync(output))throw Error('Output directory already exists; refusing to overwrite');
    fs.mkdirSync(path.dirname(output),{recursive:true});
    const staging=fs.mkdtempSync(path.join(path.dirname(output),'.integration-projection-'));
    const stateFile='kristal-projection-v6.json';
    try {
    jsonfile(path.join(staging,stateFile),state);
    const stateBytes=fs.readFileSync(path.join(staging,stateFile));
    jsonfile(path.join(staging,'konstellation-backend.json'),{
      adapter:'kristal-state-v6',directory:'.',state:stateFile,stateSha256:sha256(stateBytes),
      compatibilityMode:'strict',
    });
    jsonfile(path.join(staging,'bridge-receipt.json'),{
      profile:'kristal-integration-projection/0.1',sourceContextPackId:pack.context_pack_id,
      sourceContextPackFileSha256:sha256(original),projectionFileSha256:sha256(stateBytes),
      sourceStateRefs:refs,
      limits:'Only a derived reading surface: not a semantic-state commitment or proof of full coverage.',
    });
    if(fs.existsSync(output))throw Error('Output directory appeared during projection; refusing to overwrite');
    fs.renameSync(staging,output);
    } catch(err) {fs.rmSync(staging,{recursive:true,force:true});throw err;}
    console.log(JSON.stringify({config:path.join(output,'konstellation-backend.json'),
      sourceStateRefs:refs, note:'Set KONSTELLATION_BACKEND_CONFIG and restart Konstellation to use this derived view.'},null,2));return;
  }
  if(command==='v11-handoff') {
    if(['framework','registry','crosswalk','catalog'].some(k=>!flags[k]))
      throw Error('v11-handoff requires --framework, --registry, --crosswalk and --catalog');
    if(flags['kit-candidate']!==undefined && flags['kit-candidate']!=='yes')
      throw Error('v11-handoff --kit-candidate must be yes');
    if(flags['dik-job'] && flags['kit-candidate']!=='yes')
      throw Error('v11-handoff diK job receipt requires --kit-candidate yes');
    if(flags.locales && !flags.graph)
      throw Error('v11-handoff --locales requires --graph');
    const script=path.join(path.dirname(fileURLToPath(import.meta.url)),'v11_handoff.py');
    const args=[script,...['framework','registry','crosswalk','catalog','graph','locales','dik-job','out']
      .flatMap(k=>flags[k]===undefined?[]:['--'+k,flags[k]]),
      ...(flags['kit-candidate']==='yes'?['--kit-import-candidate']:[])];
    const r=spawnSync(process.env.KRISTAL_PYTHON||'python',args,{
      shell:false,encoding:'utf8',maxBuffer:16_000_000,timeout:120000,
      env:{...process.env,PYTHONUTF8:'1'},
    });
    if(r.error)throw r.error;
    if(r.stdout)process.stdout.write(r.stdout);
    if(r.stderr)process.stderr.write(r.stderr);
    if(r.status!==0)throw Error(`Pinned Framework v11 handoff: exit ${r.status}`);
    return;
  }
  if(command==='v11') {
    const mode=flags.operation;
    if(!['check','coverage','view'].includes(mode) ||
       ['framework','registry','graph','crosswalk','catalog'].some(k=>!flags[k]))
      throw Error('v11 requires --operation check|coverage|view, --framework, --registry, --graph, --crosswalk and --catalog');
    if(mode==='view' ? (!flags.locale || flags.locales) : (mode==='coverage' ? Boolean(flags.locale) : Boolean(flags.locale||flags.locales)))
      throw Error('Invalid v11 locale options for operation '+mode);
    const script=path.join(path.dirname(fileURLToPath(import.meta.url)),'v11_integration.py');
    const args=[script,mode, ...['framework','registry','graph','crosswalk','catalog','locale','locales','out']
      .flatMap(k=>flags[k]===undefined?[]:['--'+k,flags[k]])];
    const r=spawnSync(process.env.KRISTAL_PYTHON||'python',args,{
      shell:false,encoding:'utf8',maxBuffer:16_000_000,timeout:120000,
      env:{...process.env,PYTHONUTF8:'1'},
    });
    if(r.error)throw r.error;
    if(r.stdout)process.stdout.write(r.stdout);
    if(r.stderr)process.stderr.write(r.stderr);
    if(r.status!==0)throw Error(`Pinned Framework v11 ${mode}: exit ${r.status}`);
    return;
  }
  if(command==='author') {
    const action=flags.action;
    const allowed=new Set(['inspect','status','check','read-surface','build-v9','publish-v9']);
    if(!allowed.has(action) || !flags.tool || !flags.workspace)throw Error('author requires --action inspect|status|check|read-surface|build-v9|publish-v9 --tool FILE --workspace DIR');
    const writes=new Set(['build-v9','publish-v9']);
    if(writes.has(action) && !(process.env.KRISTAL_ALLOW_WRITE==='1' && flags.confirm===action))
      throw Error('Write denied: requires KRISTAL_ALLOW_WRITE=1 and --confirm '+action);
    const tool=fs.realpathSync(path.resolve(flags.tool));
    const workspace=fs.realpathSync(path.resolve(flags.workspace));
    if(!fs.statSync(tool).isFile() || !fs.statSync(workspace).isDirectory())throw Error('Tool or workspace not found');
    const python=process.env.KRISTAL_PYTHON||'python';
    // Controlled positional arguments, no arbitrary shell string, no user-supplied command flags.
    const args=[tool,action,workspace, ...(action==='read-surface'?['--require-ready']:[])];
    const r=spawnSync(python,args,{encoding:'utf8',shell:false,maxBuffer:2_000_000,timeout:60000,
      env:{...process.env,PYTHONUTF8:'1'}});
    if(r.error)throw r.error;
    if(r.stdout)process.stdout.write(r.stdout);
    if(r.stderr)process.stderr.write(r.stderr);
    if(r.status!==0)throw Error(`Local Kit ${action}: exit ${r.status}`);
    return;
  }
}
if(process.argv[1] && fileURLToPath(import.meta.url)===path.resolve(process.argv[1])) {
  main().catch(err=>{console.error('ERROR:',err.message);process.exitCode=1;});
}
export {api,snapshotState,baseUrl,options,requireContextPack,requireCapabilities};
