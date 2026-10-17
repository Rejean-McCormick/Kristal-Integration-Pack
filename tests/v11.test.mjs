import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {options} from '../tools/kristal-bridge.mjs';
import {requireKristalV11ReadView} from '../overlay/server/integrations/kristal-v11-read-view.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const fakeSha='a'.repeat(64);
const model={
 profile:'kristal.integration.read-view/v11.0-draft.1',derived_only:true,
 source:{namespace_id:'demo',graph_id:'g',framework_version:'11.0.0-draft.4',
  graph_sha256:fakeSha,registry_sha256:fakeSha,crosswalk_sha256:fakeSha,catalog_sha256:fakeSha},
 requested_locale:'fr-CA',coverage_counts:{direct:0,fallback:1,missing:1},
 presentation:[
   {kind:'entity',semantic_id:'KQ1',lexical:{status:'fallback',term:'Mot',effective_locale:'fr',layer_id:'curated'}},
   {kind:'property',semantic_id:'KP2',lexical:{status:'missing'}}],
 assertions:[{id:'KA1',subject:'KQ1',predicate:'KP2',object:{kind:'literal',datatype:'string',value:'citation'},sources:['KS3']}],
};
const clone=x=>JSON.parse(JSON.stringify(x));
test('v11 reader keeps prior draft.3 derived views readable without changing canon',()=>{
 const prior=clone(model);prior.source.framework_version='11.0.0-draft.3';
 assert.equal(requireKristalV11ReadView(prior).source.framework_version,'11.0.0-draft.3');
 prior.source.framework_version='11.0.0-draft.5';
 assert.throws(()=>requireKristalV11ReadView(prior),/Invalid v11/);
});
test('v11 read-view allows terms only in presentation, literal quotes remain values',()=>{
 assert.equal(requireKristalV11ReadView(clone(model)).presentation[0].lexical.term,'Mot');
 for(const fault of [
   v=>{v.assertions[0].predicate='hasAuthor';},
   v=>{v.presentation[0].semantic_id='Q1';},
   v=>{v.presentation[0].accepted_external_exact={system:'wikidata',id:'P12'};},
   v=>{v.presentation[1].lexical.term='guessed translation';},
   v=>{v.source.graph_sha256='forged';},
   v=>{v.coverage_counts.fallback=2;},
   v=>{v.presentation[0].lexical.effective_locale='fr-CA';},
 ]) {const v=clone(model);fault(v);assert.throws(()=>requireKristalV11ReadView(v),/Invalid v11/);}
});
test('v11 CLI is strictly allowlisted and all modes are explicit',()=>{
 assert.equal(options(['v11','--operation','view','--locale','fr']).command,'v11');
 assert.throws(()=>options(['v11','--execute','arbitrary']),/Unsupported option/);
 assert.throws(()=>options(['v11','--operation','check','--operation','view']),/Repeated option/);
});
test('v11 handoff CLI rejects missing files, unexpected flags or write requests',()=>{
 assert.equal(options(['v11-handoff','--framework','/fw']).command,'v11-handoff');
 for(const argv of [['v11-handoff','--activate','yes'],['v11-handoff','--kit-candidate','yes','--kit-candidate','yes']])
   assert.throws(()=>options(argv),/Unsupported option|Repeated option/);
 const r=spawnSync(process.execPath,[path.join(root,'tools/kristal-bridge.mjs'),'v11-handoff','--kit-candidate','yes'],{encoding:'utf8'});
 assert.notEqual(r.status,0);assert.match(r.stderr,/requires/);
});
test('v11 CLI rejects missing pinned inputs, no write or network',()=>{
 const r=spawnSync(process.execPath,[path.join(root,'tools/kristal-bridge.mjs'),'v11','--operation','check'],{encoding:'utf8'});
 assert.notEqual(r.status,0);assert.match(r.stderr,/requires/);
});
test('real pinned Framework v11 check works with supplied checkout (optional)',t=>{
 const fw=process.env.KRISTAL_FRAMEWORK_ROOT;
 if(!fw){t.skip('Set KRISTAL_FRAMEWORK_ROOT to Framework draft.4');return;}
 const sample=path.join(fw,'examples/v11');
 const args=['v11','--operation','view','--framework',fw,
   '--registry',path.join(sample,'identity-registry.example.json'),
   '--graph',path.join(sample,'semantic-graph.example.json'),
   '--crosswalk',path.join(sample,'external-crosswalk.example.json'),
   '--catalog',path.join(sample,'dictionaries/catalog.json'), '--locale','fr-CA'];
 const r=spawnSync(process.execPath,[path.join(root,'tools/kristal-bridge.mjs'),...args],{encoding:'utf8',timeout:30000});
 assert.equal(r.status,0,r.stderr);
 const view=JSON.parse(r.stdout);requireKristalV11ReadView(view);
 assert.equal(view.presentation.find(x=>x.semantic_id==='KQ1001').lexical.status,'fallback');
 assert.equal(view.assertions[0].predicate,'KP2001');
});
