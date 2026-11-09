"""Bounded Framework v11 read-view -> UNESCO semantic/article planning handoff.

Never infers a KQ from a Wikidata QID, does not call GF or generate text,
and never considers a derived read view an authorization to publish.
The explicit mapping file is a *selection request*, not independent evidence
of canonical identity approval. This tool is intentionally noncanonical.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

VIEW_PROFILE='kristal.integration.read-view/v11.0-draft.1'
OUT_PROFILE='kristal.integration.unesco-mt1-10-semantic-handoff/1.0'
KQ=re.compile(r'^KQ[0-9]+$');KA=re.compile(r'^KA[0-9]+$');KP=re.compile(r'^KP[0-9]+$');KS=re.compile(r'^KS[0-9]+$')
CID=re.compile(r'^concept[1-9][0-9]*$')

class BridgeError(ValueError):pass

def read_file(p:Path,limit=8_000_000):
    if not p.is_file() or p.stat().st_size>limit:raise BridgeError('Missing or oversized JSON source: '+str(p))
    b=p.read_bytes()
    d=json.loads(b)
    if not isinstance(d,dict):raise BridgeError('JSON object expected')
    return d,hashlib.sha256(b).hexdigest()

def make_handoff(view:dict,selection:dict|None=None,*,view_sha:str):
    if (view.get('profile')!=VIEW_PROFILE or view.get('derived_only') is not True or
        view.get('source',{}).get('framework_version')!='11.0.0-draft.4'):
        raise BridgeError('Requires the bounded Framework v11 draft.4 derived read-view')
    src=view['source']
    for k in ('namespace_id','graph_id','graph_sha256','registry_sha256','crosswalk_sha256','catalog_sha256'):
        if not isinstance(src.get(k),str) or not src[k]:raise BridgeError('Missing v11 source provenance: '+k)
    if not isinstance(view.get('requested_locale'),str):raise BridgeError('Missing locale')
    assertions=view.get('assertions'); pres=view.get('presentation')
    if not isinstance(assertions,list) or not isinstance(pres,list):raise BridgeError('Missing view records')
    ids={}; lexical={}
    for p in pres:
        kid=p.get('semantic_id'); typ=p.get('kind')
        if (typ=='entity' and not KQ.fullmatch(str(kid))) or (typ=='property' and not KP.fullmatch(str(kid))) or typ not in ('entity','property'):
            raise BridgeError('Unexpected semantic identity in lexical presentation')
        if kid in ids:raise BridgeError('Duplicate semantic identity')
        ids[kid]=typ
        lex=p.get('lexical')
        if not isinstance(lex,dict) or lex.get('status') not in ('direct','fallback','missing'):raise BridgeError('Invalid lexical status')
        lexical[kid]=lex
    by_subject={}
    seen=set()
    for a in assertions:
        aid=a.get('id');subject=a.get('subject'); pred=a.get('predicate');obj=a.get('object')
        if not KA.fullmatch(str(aid)) or aid in seen:raise BridgeError('Invalid or duplicate KA')
        seen.add(aid)
        if ids.get(subject)!='entity' or ids.get(pred)!='property':raise BridgeError('Assertion endpoint absent from reading view')
        if not isinstance(obj,dict) or obj.get('kind') not in ('entity','literal'):
            raise BridgeError('Unsupported assertion object')
        if obj['kind']=='entity' and ids.get(obj.get('id'))!='entity':raise BridgeError('Missing object entity')
        sources=a.get('sources')
        if not isinstance(sources,list) or not sources or any(not KS.fullmatch(str(x)) for x in sources):
            raise BridgeError('All exported KA must retain one or more KS references')
        by_subject.setdefault(subject,[]).append(a)
    selected=[]
    if selection is not None:
        if (selection.get('format')!='unesco-mt1-10-reviewed-selection/1.0' or selection.get('branch')!='unesco-mt1-10' or
            selection.get('namespace_id')!=src['namespace_id']):
            raise BridgeError('Selection must match branch and canonical namespace')
        rows=selection.get('selections')
        if not isinstance(rows,list):raise BridgeError('Missing selection rows')
        keys=set();kqs=set()
        for x in rows:
            cid=x.get('unesco_id'); kid=x.get('local_kq')
            if not CID.fullmatch(str(cid)) or not KQ.fullmatch(str(kid)) or cid in keys or kid in kqs:
                raise BridgeError('Invalid or duplicate UNESCO to local KQ selection')
            keys.add(cid);kqs.add(kid)
            if ids.get(kid)!='entity':raise BridgeError('Selected KQ missing from read view: '+kid)
            if not isinstance(x.get('decision_ref'),str) or not x['decision_ref'].strip():
                raise BridgeError('Missing independent decision reference')
            selected.append({'unesco_id':cid,'local_kq':kid,'decision_ref':x['decision_ref'],
                             'assertions':by_subject.get(kid,[]),'lexical':lexical[kid]})
    return {'profile':OUT_PROFILE,'branch':'unesco-mt1-10','semantic_grain':'one_branch_kristal',
            'namespace_id':src['namespace_id'],'graph_id':src['graph_id'],
            'view_sha256':view_sha,'source':src,'locale':view['requested_locale'],
            'selections':selected,'selected_concepts':len(selected),
            'assertions_with_KS':sum(len(x['assertions']) for x in selected),
            'article_prose_generated':False,'qualified_language_runtime':False,
            'authoritative_authoring_checked':False,'source_licensing_checked':False,
            'publication_authorized':False,'status':'PRIVATE_SEMANTIC_HANDOFF_ONLY'}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--view',required=True,type=Path);p.add_argument('--selection',type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args(argv)
    try:
        view,sha=read_file(a.view)
        sel=read_file(a.selection)[0] if a.selection else None
        result=make_handoff(view,sel,view_sha=sha)
        if a.out.exists() or any((p/'.git').exists() for p in a.out.resolve().parents):
            raise BridgeError('Private output must be new and outside a Git checkout')
        a.out.parent.mkdir(parents=True,exist_ok=True)
        with a.out.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
        print(json.dumps({'out':str(a.out),'selected_concepts':len(result['selections']),
                          'assertions_with_KS':result['assertions_with_KS'],'publication':'BLOCKED'}))
        return 0
    except (BridgeError,KeyError,TypeError,ValueError,FileExistsError) as exc:
        print(json.dumps({'error':str(exc),'publication':'BLOCKED'}),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
