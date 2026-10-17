"""Framework v11 draft.4 adapter tests; external pin is mandatory for live profiles."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('v11_integration', ROOT/'tools/v11_integration.py')
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)
FRAMEWORK = Path(os.environ['KRISTAL_FRAMEWORK_ROOT']) if os.environ.get('KRISTAL_FRAMEWORK_ROOT') else None

class BridgeUnit(unittest.TestCase):
    def test_pins_are_explicit(self):
        pin=json.loads((ROOT/'contracts/v11-framework-pin.json').read_text())
        self.assertEqual(pin['version'], '11.0.0-draft.4')
        self.assertIn('tools/v11/validate_v11.py',pin['files'])
        self.assertEqual(len(set(pin['files'])),len(pin['files']))
        self.assertTrue(all(len(v)==64 for v in pin['files'].values()))

    def test_unpinned_root_is_rejected_without_import(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'VERSION').write_text('11.0.0-draft.4\n')
            with self.assertRaisesRegex(bridge.IntegrationError,'digest mismatch'):
                bridge.verify_framework(p)

    def test_unrecognized_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'VERSION').write_text('10.0.0\n')
            with self.assertRaisesRegex(bridge.IntegrationError,'version'):
                bridge.verify_framework(p)

    def test_output_is_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            dst=Path(d)/'existing.json';dst.write_text('DO NOT CHANGE')
            with self.assertRaises(FileExistsError):
                bridge.emit({'modified':True},dst)
            self.assertEqual(dst.read_text(),'DO NOT CHANGE')

    def test_view_has_no_unapproved_label_or_q(self):
        graph={'entities':['KQ1','KQ2'],'properties':['KP1'],'assertions':[],
               'namespace_id':'demo','graph_id':'demo'}
        layers={'en':{'tag':'en','fallbacks':[],'layers':[]}}
        class Dict:
            @staticmethod
            def safe_file(root,name):
                return root/name
            @staticmethod
            def layer_records(path,kind):
                return []
        # Ensure absent labels are *missing*, never guessed or translated.
        result=bridge.indexed_labels(graph=graph,catalog={'languages':list(layers.values())},catalog_path=Path('/tmp/catalog.json'),locale='en',dictionary=Dict())
        self.assertEqual(set(result),{'KQ1','KQ2','KP1'})
        self.assertTrue(all(x['status']=='missing' for x in result.values()))

    def test_locale_must_be_declared(self):
        with self.assertRaisesRegex(bridge.IntegrationError,'not declared'):
            bridge.indexed_labels(graph={'entities':[],'properties':[]},catalog={'languages':[]},catalog_path=Path('x'),locale='xx',dictionary=object())

@unittest.skipUnless(FRAMEWORK and (FRAMEWORK/'VERSION').exists(), 'Set KRISTAL_FRAMEWORK_ROOT to tested Framework draft.4 checkout for integration')
class RealFrameworkIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge.verify_framework(FRAMEWORK)
        cls.examples=FRAMEWORK/'examples/v11'

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name)
        source=self.examples
        self.files={}
        for key,file in [('registry','identity-registry.example.json'),('graph','semantic-graph.example.json'),('crosswalk','external-crosswalk.example.json')]:
            target=base/file;shutil.copy2(source/file,target);self.files[key]=target
        shutil.copytree(source/'dictionaries',base/'dictionaries')
        self.files['catalog']=base/'dictionaries/catalog.json'
        self.args=SimpleNamespace(framework=FRAMEWORK,**self.files,locale='fr-CA',out=None,locales=None)
        self.mods=bridge.load_framework(FRAMEWORK)

    def test_fixture_check_and_derived_read_view(self):
        verified=bridge.verify_bundle(self.args,self.mods)
        result=bridge.make_read_view(self.args,verified,self.mods[1])
        self.assertTrue(result['derived_only'])
        self.assertEqual(result['coverage_counts'],{'direct':0,'fallback':1,'missing':2})
        self.assertEqual(result['assertions'][0]['subject'],'KQ1001')
        self.assertEqual(result['assertions'][0]['predicate'],'KP2001')
        self.assertEqual(result['assertions'][0]['object']['id'],'KQ1002')
        display={x['semantic_id']:x for x in result['presentation']}
        self.assertEqual(display['KQ1001']['lexical']['term'],'Saint Augustin')
        self.assertEqual(display['KQ1001']['accepted_external_exact']['id'],'Q8018')
        self.assertNotIn('accepted_external_exact',display['KQ1002'])
        self.assertEqual(display['KP2001']['lexical']['status'],'missing')

    def test_coverage_delegates_to_framework(self):
        report=self.mods[2].make_report(graph_path=self.args.graph,catalog_path=self.args.catalog,
                 registry_path=self.args.registry,crosswalk_path=self.args.crosswalk,locales=['fr-CA','en'])
        self.assertEqual(report['artifact_type'],'kristal_dik_coverage_report')
        self.assertEqual(report['locales'][0]['KQ']['fallback'],1)
        self.assertEqual(report['locales'][0]['KP']['missing'],1)

    def test_text_predicate_fails_closed(self):
        graph=json.loads(self.args.graph.read_text())
        graph['assertions'][0]['predicate']='has doctrinal status'
        self.args.graph.write_text(json.dumps(graph))
        with self.assertRaises(Exception):bridge.verify_bundle(self.args,self.mods)

    def test_dictionary_layer_corruption_fails_closed(self):
        layer=self.args.catalog.parent/'curated-fr.json'
        layer.write_text(layer.read_text()+'\n')
        with self.assertRaisesRegex(Exception,'digest mismatch'):
            bridge.verify_bundle(self.args,self.mods)

    def test_unaccepted_wikidata_crosswalk_cannot_create_label(self):
        # Demote accepted exact to candidate: imported Wikidata must no longer be trusted.
        cw=json.loads(self.args.crosswalk.read_text())
        cw['mappings'][0]['status']='candidate'
        cw['mappings'][0].pop('review',None)
        self.args.crosswalk.write_text(json.dumps(cw))
        with self.assertRaisesRegex(Exception,'unaccepted or stale'):
            bridge.verify_bundle(self.args,self.mods)

    def test_new_view_does_not_mutate_inputs(self):
        before={k:bridge.sha(v) for k,v in self.files.items()}
        verified=bridge.verify_bundle(self.args,self.mods)
        result=bridge.make_read_view(self.args,verified,self.mods[1])
        dst=Path(self.tmp.name)/'read-view.json'
        bridge.emit(result,dst)
        self.assertEqual({k:bridge.sha(v) for k,v in self.files.items()},before)
        self.assertTrue(dst.exists())
        with self.assertRaises(FileExistsError):bridge.emit(result,dst)

    def test_cli_explicit_pinning_and_v11_profile(self):
        argv=[str(ROOT/'tools/v11_integration.py'),'check','--framework',str(FRAMEWORK)]
        for key,v in self.files.items():argv += ['--'+key,str(v)]
        completed=subprocess.run([sys.executable,*argv],capture_output=True,text=True,timeout=30)
        self.assertEqual(completed.returncode,0,completed.stderr)
        self.assertTrue(json.loads(completed.stdout)['valid'])

if __name__=='__main__': unittest.main()
