"""Safety and technical feature tests for the V1.3 Blender Forge upgrade.

No Blender on this host => Blender bpy execution explicitly NOT TESTED.
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from forge_v13_core import (num,vec,ident,validate_recipe,validate_repair,validate_lod,
                           validate_variant_config,resolve_variant,validate_assembly,audit_assembly)
from reference_alignment import align
from regress_views import analyze as regress
from benchmark_runner import validate_run, compare_runs
from blender_bridge import prepare_argv
from test_forge import glb_bytes


def sample(name):return json.loads((ROOT/'examples/upgrades'/name).read_text(encoding='utf-8'))


class GeometryRecipeTests(unittest.TestCase):
    def setUp(self):self.doc=sample('chair_procedural_demo.json')
    def fails(self,term=None):
        with self.assertRaises(ValueError) as e:validate_recipe(self.doc)
        if term:self.assertIn(term,str(e.exception))
    def test_example_preflight(self):
        res=validate_recipe(self.doc)
        self.assertEqual(res['status'],'VALIDATED_SPEC_NOT_EXECUTED')
        self.assertIn('seat_seam',res['parts'])
        self.assertIn('seat_recess',res['feature_ids'])
    def test_missing_project_id(self):self.doc.pop('project_id');self.fails()
    def test_wrong_version(self):self.doc['schema_version']='1.0';self.fails('1.3')
    def test_arbitrary_code_key_refused(self):self.doc['operators'][0]['python_code']='exec()';self.fails('unknown')
    def test_unknown_operator(self):self.doc['operators'][0]['op']='run-python';self.fails('unsupported')
    def test_unsupported_target_field_refused(self):self.doc['operators'][0]['target_part_id']='seat_base';self.fails('unknown')
    def test_misplaced_material_refused(self):self.doc['operators'][0]['material_id']='nope';self.fails('material')
    def test_negative_size_refused(self):self.doc['operators'][0]['size_m'][0]=-0.1;self.fails('size')
    def test_nan_refused(self):self.doc['operators'][0]['center_m'][1]=float('nan');self.fails('finite')
    def test_inf_refused(self):self.doc['operators'][0]['center_m'][0]=float('inf');self.fails('finite')
    def test_boolean_as_size_refused(self):self.doc['operators'][0]['size_m'][2]=True;self.fails('finite')
    def test_duplicate_part(self):self.doc['operators'][1]['part_id']=self.doc['operators'][0]['part_id'];self.fails('duplicate')
    def test_duplicate_feature(self):self.doc['operators'][-1]['feature_id']='seam_geometry';self.fails('feature_id')
    def test_groove_must_target_prior(self):self.doc['operators'][-1]['target_part_id']='missing';self.fails('existing')
    def test_groove_no_feature(self):self.doc['operators'][-1].pop('feature_id');self.fails('feature_id')
    def test_malicious_material_node_rejected(self):self.doc['materials'][0]['node_script']='expr';self.fails('unknown')
    def test_empty_operators(self):self.doc['operators']=[];self.fails('1..300')
    def test_many_ops_bounded(self):self.doc['operators']=[self.doc['operators'][0]]*301;self.fails('1..300')
    def test_loft_too_few_rings(self):self.doc['operators'][6]['rings']=[{'center_m':[0,0,0],'radius_x_m':1,'radius_y_m':1}];self.fails('loft')
    def test_invalid_tube_controlpoints(self):self.doc['operators'][7]['points_m']=[[0,0,0]];self.fails('tube')
    def test_num_bools_fails(self):
        with self.assertRaises(ValueError):num(False)
    def test_ident_rejects_traversal(self):
        with self.assertRaises(ValueError):ident('../../evil')
    def test_primitive_variations(self):
        self.doc['operators'].append({'op':'cylinder','part_id':'pin_demo','center_m':[0,0,.7],'radius_m':.01,'depth_m':.06,'material_id':'steel'})
        self.doc['operators'].append({'op':'uv_sphere','part_id':'ball_demo','center_m':[0,0,.8],'size_m':[.04,.04,.04],'material_id':'steel'})
        self.assertEqual(validate_recipe(self.doc)['status'],'VALIDATED_SPEC_NOT_EXECUTED')
    def test_groove_cylinder(self):
        self.doc['operators'][-1]={'op':'groove_cylinder','part_id':'cutter_demo','target_part_id':'seat_base',
                                  'feature_id':'circular_groove','center_m':[0,0,.46],'radius_m':.02,'depth_m':.05}
        self.assertIn('circular_groove',validate_recipe(self.doc)['feature_ids'])


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.s={'schema_version':'1.3','project_id':'forge-chair-demo','expected_snapshot_sha256':'a'*64,
                'protected_part_ids':['seat_base'], 'changes':[{'part_id':'seat_cushion','translation_m':[0,0,.003]}]}
    def test_success(self):self.assertIn('seat_cushion',validate_repair(self.s)['affected_parts'])
    def test_missing_snapshot(self):
        self.s.pop('expected_snapshot_sha256')
        with self.assertRaisesRegex(ValueError,'required'):validate_repair(self.s)
    def test_stale_non_hash(self):
        self.s['expected_snapshot_sha256']='bad'
        with self.assertRaises(ValueError):validate_repair(self.s)
    def test_protected_target(self):
        self.s['changes'][0]['part_id']='seat_base'
        with self.assertRaisesRegex(ValueError,'locked'):validate_repair(self.s)
    def test_locked_scene_target(self):
        with self.assertRaisesRegex(ValueError,'locked'):validate_repair(self.s,locked={'seat_cushion'})
    def test_missing_scene_target(self):
        with self.assertRaisesRegex(ValueError,'not found'):validate_repair(self.s,available={'seat_base'})
    def test_bad_scale(self):
        self.s['changes'][0]['scale_xyz']=[1,0,1]
        with self.assertRaises(ValueError):validate_repair(self.s)
    def test_unrecognized_operation(self):
        self.s['changes'][0]['bpy_expression']='bpy.ops.delete'
        with self.assertRaisesRegex(ValueError,'unknown'):validate_repair(self.s)
    def test_same_target_twice(self):
        self.s['changes'].append(copy.deepcopy(self.s['changes'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate'):validate_repair(self.s)
    def test_no_real_operation(self):
        self.s['changes'][0].pop('translation_m')
        with self.assertRaisesRegex(ValueError,'no operation'):validate_repair(self.s)
    def test_empty_changes(self):
        self.s['changes']=[]
        with self.assertRaises(ValueError):validate_repair(self.s)


class LodTests(unittest.TestCase):
    def setUp(self):self.s=sample('chair_lods_demo.json')
    def test_valid(self):self.assertEqual(validate_lod(self.s)['lod_count'],3)
    def test_duplicate_ratio(self):
        self.s['ratios']=[.5,.5]
        with self.assertRaisesRegex(ValueError,'decrease'):validate_lod(self.s)
    def test_wrong_order(self):
        self.s['ratios']=[.3,.8]
        with self.assertRaisesRegex(ValueError,'decrease'):validate_lod(self.s)
    def test_zero_ratio(self):
        self.s['ratios']=[0]
        with self.assertRaises(ValueError):validate_lod(self.s)
    def test_duplicate_protected(self):
        self.s['protected_part_ids']=['seat_seam','seat_seam']
        with self.assertRaises(ValueError):validate_lod(self.s)
    def test_untrusted_expression_rejected(self):
        self.s['python']='open()'
        with self.assertRaises(ValueError):validate_lod(self.s)


class VariantTests(unittest.TestCase):
    def setUp(self):self.s=sample('chair_variant_family.json');self.sel=sample('chair_variant_selected.json')
    def test_valid_resolution(self):
        result=resolve_variant(self.s,self.sel)
        self.assertEqual(result['status'],'VALIDATED_SELECTION_NOT_BUILT')
        self.assertEqual(result['material_overrides']['back_cushion'],'fabric')
        self.assertEqual(result['theoretical_combinations'],4)
    def test_forbidden(self):
        self.sel['seat']='without_pad'
        self.assertEqual(resolve_variant(self.s,self.sel)['status'],'BLOCKED')
    def test_allowed_alternate(self):
        self.sel.update({'seat':'without_pad','upholstery':'steel'})
        self.assertEqual(resolve_variant(self.s,self.sel)['status'],'VALIDATED_SELECTION_NOT_BUILT')
    def test_unknown_option(self):
        self.sel['seat']='jet_engine'
        with self.assertRaises(ValueError):resolve_variant(self.s,self.sel)
    def test_missing_slot(self):
        self.sel.pop('seat')
        with self.assertRaises(ValueError):resolve_variant(self.s,self.sel)
    def test_conflicting_visibility(self):
        self.s['slots']['upholstery']['options']['fabric']['hide_part_ids']=['seat_cushion']
        self.assertEqual(resolve_variant(self.s,self.sel)['status'],'BLOCKED')
    def test_conflicting_materials(self):
        self.s['slots']['seat']['options']['standard']['material_overrides']={'back_cushion':'steel'}
        self.assertEqual(resolve_variant(self.s,self.sel)['status'],'BLOCKED')
    def test_rule_invalid_option(self):
        self.s['rules'][0]['forbid']={'upholstery':'unknown'}
        with self.assertRaises(ValueError):validate_variant_config(self.s)
    def test_oppositional_same_part_in_option(self):
        self.s['slots']['seat']['options']['standard']['hide_part_ids']=['seat_cushion']
        with self.assertRaises(ValueError):validate_variant_config(self.s)
    def test_malicious_path_rejected(self):
        self.s['slots']['seat']['options']['standard']['script_path']='/tmp/exec'
        with self.assertRaisesRegex(ValueError,'unknown'):validate_variant_config(self.s)
    def test_theoretical_combinations_not_generated(self):
        self.assertEqual(validate_variant_config(self.s)['status'],'VALIDATED_SPEC_NOT_EXECUTED')


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.s=sample('chair_assembly_demo.json')
        self.inspect={'status':'MEASURED_NOT_APPROVED','parts':[
            {'part_id':'seat_base','world_bbox_min_m':[-.3,-.2,.42],'world_bbox_max_m':[.3,.2,.48]},
            {'part_id':'seat_cushion','world_bbox_min_m':[-.3,-.2,.485],'world_bbox_max_m':[.3,.2,.56]},
            {'part_id':'back_cushion','world_bbox_min_m':[-.28,.2,.55],'world_bbox_max_m':[.28,.3,.98]}]}
    def test_valid(self):self.assertEqual(validate_assembly(self.s)['constraints'],2)
    def test_proxy_pass(self):
        self.assertEqual(audit_assembly(self.s,self.inspect)['status'],'PROXY_CHECKED_NOT_CERTIFIED')
    def test_far_apart(self):
        self.inspect['parts'][1]['world_bbox_min_m'][2]=1.0
        self.inspect['parts'][1]['world_bbox_max_m'][2]=1.1
        self.assertEqual(audit_assembly(self.s,self.inspect)['status'],'FAIL')
    def test_missing_part(self):
        self.inspect['parts'].pop()
        self.assertEqual(audit_assembly(self.s,self.inspect)['status'],'INDETERMINATE')
    def test_overlap_cannot_prove_clearance(self):
        self.s['constraints']=[{'id':'touch_clearance','kind':'clearance','part_a':'seat_base','part_b':'seat_cushion','min_clearance_mm':0}]
        self.inspect['parts'][1]['world_bbox_min_m'][2]=.45
        self.assertEqual(audit_assembly(self.s,self.inspect)['status'],'INDETERMINATE')
    def test_unverified_inspection_refused(self):
        self.inspect['status']='PASS'
        with self.assertRaises(ValueError):audit_assembly(self.s,self.inspect)
    def test_duplicate_constraints(self):
        self.s['constraints'].append(copy.deepcopy(self.s['constraints'][0]))
        with self.assertRaises(ValueError):validate_assembly(self.s)
    def test_unsupported_mechanical_claim(self):
        self.s['constraints'][0]['kind']='mesh_collision_exact'
        with self.assertRaises(ValueError):validate_assembly(self.s)


class AlignmentTests(unittest.TestCase):
    def setUp(self):self.s=sample('alignment_synthetic_2d.json')
    def test_incomplete_calibration_indeterminate(self):self.assertEqual(align(self.s)['status'],'INDETERMINATE')
    def test_declared_ortho_known_transform(self):
        self.s['camera_verified']=True;self.s['verified_by']='technician-demo'
        a=align(self.s)
        self.assertEqual(a['status'],'LANDMARK_ALIGNED_PENDING_VISUAL')
        self.assertAlmostEqual(a['pixels_per_meter'],400,places=4)
        self.assertAlmostEqual(a['rms_error_px'],0,places=4)
    def test_perspective_cannot_claim_orthographic(self):
        self.s['camera_verified']=True;self.s['verified_by']='technician-demo';self.s['projection']='perspective'
        self.assertEqual(align(self.s)['status'],'INDETERMINATE')
    def test_outlier_indeterminate(self):
        self.s['camera_verified']=True;self.s['verified_by']='technician-demo'
        self.s['landmarks'][1]['pixel_xy']=[990,990]
        self.assertEqual(align(self.s)['status'],'INDETERMINATE')
    def test_degenerate_model_landmarks(self):
        for p in self.s['landmarks']:p['model_xy_m']=[0,0]
        with self.assertRaises(ValueError):align(self.s)
    def test_duplicate_name(self):
        self.s['landmarks'][1]['id']=self.s['landmarks'][0]['id']
        with self.assertRaises(ValueError):align(self.s)
    def test_only_two_landmarks(self):
        self.s['landmarks']=self.s['landmarks'][:2]
        with self.assertRaises(ValueError):align(self.s)
    def test_unknown_view(self):
        self.s['view']='three_quarter'
        with self.assertRaises(ValueError):align(self.s)
    def test_any_missing_pixel_refused(self):
        self.s['landmarks'][1].pop('pixel_xy')
        with self.assertRaises(ValueError):align(self.s)


@unittest.skipUnless(importlib.util.find_spec('PIL'),'Pillow optional')
class RegressionTests(unittest.TestCase):
    def setUp(self):
        from PIL import Image
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        Image.new('RGBA',(10,10),(0,0,0,255)).save(self.root/'old.png')
        Image.new('RGBA',(10,10),(0,0,0,255)).save(self.root/'new.png')
        self.s={'schema_version':'1.3','render_profile':'same-clay-2026', 'camera_verified':True,
                'required_views':['front','back'], 'pixel_tolerance':3,'max_changed_fraction':0.01,
                'views':[{'name':'front','before':'old.png','after':'new.png'},
                         {'name':'back','before':'old.png','after':'new.png'}]}
    def tearDown(self):self.tmp.cleanup()
    def test_same_image_passes(self):
        self.assertEqual(regress(self.s,self.root)['status'],'PASS_MEASURED_NOT_ARTISTIC_QA')
    def test_change_fails(self):
        from PIL import Image
        Image.new('RGBA',(10,10),(255,255,255,255)).save(self.root/'new.png')
        self.assertEqual(regress(self.s,self.root)['status'],'FAIL')
    def test_mismatched_camera_indeterminate(self):
        self.s['camera_verified']=False
        self.assertEqual(regress(self.s,self.root)['status'],'INDETERMINATE')
    def test_missing_view(self):
        self.s['views'].pop()
        self.assertEqual(regress(self.s,self.root)['status'],'INDETERMINATE')
    def test_invalid_file(self):
        self.s['views'][0]['after']='missing.png'
        with self.assertRaises(ValueError):regress(self.s,self.root)
    def test_protected_mask_only(self):
        from PIL import Image
        im=Image.new('RGBA',(10,10),(0,0,0,255));im.putpixel((0,0),(200,10,10,255));im.save(self.root/'new.png')
        mask=Image.new('L',(10,10),0)
        for x in range(5,10):
            for y in range(5,10):mask.putpixel((x,y),255)
        mask.save(self.root/'mask.png')
        for v in self.s['views']:v['protected_mask']='mask.png'
        self.assertEqual(regress(self.s,self.root)['status'],'PASS_MEASURED_NOT_ARTISTIC_QA')
    def test_protected_pixel_fails(self):
        from PIL import Image
        im=Image.new('RGBA',(10,10),(0,0,0,255));im.putpixel((0,0),(100,10,10,255));im.save(self.root/'new.png')
        mask=Image.new('L',(10,10),0);mask.putpixel((0,0),255);mask.save(self.root/'mask.png')
        for v in self.s['views']:v['protected_mask']='mask.png'
        self.assertEqual(regress(self.s,self.root)['status'],'FAIL')
    def test_empty_mask_invalid(self):
        from PIL import Image
        Image.new('L',(10,10),0).save(self.root/'mask.png')
        self.s['views'][0]['protected_mask']='mask.png'
        with self.assertRaises(ValueError):regress(self.s,self.root)
    def test_unsafe_image_path(self):
        self.s['views'][0]['before']='../../passwd'
        with self.assertRaises(ValueError):regress(self.s,self.root)


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'result.glb').write_bytes(glb_bytes())
        self.record={'schema_version':'1.3','case_id':'TECH-CHAIR','state':'EXECUTED_PENDING_VISUAL','engine':'Blender',
                     'blender_version':'4.5','source_reference_ids':['ref-front'],'operator_log':['run-build'],
                     'metrics':{'dimension_error_mm':2,'missing_required_parts':0,'triangle_count':1200,
                                'correction_cycles':3,'minutes_elapsed':4},
                     'artifacts':[{'path':'result.glb','sha256':hashlib.sha256((self.root/'result.glb').read_bytes()).hexdigest()}]}
    def tearDown(self):self.tmp.cleanup()
    def add_visual_artifact(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow not installed')
        dst=self.root/'view.png';Image.new('RGB',(8,8),(123,123,123)).save(dst)
        self.record['artifacts'].append({'path':'view.png','sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
    def test_not_executed_truthful(self):
        self.assertEqual(validate_run(sample('benchmark_not_executed.json'),self.root)['status'],'NOT_EXECUTED')
    def test_good_measurement_pending_visual(self):
        self.assertEqual(validate_run(self.record,self.root)['status'],'EXECUTED_PENDING_VISUAL')
    def test_missing_engine(self):
        self.record.pop('blender_version')
        self.assertEqual(validate_run(self.record,self.root)['status'],'FAIL')
    def test_missing_metric(self):
        self.record['metrics'].pop('dimension_error_mm')
        self.assertEqual(validate_run(self.record,self.root)['status'],'FAIL')
    def test_bad_hash(self):
        self.record['artifacts'][0]['sha256']='bad'
        self.assertEqual(validate_run(self.record,self.root)['status'],'FAIL')
    def test_wrong_reference_file_path(self):
        self.record['artifacts'][0]['path']='../../secret'
        self.assertEqual(validate_run(self.record,self.root)['status'],'FAIL')
    def test_visual_review_requires_two_reviewers(self):
        self.record['state']='VISUALLY_REVIEWED'
        self.record['reviewers']=['one']
        self.record['artistic_scores']=[{'reviewer':'one','reference_fidelity_0_100':50}]
        self.assertEqual(validate_run(self.record,self.root)['status'],'FAIL')
    def test_two_reviews_and_score(self):
        self.record['state']='VISUALLY_REVIEWED';self.record['reviewers']=['one','two']
        self.add_visual_artifact()
        self.record['artistic_scores']=[{'reviewer':'one','reference_fidelity_0_100':70},
                                        {'reviewer':'two','reference_fidelity_0_100':65}]
        self.assertEqual(validate_run(self.record,self.root)['status'],'READY_FOR_COMPARATIVE_ANALYSIS')
    def test_blinded_comparison_requires_reviews(self):
        self.assertEqual(compare_runs(self.record,self.record,self.root)['status'],'INDETERMINATE')
    def test_comparison_differences(self):
        self.record['state']='VISUALLY_REVIEWED';self.record['reviewers']=['one','two']
        self.add_visual_artifact()
        self.record['artistic_scores']=[{'reviewer':'one','reference_fidelity_0_100':70},
                                        {'reviewer':'two','reference_fidelity_0_100':65}]
        other=copy.deepcopy(self.record);other['metrics']['dimension_error_mm']=1
        res=compare_runs(self.record,other,self.root)
        self.assertEqual(res['status'],'COMPARISON_MEASURED_NOT_CAUSAL')
        self.assertEqual(res['deltas_candidate_minus_baseline']['dimension_error_mm'],-1)
    def test_mismatched_case_rejected(self):
        self.record['state']='VISUALLY_REVIEWED';self.record['reviewers']=['one','two']
        self.add_visual_artifact()
        self.record['artistic_scores']=[{'reviewer':'one','reference_fidelity_0_100':70},
                                        {'reviewer':'two','reference_fidelity_0_100':65}]
        other=copy.deepcopy(self.record);other['case_id']='HARD-SURFACE'
        self.assertEqual(compare_runs(self.record,other,self.root)['status'],'INDETERMINATE')


class BridgeAndCliTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.d=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def test_bridge_requires_spec(self):
        with self.assertRaises(ValueError):prepare_argv('blender','build-recipe',self.d)
    def test_bridge_compile(self):
        f=self.d/'recipe.json';f.write_text('{}')
        v=prepare_argv('blender','build-recipe',self.d,spec=str(f))
        self.assertIn('build-recipe',v);self.assertIn('--spec',v)
    def test_bridge_repair_requires_blend(self):
        f=self.d/'recipe.json';f.write_text('{}')
        with self.assertRaises(ValueError):prepare_argv('blender','apply-repair',self.d,spec=str(f))
    def test_bridge_rejects_arbitrary_task(self):
        with self.assertRaises(ValueError):prepare_argv('blender','exec-python',self.d)
    def test_bridge_rejects_spec_on_inspect(self):
        f=self.d/'recipe.json';f.write_text('{}');bl=self.d/'demo.blend';bl.write_bytes(b'blend')
        with self.assertRaises(ValueError):prepare_argv('blender','inspect',self.d,blend=bl,spec=str(f))
    def test_bridge_refuses_oversize(self):
        f=self.d/'large.json';f.write_bytes(b'x'*256001)
        with self.assertRaises(ValueError):prepare_argv('blender','build-recipe',self.d,spec=str(f))
    def test_cli_recipe(self):
        cp=subprocess.run([sys.executable,str(ROOT/'scripts/forge_upgrade.py'),'recipe',str(ROOT/'examples/upgrades/chair_procedural_demo.json')],capture_output=True,text=True)
        self.assertEqual(cp.returncode,0);self.assertIn('VALIDATED_SPEC_NOT_EXECUTED',cp.stdout)
    def test_cli_not_executed_benchmark_failclosed(self):
        cp=subprocess.run([sys.executable,str(ROOT/'scripts/forge_upgrade.py'),'benchmark',str(ROOT/'examples/upgrades/benchmark_not_executed.json')],capture_output=True,text=True)
        self.assertEqual(cp.returncode,2);self.assertIn('NOT_EXECUTED',cp.stdout)
    def test_cli_variant_selection(self):
        cp=subprocess.run([sys.executable,str(ROOT/'scripts/forge_upgrade.py'),'variant-selection',
                           str(ROOT/'examples/upgrades/chair_variant_family.json'), '--selection',
                           str(ROOT/'examples/upgrades/chair_variant_selected.json')],capture_output=True,text=True)
        self.assertEqual(cp.returncode,0)
    def test_bridge_worker_tasks_wired(self):
        s=(ROOT/'scripts/blender_worker.py').read_text()
        for task in ['build-recipe','apply-repair','create-lods','build-variant','assembly-audit']:
            self.assertIn(task,s)
    def test_eight_skills_preserved(self):
        for name in ['reference-analyst','geometry-architect','sculpt-surface','material-specialist','topology-engineer','rigging-specialist','fidelity-auditor','export-engineer']:
            self.assertTrue((ROOT/'skills'/name/'SKILL.md').is_file())


if __name__=='__main__':unittest.main()
