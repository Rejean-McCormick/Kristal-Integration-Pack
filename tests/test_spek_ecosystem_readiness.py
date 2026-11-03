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
