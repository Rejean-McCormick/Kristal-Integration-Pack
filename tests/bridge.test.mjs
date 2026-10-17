import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {snapshotState,baseUrl,requireContextPack,requireCapabilities,options} from '../tools/kristal-bridge.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const checkout=process.env.KONSTELLATION_ROOT;
async function mockEndpoint() {
  const state={schema_version:'6.0',artifact_type:'kristal_state',artifact_status:'working',created_at:'2026-10-08T00:00:00Z',assertions:[],provenance:[],extensions:{kristal_v7:{generated_from:{source_state_refs:['sha256:source-one']}}}};
  const pack={protocol:'kompiler.context-pack',version:'1.1',context_pack_id:'pack:mock-test',records:[],sources:[],execution:{run_id:'run:mock-test'}};
  const received=[];
  const server=http.createServer(async(req,res)=>{
    const chunks=[];for await(const c of req)chunks.push(c);
    let payload;try {payload=JSON.parse(Buffer.concat(chunks).toString('utf8')||'null');}catch{}
    received.push({path:req.url,authorization:req.headers.authorization||null,body:payload});
    let val;
    if(req.url==='/v1/capabilities')val={protocol:'kompiler.capabilities',version:'1.1',targets:[]};
    else if(req.url==='/v1/queries/validate')val={valid:true};
    else if(req.url==='/v1/runs')val=pack;
    else if(req.url==='/v1/projections/v6')val=state;
    else {res.writeHead(404);res.end();return;}
    res.setHeader('Content-Type','application/json');res.end(JSON.stringify(val));
  });
  await new Promise(ok=>server.listen(0,'127.0.0.1',ok));
  return {server,url:`http://127.0.0.1:${server.address().port}`,received,pack,state};
}
function cli(cmd,args,env={}) {
  return new Promise(resolve => {
    const proc=spawn(process.execPath,[path.join(root,'tools/kristal-bridge.mjs'),cmd,...args],{env:{...process.env,...env}});
    let stdout='',stderr='';
    proc.stdout.on('data',c=>stdout+=c);proc.stderr.on('data',c=>stderr+=c);
    proc.on('close',code=>resolve({status:code,stdout,stderr}));
  });
}

test('CLI refuses non-loopback upstreams and unsupported v6 payloads',()=>{
  assert.throws(()=>snapshotState({schema_version:'9.0',assertions:[],provenance:[]}));
  assert.equal(snapshotState({schema_version:'6.0',artifact_type:'kristal_state',assertions:[],provenance:[]}).length,0);
  const old=process.env.KOMPILER_URL;
  try {process.env.KOMPILER_URL='http://example.com:7788';assert.throws(baseUrl,/loopback|local/);}
  finally {if(old===undefined)delete process.env.KOMPILER_URL;else process.env.KOMPILER_URL=old;}
});
test('doctor, run and project generate pinned Konstellation backend and receipt',async t=>{
  const mock=await mockEndpoint();t.after(()=>mock.server.close());
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'kristal-bridge-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const env={KOMPILER_URL:mock.url,KOMPILER_TOKEN:'do-not-export-token'};
  const queryFile=path.join(dir,'query.json'), packFile=path.join(dir,'context.json'), out=path.join(dir,'projection');
  fs.writeFileSync(queryFile,JSON.stringify({protocol:'kompiler.query',version:'1.1',request_id:'t',operations:[{id:'a',target:'Mock',operation:'find'}]}));
  for(const [cmd,args] of [['doctor',[]],['run',['--query',queryFile,'--out',packFile]],['project',['--pack',packFile,'--out',out]]]){
    const r=await cli(cmd,args,env); assert.equal(r.status,0,`${cmd} failed: ${r.stderr}`);
  }
  assert.equal(JSON.parse(fs.readFileSync(packFile)).context_pack_id,mock.pack.context_pack_id);
  const conf=JSON.parse(fs.readFileSync(path.join(out,'konstellation-backend.json')));
  assert.equal(conf.adapter,'kristal-state-v6');
  assert.equal(conf.compatibilityMode,'strict');
  assert.match(conf.stateSha256,/^[a-f0-9]{64}$/);
  const receipt=JSON.parse(fs.readFileSync(path.join(out,'bridge-receipt.json')));
  assert.deepEqual(receipt.sourceStateRefs,['sha256:source-one']);
  assert.ok(!JSON.stringify(receipt).includes(env.KOMPILER_TOKEN));
  assert.ok(mock.received.every(x=>x.authorization==='Bearer '+env.KOMPILER_TOKEN));
  const repeat=await cli('project',['--pack',packFile,'--out',out],env);
  assert.notEqual(repeat.status,0,'must not overwrite a nonempty output');
});
test('author blocks write by default; inspection invokes existing Local Kit',async()=>{
  const kit=process.env.KRISTAL_KIT_ROOT;
  if(!kit) return;
  const tool=path.join(kit,'tools','kristal.py'), workspace=path.join(kit,'examples','demo-open');
  const args=['--tool',tool,'--workspace',workspace];
  let r=await cli('author',['--action','build-v9',...args]);
  assert.notEqual(r.status,0);assert.match(r.stderr,/Write denied/);
  r=await cli('author',['--action','inspect',...args],{KRISTAL_PYTHON:'python'});
  assert.equal(r.status,0,r.stderr);assert.match(r.stdout,/workspace|kristal/i);
});
test('upstream limits and denylist on installed Bridge module',async t=>{
  if(!checkout)return;
  const {KompilerBridge,safeKompilerEndpoint}=await import(path.join(checkout,'server','integrations','kompiler-bridge.mjs'));
  assert.throws(()=>safeKompilerEndpoint({KONSTELLATION_KOMPILER_URL:'https://remote.invalid'}));
  assert.throws(()=>safeKompilerEndpoint({KONSTELLATION_KOMPILER_URL:'http://localhost:7788/private'}));
  const mock=await mockEndpoint();t.after(()=>mock.server.close());
  const client=new KompilerBridge({url:mock.url,maxBytes:1024});
  const caps=await client.capabilities();assert.equal(caps.protocol,'kompiler.capabilities');
  await assert.rejects(()=>client.request('POST','/v1/runs/evil',{a:1}),{code:'ACCESS_DENIED'});
  const limited=new KompilerBridge({url:mock.url,maxBytes:15});
  await assert.rejects(()=>limited.capabilities(),{code:'UPSTREAM_LIMIT'});
});

test('C5: rejects fake protocol, unsupported version and incomplete Context Packs',()=>{
  const baseline={protocol:'kompiler.context-pack',version:'1.1',context_pack_id:'pack:valid',records:[],execution:{run_id:'run:ok'}};
  assert.doesNotThrow(()=>requireContextPack(baseline));
  for(const fake of [
    {...baseline,protocol:'kristal_state'},
    {...baseline,version:'2.0'},
    {...baseline,execution:null},
    {...baseline,records:null},
    {...baseline,context_pack_id:''},
  ]) assert.throws(()=>requireContextPack(fake),/Context Pack/);
  assert.doesNotThrow(()=>requireCapabilities({protocol:'kompiler.capabilities',version:'1.1',targets:[]}));
  assert.throws(()=>requireCapabilities({protocol:'kompiler.capabilities',version:'9.9',targets:[]}),/Incompatible/);
});

test('strict CLI flags and protocol target identifiers are fail-closed',()=>{
  assert.throws(()=>options(['doctor','--execute','1']),/Unsupported option/);
  assert.throws(()=>options(['project','--shell','yes']),/Unsupported option/);
  assert.throws(()=>options(['run','--query','x','--query','y']),/Repeated option/);
  assert.throws(()=>requireCapabilities({protocol:'kompiler.capabilities',version:'1.1',targets:[{}]}),/target identifier/);
});
