import importlib.util
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'tools/spek_ecosystem_readiness.py'
spec=importlib.util.spec_from_file_location('spek_readiness',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_missing_repositories_fail_closed(tmp_path):
    report=m.audit(**dict.fromkeys(['spek','manager','semantik','runtime','arketype','framework','public',
                    'instance','requests','graph','identity_map','runtime_root'],tmp_path/'not-present'))
    assert report['status']=='BLOCKED'
    assert report['git_or_network_operations'] is False
    assert report['real_gf_pgf_article_produced'] is False


def test_framework_schema_must_enforce_private_gates(tmp_path):
    path=tmp_path/'private-editorial-handoff.schema.json'
    path.write_text('{}',encoding='utf-8')
    assert not m._valid_framework_handoff_schema(path)
    doc={'type':'object','additionalProperties':False,'properties':{
      'format':{'const':'spek.private-editorial-handoff/1.0'},
      'status':{'const':'PRIVATE_UNQUALIFIED_NOT_PUBLISHABLE'},
      'qualification':{'properties':{key:{'const':False} for key in (
        'semantic_entailment_checked','semantik_result_pairs_verified',
        'rhetorical_relations_approved','c1_c2_c3_approved','publication_authorized')}}}}
    import json
    path.write_text(json.dumps(doc),encoding='utf-8')
    assert m._valid_framework_handoff_schema(path)
    doc['properties']['qualification']['properties']['publication_authorized']['const']=True
    path.write_text(json.dumps(doc),encoding='utf-8')
    assert not m._valid_framework_handoff_schema(path)
