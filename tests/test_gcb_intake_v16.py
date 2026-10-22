"""Offline regressions for adaptive G0-F file request behavior.

These only test file metadata and user request construction, never visual QA.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from gcb_intake import evaluate_intake, format_request


class FileIntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        (self.project / 'input').mkdir()
        self.manifest = {
            'project_id': 'dragon_demo',
            'intent': 'reference_model',
            'target': 'roblox',
            'needs': {},
            'assets': [],
            'provided_information': {},
            'unavailable': [],
        }

    def create_asset(self, name, role='art_reference', view='side'):
        f = self.project / 'input' / name
        f.write_bytes(b'demo asset only - no real visual content')
        self.manifest['assets'].append({
            'id': 'A' + str(len(self.manifest['assets']) + 1),
            'role': role, 'path': 'input/' + name, 'view': view
        })
        return f

    def test_missing_primary_art_is_essential(self):
        rep = evaluate_intake(self.manifest, self.project)
        self.assertEqual(rep['status'], 'AWAITING_REQUIRED_INPUT')
        self.assertFalse(rep['ready_for_g1'])
        self.assertIn('primary_visual', [x['code'] for x in rep['missing_required']])
        self.assertIn('Envie os materiais essenciais', format_request(rep))

    def test_one_existing_reference_suffices_for_non_strict(self):
        self.create_asset('dragon.png')
        rep = evaluate_intake(self.manifest, self.project)
        self.assertTrue(rep['ready_for_g1'])
        self.assertEqual(rep['status'], 'READY_FOR_REFERENCE_ANALYSIS')
        self.assertFalse(rep['missing_required'])
        self.assertIn('dragon.png', format_request(rep))
        self.assertNotIn('Arquivos/informacoes essenciais pendentes', format_request(rep))

    def test_strict_fidelity_suggests_views_not_require(self):
        self.create_asset('dragon.png')
        self.manifest['needs']['strict_fidelity'] = True
        rep = evaluate_intake(self.manifest, self.project)
        self.assertTrue(rep['ready_for_g1'])
        self.assertEqual(rep['status'], 'READY_WITH_ASSUMPTIONS')
        self.assertIn('multi_angle_views', [x['code'] for x in rep['recommended_files']])
        self.assertEqual(rep['missing_required'], [])

    def test_extra_views_and_closeups_remove_requests(self):
        self.create_asset('dragon_side.png')
        self.create_asset('dragon_front.webp', role='orthographic_reference', view='front')
        self.create_asset('dragon_head.jpg', role='detail_reference', view='unknown')
        self.manifest['needs']['strict_fidelity'] = True
        rep = evaluate_intake(self.manifest, self.project)
        self.assertEqual(rep['recommended_files'], [])

    def test_declined_optional_file_not_requested_again(self):
        self.create_asset('dragon.png')
        self.manifest['needs']['strict_fidelity'] = True
        self.manifest['unavailable'] = ['multi_angle_views', 'closeups']
        rep = evaluate_intake(self.manifest, self.project)
        self.assertEqual(rep['recommended_files'], [])
        self.assertEqual(rep['status'], 'READY_FOR_REFERENCE_ANALYSIS')

    def test_editing_requires_real_source_file(self):
        self.manifest['intent'] = 'edit_existing'
        rep = evaluate_intake(self.manifest, self.project)
        self.assertIn('editable_source', [x['code'] for x in rep['missing_required']])
        self.create_asset('dragon.blend', role='source_mesh')
        rep2 = evaluate_intake(self.manifest, self.project)
        self.assertTrue(rep2['ready_for_g1'])

    def test_authorized_scene_access_is_alternative_to_upload(self):
        self.manifest['intent'] = 'edit_existing'
        self.manifest['needs']['existing_scene_access'] = True
        rep = evaluate_intake(self.manifest, self.project)
        self.assertTrue(rep['ready_for_g1'])

    def test_original_model_can_start_from_text_without_file(self):
        self.manifest['intent'] = 'original_model'
        self.manifest['provided_information']['brief'] = 'Dragao cartoon com tres chifres'
        rep = evaluate_intake(self.manifest, self.project)
        self.assertTrue(rep['ready_for_g1'])

    def test_original_model_empty_requires_brief_not_photo(self):
        self.manifest['intent'] = 'original_model'
        rep = evaluate_intake(self.manifest, self.project)
        self.assertEqual([x['code'] for x in rep['missing_required']], ['creative_brief'])

    def test_exact_scale_requires_verified_numbers_even_if_pdf_exists(self):
        self.create_asset('dragon.png')
        self.create_asset('manual.pdf', role='technical_document', view='unknown')
        self.manifest['needs']['absolute_scale_required'] = True
        rep = evaluate_intake(self.manifest, self.project)
        self.assertIn('physical_scale', [x['code'] for x in rep['missing_required']])
        self.manifest['provided_information']['verified_dimension_source'] = 'Measured drawing p3, confirmed by agent'
        rep2 = evaluate_intake(self.manifest, self.project)
        self.assertTrue(rep2['ready_for_g1'])

    def test_retarget_only_blocks_if_no_rig_source_or_description(self):
        self.create_asset('dragon.png')
        self.manifest['needs']['retarget_rig'] = True
        rep = evaluate_intake(self.manifest, self.project)
        self.assertIn('target_skeleton', [x['code'] for x in rep['missing_required']])
        self.manifest['provided_information']['rig_spec'] = 'Root -> Spine -> Jaw with XYZ axes'
        rep2 = evaluate_intake(self.manifest, self.project)
        self.assertTrue(rep2['ready_for_g1'])

    def test_animation_requests_motion_only_as_recommended(self):
        self.create_asset('dragon.png')
        self.manifest['needs']['animation'] = True
        rep = evaluate_intake(self.manifest, self.project)
        self.assertTrue(rep['ready_for_g1'])
        self.assertIn('motion_reference', [x['code'] for x in rep['recommended_files']])
        self.assertIn('animation_clips', [x['code'] for x in rep['text_questions']])

    def test_path_escape_is_rejected_and_never_counted(self):
        self.manifest['assets'] = [{'id': 'A1', 'role':'art_reference','path':'../secret.png'}]
        rep = evaluate_intake(self.manifest, self.project)
        self.assertEqual(rep['status'], 'BLOCKED_INVALID_MANIFEST')
        self.assertEqual(rep['verified_assets'], [])

    def test_nonexistent_file_not_claimed_received(self):
        self.manifest['assets'] = [{'id':'A1','role':'art_reference','path':'input/missing.png'}]
        rep = evaluate_intake(self.manifest, self.project)
        self.assertEqual(rep['verified_assets'], [])
        self.assertTrue(rep['errors'])

    def test_symlink_is_rejected(self):
        orig = self.project / 'input' / 'real.png'
        orig.write_bytes(b'image')
        (self.project / 'input' / 'alias.png').symlink_to(orig)
        self.manifest['assets'] = [{'id':'A1','role':'art_reference','path':'input/alias.png'}]
        rep = evaluate_intake(self.manifest, self.project)
        self.assertTrue(any('symlink' in e for e in rep['errors']))

    def test_duplicate_asset_id_not_silently_accepted(self):
        self.create_asset('one.png')
        self.create_asset('two.png')
        self.manifest['assets'][1]['id'] = 'A1'
        rep = evaluate_intake(self.manifest, self.project)
        self.assertEqual(rep['status'], 'BLOCKED_INVALID_MANIFEST')
        self.assertTrue(any('duplicate ID' in x for x in rep['errors']))

    def test_cli_generates_single_consolidated_request(self):
        source = self.create_asset('dragon.png')
        self.manifest['needs'] = {'strict_fidelity': True}
        src = self.project / 'intake_manifest.json'
        src.write_text(json.dumps(self.manifest),encoding='utf-8')
        cmd = [sys.executable, str(ROOT/'scripts/gcb_intake.py'), str(src),
               '--root', str(self.project), '--out', 'planning/gcb/intake']
        p = subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr+'\n'+p.stdout)
        dst = self.project/'planning/gcb/intake'
        report = json.loads((dst/'intake_report.json').read_text())
        self.assertTrue(report['ready_for_g1'])
        self.assertIn('dragon.png', (dst/'file_request.md').read_text())
        self.assertEqual(report['status'], 'READY_WITH_ASSUMPTIONS')

    def test_cli_returns_3_when_essential_files_missing(self):
        src=self.project/'intake_manifest.json'
        src.write_text(json.dumps(self.manifest),encoding='utf-8')
        p=subprocess.run([sys.executable,str(ROOT/'scripts/gcb_intake.py'),str(src),
                          '--root',str(self.project),'--out','planning/gcb/intake'],capture_output=True,text=True)
        self.assertEqual(p.returncode,3,p.stdout+'\n'+p.stderr)

    def test_gcb_prepare_respects_explicit_intake_report_guard(self):
        intake = self.project / 'intake_report.json'
        intake.write_text(json.dumps({'ready_for_g1':False,'missing_required':[{'code':'primary_visual'}],
                                      'errors':[]}),encoding='utf-8')
        out=self.project/'planning/gcb'
        demo=ROOT/'examples/gcb/demo_bloxy_plant.json'
        p=subprocess.run([sys.executable,str(ROOT/'scripts/gcb.py'),'prepare',str(demo),
                          '--out',str(out),'--intake-report',str(intake)],capture_output=True,text=True)
        self.assertEqual(p.returncode,4,p.stdout+'\n'+p.stderr)
        self.assertFalse((out/'sheets').exists())
        intake.write_text(json.dumps({'ready_for_g1':True,'missing_required':[], 'errors':[]}),encoding='utf-8')
        p2=subprocess.run([sys.executable,str(ROOT/'scripts/gcb.py'),'prepare',str(demo),
                           '--out',str(out),'--intake-report',str(intake)],capture_output=True,text=True)
        self.assertEqual(p2.returncode,0,p2.stdout+'\n'+p2.stderr)
        self.assertTrue((out/'gcb_spec.json').exists())


if __name__ == '__main__':
    unittest.main()
