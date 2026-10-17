"""Optional conformance check against Konstellation and Kristal Framework snapshots."""
import argparse, json
from pathlib import Path
try:
    from jsonschema import Draft202012Validator
except ImportError:
    raise SystemExit('Install jsonschema for optional schema validation: python -m pip install jsonschema')
parser=argparse.ArgumentParser()
parser.add_argument('--konstellation',type=Path)
parser.add_argument('--framework',type=Path)
a=parser.parse_args()
pack=Path(__file__).resolve().parents[1]
state=json.loads((pack/'examples/kompiler-v7-projection-demo.json').read_text('utf8'))
assert state['schema_version']=='6.0' and state['artifact_type']=='kristal_state'
schemas=[]
if a.konstellation: schemas.append(a.konstellation/'contracts/upstream/kristal-state-v6.schema.json')
if a.framework: schemas.append(a.framework/'schemas/v6/kristal-state.schema.json')
if not schemas:
    print('BASIC SAMPLE ONLY — provide --konstellation and --framework for two-schema validation')
for p in schemas:
    Draft202012Validator(json.loads(p.read_text('utf8'))).validate(state)
    print('SCHEMA OK:',p)
print('Demo backend:',json.loads((pack/'examples/demo-backend.json').read_text())['adapter'])
