/** Optional v11 display envelope guard for consumers (read-only).
 * This is NOT a replacement for the pinned Framework validator, and this module
 * is deliberately NOT auto-installed into Konstellation routes by install.py.
 */
const SHA = /^[0-9a-f]{64}$/;
const ENTITY = /^KQ[1-9][0-9]*$/;
const PROPERTY = /^KP[1-9][0-9]*$/;
const ASSERTION = /^KA[1-9][0-9]*$/;
const SOURCE = /^KS[1-9][0-9]*$/;
const plainObject = x => x !== null && typeof x === 'object' && !Array.isArray(x);
function reject(reason){throw new Error('Invalid v11 derived read-view: '+reason);}

export function requireKristalV11ReadView(view) {
  if (!plainObject(view) || view.profile!=='kristal.integration.read-view/v11.0-draft.1'
      || view.derived_only !== true) reject('derived read-view profile required');
  const s=view.source;
  if(!plainObject(s) || typeof s.namespace_id !== 'string' || !s.namespace_id
      || typeof s.graph_id !== 'string' || !s.graph_id
      || !['11.0.0-draft.3','11.0.0-draft.4'].includes(s.framework_version)
      || ['graph_sha256','registry_sha256','crosswalk_sha256','catalog_sha256'].some(k=>!SHA.test(s[k]||'')))
    reject('missing or unpinned source integrity references');
  if(typeof view.requested_locale!=='string' || !/^[a-zA-Z]{2,8}(?:-[a-zA-Z0-9]{1,8})*$/.test(view.requested_locale))
    reject('invalid locale');
  if(!Array.isArray(view.presentation) || !Array.isArray(view.assertions) || !plainObject(view.coverage_counts))
    reject('malformed display or assertion inventory');
  const ids = new Set();
  const actual = {direct:0,fallback:0,missing:0};
  for(const entry of view.presentation){
    if(!plainObject(entry) || !(entry.kind==='entity' ? ENTITY : entry.kind==='property' ? PROPERTY : null)?.test(entry.semantic_id||''))
      reject('non-KQ/KP semantic reference');
    if(ids.has(entry.semantic_id))reject('duplicate presentation reference');
    ids.add(entry.semantic_id);
    const lex=entry.lexical;
    if(!plainObject(lex) || !Object.hasOwn(actual,lex.status))reject('invalid lexical status');
    if(lex.status==='missing'){
      if(Object.hasOwn(lex,'term'))reject('invented term on missing identity');
    } else if(typeof lex.term!=='string' || !lex.term
        || typeof lex.layer_id!=='string' || !lex.layer_id
        || typeof lex.effective_locale!=='string' || !lex.effective_locale
        || (lex.status==='direct' && lex.effective_locale!==view.requested_locale)
        || (lex.status==='fallback' && lex.effective_locale===view.requested_locale)){
      reject('unverifiable displayed term');
    }
    if(entry.accepted_external_exact !== undefined){
      const ext=entry.accepted_external_exact;
      if(!plainObject(ext) || ext.system!=='wikidata' || !(entry.kind==='entity' ? /^Q[1-9][0-9]*$/ : /^P[1-9][0-9]*$/).test(ext.id||''))
        reject('invalid external exact mapping');
    }
    actual[lex.status]++;
  }
  if(['direct','fallback','missing'].some(k=>view.coverage_counts[k]!==actual[k]))reject('coverage summary mismatch');
  for(const assertion of view.assertions){
    if(!plainObject(assertion) || !ASSERTION.test(assertion.id||'')
        || !ENTITY.test(assertion.subject||'') || !PROPERTY.test(assertion.predicate||'')
        || !plainObject(assertion.object) || !Array.isArray(assertion.sources)
        || !assertion.sources.every(s=>SOURCE.test(s))
        || (assertion.object.kind==='entity' ? !ENTITY.test(assertion.object.id||'')
            : assertion.object.kind==='literal' ? (!['string','boolean','integer','number','date','dateTime','uri'].includes(assertion.object.datatype) || !Object.hasOwn(assertion.object,'value'))
            : true))
      reject('non-canonical assertion reference');
    if(!ids.has(assertion.subject) || !ids.has(assertion.predicate)
        || (assertion.object.kind==='entity' && !ids.has(assertion.object.id)))
      reject('assertion reference not represented in display inventory');
    if(assertion.qualifiers){
      if(!Array.isArray(assertion.qualifiers) || assertion.qualifiers.some(q=>!PROPERTY.test(q?.predicate||'') || !ids.has(q.predicate) || !plainObject(q.object) || !(q.object.kind==='entity' ? ENTITY.test(q.object.id||'') && ids.has(q.object.id) : q.object.kind==='literal' && Object.hasOwn(q.object,'value') && typeof q.object.datatype==='string')))
        reject('invalid qualifier predicate');
    }
  }
  return view;
}
