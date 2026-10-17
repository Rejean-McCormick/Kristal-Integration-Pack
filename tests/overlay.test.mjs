/** Test candidate overlay in isolation; no installed Konstellation files modified. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,cpSync,rmSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const source=path.join(root,'overlay/server/integrations/kompiler-bridge.mjs');
function fixture(){
 const temp=mkdtempSync(path.join(os.tmpdir(),'integration-overlay-'));
 const server=path.join(temp,'server','integrations');mkdirSync(server,{recursive:true});
 cpSync(source,path.join(server,'kompiler-bridge.mjs'));
 writeFileSync(path.join(temp,'server','errors.mjs'),`export function fail(code,message,status=400){const err=new Error(message);err.code=code;err.status=status;throw err;}`);
 return {temp,url:pathToFileURL(path.join(server,'kompiler-bridge.mjs')).href};
}
function response(json,headers={'content-type':'application/json'}){
 return new Response(JSON.stringify(json),{headers,status:200});
}

test('candidate overlay permits only loopback and allowed upstream routes',async(t)=>{
 const f=fixture();t.after(()=>rmSync(f.temp,{recursive:true,force:true}));
 const {KompilerBridge,safeKompilerEndpoint}=await import(f.url);
 for(const url of ['https://remote.example','http://example.com:7788','http://localhost:7788/path','http://user:password@localhost:7788']){
   assert.throws(()=>new KompilerBridge({url}),{code:'INVALID_CONFIG'});
 }
 assert.equal(safeKompilerEndpoint({KONSTELLATION_KOMPILER_URL:'http://127.0.0.1:7788'}),'http://127.0.0.1:7788');
 const calls=[];
 const client=new KompilerBridge({url:'http://127.0.0.1:7788',fetcher:async(url,opts)=>{calls.push([url,opts]);return response({protocol:'kompiler.capabilities',version:'1.1',targets:[{target_id:'demo'}]});}});
 const v=await client.capabilities();assert.equal(v.targets[0].target_id,'demo');
 assert.equal(calls[0][1].redirect,'error');
 await assert.rejects(()=>client.request('POST','/v1/files',{file:'../../etc/passwd'}),{code:'ACCESS_DENIED'});
 assert.equal(calls.length,1);
});

test('candidate overlay rejects foreign protocols, incomplete results and bad projections',async(t)=>{
 const f=fixture();t.after(()=>rmSync(f.temp,{recursive:true,force:true}));
 const {KompilerBridge}=await import(f.url);
 let next={protocol:'wrong',version:'1.1',targets:[]};
 const client=new KompilerBridge({url:'http://127.0.0.1:7788',fetcher:async()=>response(next)});
 await assert.rejects(()=>client.capabilities(),{code:'UPSTREAM_INVALID'});
 next={protocol:'kompiler.capabilities',version:'1.1',targets:[{}]};
 await assert.rejects(()=>client.capabilities(),{code:'UPSTREAM_INVALID'});
 next={valid:'yes'};
 await assert.rejects(()=>client.validate({}),{code:'UPSTREAM_INVALID'});
 next={protocol:'kompiler.context-pack',version:'9.9',context_pack_id:'pack:bad',records:[],execution:{}};
 await assert.rejects(()=>client.run({}),{code:'UPSTREAM_INVALID'});
 next={schema_version:'9.0',artifact_type:'kristal_state',assertions:[],provenance:[]};
 await assert.rejects(()=>client.projection({protocol:'kompiler.context-pack',version:'1.1'}),{code:'UPSTREAM_INVALID'});
 await assert.rejects(()=>client.projection({protocol:'other',version:'1.1'}),{code:'INVALID_QUERY'});
});

test('candidate overlay enforces body length independent of Content-Length',async(t)=>{
 const f=fixture();t.after(()=>rmSync(f.temp,{recursive:true,force:true}));
 const {KompilerBridge}=await import(f.url);
 const c=new KompilerBridge({url:'http://localhost:7788',maxBytes:40,fetcher:async()=>response({protocol:'kompiler.capabilities',version:'1.1',targets:[],extra:'y'.repeat(200)})});
 await assert.rejects(()=>c.capabilities(),{code:'UPSTREAM_LIMIT'});
});
