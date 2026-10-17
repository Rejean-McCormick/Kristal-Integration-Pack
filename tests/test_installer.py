"""Portable install/reinstall/rollback tests; no Konstellation checkout required."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('integration_installer',BASE/'tools/install.py')
installer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def make_baseline(self, root):
        # Minimal anchor fixtures from Konstellation 1.0.0-rc.2, not domain content.
        contents={
          'server/index.mjs': """import { SemantikAdapter } from './integrations/semantik.mjs';
async function body(req) {
  let size = 0;
}
if (size > 65536)
  semantik = new SemantikAdapter(),
        if(req.method==='GET' && ['/api/bootstrap','/api/capabilities'].includes(url.pathname)) {
        if(url.pathname.startsWith('/api/sa')) requireScope(principal,'sa'); else requireScope(principal,'read');
        const b=await body(req); if(!b||typeof b!=='object'||Array.isArray(b)) fail('INVALID_QUERY','Objet JSON requis.');
        switch(url.pathname){
          case '/api/query':
""",
          'server/config.mjs': "scopes: ['read','metrics','sa','admin'],\n",
          'src/components/Explorer.svelte': "  import Communication from './Communication.svelte';\n      <div class=\"workspace\">\n",
        }
        (root/'package.json').write_text(json.dumps({'version':'1.0.0-rc.2'}))
        for name,contents_text in contents.items():
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(contents_text,encoding='utf8')
        return contents

    def test_preview_apply_idempotence_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            old=self.make_baseline(root)
            self.assertEqual(len(installer.patch(root,apply=False)),5)
            self.assertFalse((root/'.kristal-integration-backup').exists())
            self.assertEqual(len(installer.patch(root,apply=True)),5)
            self.assertEqual(installer.patch(root,apply=True),[])
            status=installer.inspect(root)
            self.assertTrue(status['existing_integration'])
            self.assertTrue(status['recorded_patch_matches'])
            self.assertTrue(status['pack_overlay_matches_installed'])
            self.assertEqual(len(installer.rollback(root)),5)
            for name,source in old.items():self.assertEqual((root/name).read_text(),source)
            self.assertFalse((root/'server/integrations/kompiler-bridge.mjs').exists())

    def test_refuse_changed_managed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make_baseline(root);installer.patch(root,apply=True)
            p=root/'server/index.mjs';p.write_text(p.read_text()+'\n// upstream change')
            self.assertFalse(installer.inspect(root)['recorded_patch_matches'])
            with self.assertRaisesRegex(RuntimeError,'Subsequent changes'):
                installer.rollback(root)

    def test_refuse_existing_modified_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make_baseline(root)
            p=root/'server/integrations/kompiler-bridge.mjs';p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('// owner bridge, must never overwrite\n')
            with self.assertRaisesRegex(RuntimeError,'Existing integration file differs'):
                installer.patch(root,apply=True)
            self.assertFalse((root/'.kristal-integration-backup').exists())
            self.assertEqual(p.read_text(),'// owner bridge, must never overwrite\n')

    def test_unsupported_version_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make_baseline(root)
            (root/'package.json').write_text(json.dumps({'version':'2.0.0'}))
            with self.assertRaisesRegex(RuntimeError,'Unsupported'):
                installer.patch(root,apply=True)


if __name__=='__main__':unittest.main()
