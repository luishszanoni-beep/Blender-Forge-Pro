import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from gcb_core import load_spec, validate, primitive_mesh, world_anchor, fingerprint, sheet_svg


class GcbBlueprintTests(unittest.TestCase):
    def setUp(self):
        self.spec=load_spec(ROOT/'examples/gcb/demo_bloxy_plant.json')

    def test_demo_valid_and_truthful_status(self):
        report=validate(self.spec)
        self.assertEqual(report['errors'],[])
        self.assertEqual(report['status'],'SPEC_VALIDATED_PENDING_VISUAL_QA')
        self.assertIn('relative units',report['warnings'][0])

    def test_duplicate_identity_blocked(self):
        value=copy.deepcopy(self.spec)
        value['parts'][-1]['id']='LEAF_L'
        self.assertEqual(validate(value)['status'],'BLOCKED')

    def test_duplicate_component_geometry_blocked(self):
        value=copy.deepcopy(self.spec)
        value['parts'][-1]['position']=value['parts'][-2]['position']
        value['parts'][-1]['rotation_deg']=value['parts'][-2]['rotation_deg']
        self.assertTrue(any('duplicate component' in e for e in validate(value)['errors']))

    def test_misfit_attachment_blocked(self):
        value=copy.deepcopy(self.spec)
        value['parts'][2]['position'][1] += .4
        self.assertTrue(any('anchor gap' in e for e in validate(value)['errors']))

    def test_no_fabricated_real_world_scale(self):
        value=copy.deepcopy(self.spec)
        value['units']={'mode':'mm'}
        self.assertTrue(any('calibrated' in e for e in validate(value)['errors']))

    def test_undefined_source_blocked(self):
        value=copy.deepcopy(self.spec)
        value['parts'][0]['confidence']='observed'
        value['parts'][0]['source_ids']=['nonexistent']
        self.assertTrue(any('unknown source IDs' in e for e in validate(value)['errors']))

    def test_parent_cycles_blocked(self):
        value=copy.deepcopy(self.spec)
        value['parts'][0]['parent']='J1'
        self.assertTrue(any('parenting cycle' in e for e in validate(value)['errors']))

    def test_parent_without_declared_anchor_blocked(self):
        value=copy.deepcopy(self.spec)
        value['attachments']=[a for a in value['attachments'] if a['child']!='LEAF_L']
        self.assertTrue(any('missing attachment anchor' in e for e in validate(value)['errors']))

    def test_bad_numeric_transform_cannot_crash_validator(self):
        value=copy.deepcopy(self.spec)
        value['parts'][2]['position']='INVALID'
        report=validate(value)
        self.assertEqual(report['status'],'BLOCKED')

    def test_step_coverage_blocked(self):
        value=copy.deepcopy(self.spec)
        value['steps'][-1]['parts']=['LEAF_L']
        self.assertTrue(any('absent from steps' in e for e in validate(value)['errors']))

    def test_mandible_is_separate_and_unique(self):
        ids=[p['id'] for p in self.spec['parts']]
        self.assertEqual(ids.count('J1'),1)
        mandible=next(p for p in self.spec['parts'] if p['id']=='J1')
        self.assertEqual(mandible['parent'],'HEAD')
        self.assertTrue(mandible['separate_mesh'])
        attach=self.spec['attachments'][0]
        world_child=world_anchor(mandible,attach['anchor_child'])
        head=next(p for p in self.spec['parts'] if p['id']=='HEAD')
        world_parent=world_anchor(head,attach['anchor_parent'])
        self.assertAlmostEqual(sum((a-b)**2 for a,b in zip(world_child,world_parent)),0,places=6)

    def test_geometry_simple_box_dimensions(self):
        box=self.spec['parts'][1]
        points,faces=primitive_mesh(box)
        self.assertEqual(len(points),8)
        self.assertEqual(len(faces),6)
        self.assertAlmostEqual(max(p[2] for p in points)-min(p[2] for p in points),box['dimensions'][2])

    def test_technical_sheet_only_reflects_spec(self):
        before=sheet_svg(self.spec,step=2)
        self.assertIn('J1',before)
        self.assertIn('FRONTAL X/Z',before)
        self.assertIn('0.63,0.52,0.16',before)
        self.assertNotIn('<script',before)
        self.assertNotIn('LEAF_L',before)
        self.assertNotIn('LEAF_R',before)

    def test_script_cli_prepares_staged_renders(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'gcb'
            p=subprocess.run([sys.executable,str(ROOT/'scripts/gcb.py'),'prepare',
                              str(ROOT/'examples/gcb/demo_bloxy_plant.json'),'--out',str(out)],
                             capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr+'\n'+p.stdout)
            report=json.loads((out/'gcb_preflight.json').read_text())
            self.assertEqual(report['svg_count'],6)
            self.assertFalse(report['blender_executed'])
            self.assertEqual(report['g1_5_approval'],'PENDING_INDEPENDENT_AUDIT')
            self.assertTrue((out/'sheets/01_exploded.svg').exists())
            self.assertTrue((out/'gcb_handoff.md').exists())


if __name__=='__main__':unittest.main()
