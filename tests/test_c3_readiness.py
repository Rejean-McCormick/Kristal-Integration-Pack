"""Unit checks for the read-only delegation boundary, no GitHub access."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('c3_readiness', BASE/'tools/check_c3_readiness.py')
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class C3ReadinessTests(unittest.TestCase):
    def test_missing_owner_checker_is_not_evaluated(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = preflight.check(Path(tmp))
            self.assertEqual(code, 3)
            self.assertIn('NOT_EVALUATED', report)

    def test_calls_only_owner_read_only_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            owner = root/'tools/c3_collection.py'
            owner.parent.mkdir()
            owner.write_text('''import sys
print('MODE='+sys.argv[-1])
raise SystemExit(2 if sys.argv[-1]=='scan' else 0)
''')
            code,report=preflight.check(root,'scan')
            self.assertEqual(code,2)
            self.assertIn('C3_BLOCKED',report)
            self.assertIn('MODE=scan',report)
            code,report=preflight.check(root,'validate-index')
            self.assertEqual(code,0)
            self.assertIn('C1/C2 and remote publication NOT verified',report)
            with self.assertRaises(ValueError):preflight.check(root,'build-index')

if __name__ == '__main__':unittest.main()
