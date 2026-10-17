"""Read-only v11 handoff tests, and optional real pinned Framework integration."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FW = Path(os.environ['KRISTAL_FRAMEWORK_ROOT']).resolve() if os.environ.get('KRISTAL_FRAMEWORK_ROOT') else None
sys.path.insert(0,str(ROOT/'tools'))
import v11_handoff as handoff
from v11_integration import IntegrationError, sha, verify_framework


class HandoffSafety(unittest.TestCase):
    def test_dik_job_refuses_unknown_format(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            for name in ('catalog.json','dik-job.json','registry.json','crosswalk.json'):
                (base/name).write_text('{}')
            with self.assertRaisesRegex(IntegrationError,'Unsupported'):
                handoff.check_job(job_file=base/'dik-job.json',catalog=base/'catalog.json',
                                  registry=base/'registry.json',crosswalk=base/'crosswalk.json')

    def test_dik_receipt_binds_catalog_registry_crosswalk(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);registry=base/'registry.json';crosswalk=base/'crosswalk.json'
            # Use a separate content-addressed output directory, like import-large.
            catalog=base/'output'/'catalog.json'
            catalog.parent.mkdir()
            catalog.write_text(json.dumps({'namespace_id':'demo','catalog_id':'wikidata-import-snap',
                          'languages':[{'tag':'fr','layers':[],'fallbacks':[]}]}))
            registry.write_text('{}');crosswalk.write_text('{}')
            job=base/'dik-job.json'
            rec={'profile':handoff.JOB_PROFILE,'catalog_sha256':sha(catalog),
                 'upstream_verified':False,
                 'source_pins':{'dump_sha256':'a'*64,'registry_sha256':sha(registry),
                                'crosswalk_sha256':sha(crosswalk),'namespace':'demo',
                                'snapshot':'snap','locales':['fr'],'upstream_verified':False,
                                'transform':'wikidata-large-import-1.0.0-alpha.7'}}
            key=hashlib.sha256(json.dumps(rec['source_pins'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            rec['idempotency_key']=key
            destination=base/key
            catalog.parent.rename(destination)
            catalog=destination/'catalog.json';job=destination/'dik-job.json'
            job.write_text(json.dumps(rec))
            result=handoff.check_job(job_file=job,catalog=catalog,registry=registry,crosswalk=crosswalk)
            self.assertFalse(result['upstream_sha256_independently_pinned'])
            self.assertEqual(result['catalog_sha256'],sha(catalog))
            catalog.write_text(catalog.read_text()+'\n')
            with self.assertRaisesRegex(IntegrationError,'digest mismatch'):
                handoff.check_job(job_file=job,catalog=catalog,registry=registry,crosswalk=crosswalk)
            rec['catalog_sha256']=sha(catalog);job.write_text(json.dumps(rec))
            crosswalk.write_text('changed')
            with self.assertRaisesRegex(IntegrationError,'registry/crosswalk digest mismatch'):
                handoff.check_job(job_file=job,catalog=catalog,registry=registry,crosswalk=crosswalk)

    def test_job_requires_explicit_kit_mode_and_graph_for_locales(self):
        with patch.object(handoff, 'verify_framework', return_value={}):
            with self.assertRaisesRegex(IntegrationError,'--kit-import-candidate'):
                handoff.run(framework=Path('unused'),catalog=Path('missing'),registry=Path('missing'),
                        crosswalk=Path('missing'),dik_job=Path('missing-job'))
            with self.assertRaisesRegex(IntegrationError,'require --graph'):
                handoff.run(framework=Path('unused'),catalog=Path('missing'),registry=Path('missing'),
                        crosswalk=Path('missing'),locales=['fr'])


@unittest.skipUnless(FW and (FW/'VERSION').is_file(), 'Set KRISTAL_FRAMEWORK_ROOT to pinned Framework draft.4')
class RealHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        verify_framework(FW)
        cls.example=FW/'examples/v11'

    def setUp(self):
        self.dir=tempfile.TemporaryDirectory();self.addCleanup(self.dir.cleanup)
        target=Path(self.dir.name)
        for name in ('identity-registry.example.json','external-crosswalk.example.json','semantic-graph.example.json'):
            shutil.copy2(self.example/name,target/name)
        shutil.copytree(self.example/'dictionaries',target/'dictionaries')
        self.args={'framework':FW,'catalog':target/'dictionaries/catalog.json',
                   'registry':target/'identity-registry.example.json',
                   'crosswalk':target/'external-crosswalk.example.json',
                   'graph':target/'semantic-graph.example.json'}

    def test_full_preflight_with_coverage_and_nonmutation(self):
        originals={x:sha(p) for x,p in self.args.items() if x!='framework'}
        result=handoff.run(**self.args,locales=['fr-CA','en'])
        self.assertEqual(result['status'],'preflight_pass')
        self.assertEqual(result['framework_version'],'11.0.0-draft.4')
        self.assertFalse(result['activated'])
        fr=result['framework_preflight']['graph']['coverage_by_locale'][0]
        self.assertEqual(fr['KQ']['fallback'],1)
        self.assertEqual(originals,{x:sha(p) for x,p in self.args.items() if x!='framework'})

    def test_kit_import_candidate_refuses_curated_layers(self):
        with self.assertRaisesRegex(IntegrationError,'Kit import candidate cannot contain'):
            handoff.run(**self.args,kit_import_candidate=True)

    def test_kit_import_candidate_accepts_verified_only_wikidata_layers(self):
        catalog=json.loads(self.args['catalog'].read_text())
        for language in catalog['languages']:
            language['layers']=[x for x in language['layers'] if x['kind']=='wikidata']
        self.args['catalog'].write_text(json.dumps(catalog,ensure_ascii=False))
        result=handoff.run(**self.args,kit_import_candidate=True)
        self.assertTrue(result['framework_preflight']['kit_import_candidate'])
        self.assertFalse(result['registered'])
        self.assertFalse(result['selected'])

    def test_reject_modified_layer_and_existing_output(self):
        layer=self.args['catalog'].parent/'curated-fr.json'
        layer.write_text(layer.read_text()+'\n')
        with self.assertRaisesRegex(IntegrationError,'digest mismatch'):
            handoff.run(**self.args)
        outfile=Path(self.dir.name)/'already.json'
        outfile.write_text('important')
        program=ROOT/'tools/v11_handoff.py'
        argv=[sys.executable,str(program),'--framework',str(FW)]
        for field in ('registry','crosswalk','catalog'):
            argv+=['--'+field,str(self.args[field])]
        argv+=['--out',str(outfile)]
        run=subprocess.run(argv,capture_output=True,text=True,timeout=30)
        self.assertNotEqual(run.returncode,0)
        self.assertEqual(outfile.read_text(),'important')

    def test_reject_catalog_namespace_mismatch(self):
        catalog=json.loads(self.args['catalog'].read_text())
        catalog['namespace_id']='unexpected'
        self.args['catalog'].write_text(json.dumps(catalog))
        with self.assertRaisesRegex(IntegrationError,'namespace mismatch'):
            handoff.run(**self.args)

    def test_node_bridge_real_handoff(self):
        program=ROOT/'tools/kristal-bridge.mjs'
        cmd=['node',str(program),'v11-handoff','--framework',str(FW)]
        for field in ('registry','crosswalk','catalog'):
            cmd+=['--'+field,str(self.args[field])]
        completed=subprocess.run(cmd,capture_output=True,text=True,timeout=40)
        self.assertEqual(completed.returncode,0,completed.stderr)
        self.assertEqual(json.loads(completed.stdout)['status'],'preflight_pass')


if __name__=='__main__': unittest.main()


KIT = Path(os.environ['KRISTAL_AUTHORING_KIT_ROOT']).resolve() if os.environ.get('KRISTAL_AUTHORING_KIT_ROOT') else None

@unittest.skipUnless(FW and KIT and (KIT/'tools/kristal.py').is_file(),
                     'Set KRISTAL_FRAMEWORK_ROOT and KRISTAL_AUTHORING_KIT_ROOT for cross-repository exercise')
class RealAuthoringKitCrossCheck(unittest.TestCase):
    def test_explicit_promotion_is_kit_owned(self):
        # All Kit operations run against a disposable copy, never the real workspace.
        with tempfile.TemporaryDirectory(prefix='kristal-pack-cross-') as temp:
            project=Path(temp)/'project'
            shutil.copytree(KIT/'examples/demo-semantic-v11',project)
            v=project/'canon/domain/v11'
            catalog=v/'dictionaries/catalog.json'
            graph=v/'graph.json'
            before=sha(graph)
            approved=handoff.run(framework=FW, catalog=catalog,registry=v/'registry.json',
                                 crosswalk=v/'crosswalk.json',graph=graph,
                                 locales=['fr','fr-CA'],kit_import_candidate=True)
            self.assertEqual(approved['status'],'preflight_pass')
            self.assertFalse(approved['selected'])
            kit_cli=KIT/'tools/kristal.py'
            imported=subprocess.run([sys.executable,str(kit_cli),'import-dik-catalog',str(project),
                      '--catalog',str(catalog),'--revision','pack-reviewed','--register',
                      '--artifact-id','urn:pack:integration:test','--contract-id','integration.dik'],
                      capture_output=True,text=True,timeout=40)
            self.assertEqual(imported.returncode,0,imported.stderr)
            entry=json.loads(imported.stdout)
            self.assertTrue(entry['registered'])
            self.assertFalse(entry['selected'])
            self.assertEqual(sha(graph),before)
            selected=subprocess.run([sys.executable,str(kit_cli),'select-v11-catalog',str(project),
                     '--catalog',entry['catalog']],capture_output=True,text=True,timeout=40)
            self.assertEqual(selected.returncode,0,selected.stderr)
            checked=subprocess.run([sys.executable,str(kit_cli),'check-v11',str(project)],
                                   capture_output=True,text=True,timeout=40)
            self.assertEqual(checked.returncode,0,checked.stderr)
            self.assertEqual(sha(graph),before)
