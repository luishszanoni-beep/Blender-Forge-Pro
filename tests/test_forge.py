import copy
import importlib.util
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from forge_core import read_json,validate_project,route_project,check_evidence,inside,build_manifest,verify_manifest
from check_glb import analyze
from compare_views import compare
from blender_bridge import prepare_argv,resolve_exe


def glb_bytes(*, count=3, malformed_json=False, external=False):
    raw=struct.pack('<9f',0,0,0,1,0,0,0,1,0)+struct.pack('<3H',0,1,2)
    asset={
      'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0}],
      'buffers':[{'byteLength':len(raw)}],
      'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':36},{'buffer':0,'byteOffset':36,'byteLength':6}],
      'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'},
                   {'bufferView':1,'componentType':5123,'count':count,'type':'SCALAR'}],
      'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1,'mode':4}]}],
    }
    if external:asset['buffers'][0]['uri']='data.bin'
    j=(b'{oops' if malformed_json else json.dumps(asset,separators=(',',':')).encode())
    j+=b' '*((-len(j))%4);raw+=b'\0'*((-len(raw))%4)
    body=struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(raw),b'BIN\0')+raw
    return b'glTF'+struct.pack('<II',2,len(body)+12)+body


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.p=read_json(ROOT/'examples/projects/demo_chair.json')
    def test_example_works_and_marks_uncalibrated(self):
        x=validate_project(self.p,ROOT);self.assertEqual(x['status'],'PASS');self.assertTrue(x['warnings'])
    def test_char_example_works(self):
        x=validate_project(read_json(ROOT/'examples/projects/demo_character.json'),ROOT);self.assertEqual(x['status'],'PASS')
    def test_rig_is_conditional(self):
        self.assertNotIn('rigging-specialist',route_project(self.p)['ordered_skills'])
        self.assertIn('rigging-specialist',route_project(read_json(ROOT/'examples/projects/demo_character.json'))['ordered_skills'])
    def test_routing_auditor_first_and_last(self):
        stages=route_project(self.p)['ordered_skills'];self.assertEqual(stages[-1],'fidelity-auditor');self.assertIn('export-engineer',stages)
    def test_missing_reference_fails(self):
        self.p['references'][0]['path']='examples/reference_images/missing.jpg'
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_allow_missing_reference_warns(self):
        self.p['references'][0]['path']='examples/reference_images/missing.jpg'
        x=validate_project(self.p,ROOT,allow_missing_refs=True);self.assertEqual(x['status'],'PASS');self.assertTrue(any('not provided' in y for y in x['warnings']))
    def test_empty_ref_when_matching_rejected(self):
        self.p['references']=[]
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_wrong_reference_id(self):
        self.p['parts'][0]['reference_ids']=['unknown-ref']
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_wrong_feature_reference_id(self):
        self.p['parts'][0]['features'][0]['source_ref_ids']=['bad']
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_duplicate_feature(self):
        self.p['parts'][1]['features'][0]['id']=self.p['parts'][0]['features'][0]['id']
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_duplicate_reference(self):
        self.p['references'][1]['id']=self.p['references'][0]['id']
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_traversal(self):
        self.p['references'][0]['path']='../bad.png'
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_absolute_reference(self):
        self.p['references'][0]['path']='/etc/passwd'
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_nonpos_dim(self):
        self.p['dimensions_mm']['width']=-1
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_bad_budget(self):
        self.p['budgets']['triangles_max']=0
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_invalid_geo_feature(self):
        self.p['parts'][0]['features'][0]['representation']='material'
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_invalid_view(self):
        self.p['checks']['required_views']=['imaginary']
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_glb_is_required_for_web(self):
        self.p['deliverables']=['blend']
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_reference_binary_signature(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'bogus.png').write_bytes(b'not a real PNG')
            p=copy.deepcopy(self.p);p['references']=[{'id':'ref-a','path':'bogus.png','view':'front','projection':'unknown'}]
            for part in p['parts']:
                part['reference_ids']=['ref-a']
                for f in part['features']:f['source_ref_ids']=['ref-a']
            self.assertEqual(validate_project(p,r)['status'],'FAIL')
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'real.txt').write_text('abc')
            try:(r/'link.txt').symlink_to(r/'real.txt')
            except (OSError,NotImplementedError):self.skipTest('symlink forbidden by host')
            with self.assertRaisesRegex(ValueError,'symlink'):
                inside(r,'link.txt',must_exist=True)
    def test_parent_escape(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):inside(Path(d),'../outside',must_exist=False)
    def test_missing_project_fields(self):
        self.p.pop('parts')
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')
    def test_invalid_rig_value(self):
        self.p['rig_required']='yes'
        self.assertEqual(validate_project(self.p,ROOT)['status'],'FAIL')


class GlbTests(unittest.TestCase):
    def check(self,blob):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'model.glb';path.write_bytes(blob)
            return analyze(path)
    def test_valid_triangle_glb(self):
        x=self.check(glb_bytes());self.assertEqual(x['status'],'PASS');self.assertEqual(x['counts']['estimated_triangles'],1)
    def test_truncation(self):self.assertEqual(self.check(glb_bytes()[:-11])['status'],'FAIL')
    def test_bad_header_magic(self):
        blob=b'x'+glb_bytes()[1:];self.assertEqual(self.check(blob)['status'],'FAIL')
    def test_bad_version(self):
        blob=bytearray(glb_bytes());struct.pack_into('<I',blob,4,1)
        self.assertEqual(self.check(blob)['status'],'FAIL')
    def test_malformed_json(self):self.assertEqual(self.check(glb_bytes(malformed_json=True))['status'],'FAIL')
    def test_external_buffer_fails(self):self.assertEqual(self.check(glb_bytes(external=True))['status'],'FAIL')
    def test_triangle_count_mismatch(self):self.assertEqual(self.check(glb_bytes(count=2))['status'],'FAIL')
    def test_missing_file(self):
        self.assertEqual(analyze(Path('/unfindable/example.glb'))['status'],'FAIL')
    def test_fake_binary_glb(self):self.assertEqual(self.check(b'GLB' * 100)['status'],'FAIL')


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.root=Path(self.d.name)
        self.p=read_json(ROOT/'examples/projects/demo_chair.json')
        for ref in self.p['references']:
            source=ROOT/ref['path'];dest=self.root/ref['path'];dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(source.read_bytes())
        self.e={'schema_version':'1.0','project_id':self.p['project_id'],
                'gates':{},'views':[],'geometry_proofs':[],'deliverables':[],
                'critical_blockers':[], 'final_review':{'decision':'APPROVED','reviewer':'fixture reviewer'}}
        (self.root/'qa').mkdir()
        (self.root/'qa/qa.png').write_bytes((ROOT/'examples/reference_images/chair_front.png').read_bytes())
        for i in range(9):
            self.e['gates'][f'G{i}']={'state':'SKIPPED_NOT_APPLICABLE' if i==6 else 'APPROVED',
                                    'evidence_files':[] if i<2 or i==6 else ['qa/qa.png']}
        for v in self.p['checks']['required_views']:
            self.e['views'].append({'view':v,'file':'qa/qa.png','inspected':True,'reviewer':'fixture reviewer'})
        for part in self.p['parts']:
            for f in part['features']:
                if f['required'] and f['representation']=='geometry':
                    self.e['geometry_proofs'].append({'part_id':part['id'],'feature_id':f['id'],
                        'evaluated_mesh_verified':True,'reviewed':True,'export_verified':True,
                        'evidence_files':['qa/qa.png']})
        (self.root/'deliverables').mkdir()
        (self.root/'deliverables/final.blend').write_bytes(b'BLENDER-v000: diagnostic contract fixture')
        (self.root/'deliverables/final.glb').write_bytes(glb_bytes())
        self.e['deliverables']=[{'format':'blend','path':'deliverables/final.blend'},
                                {'format':'glb','path':'deliverables/final.glb','roundtrip_checked':True}]
    def tearDown(self):self.d.cleanup()
    def test_complete_contract(self):
        res=check_evidence(self.p,self.e,self.root)
        self.assertEqual(res['status'],'PASS',res)
    def test_missing_geom_proof(self):
        self.e['geometry_proofs']=[]
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'FAIL')
    def test_export_proof_missing(self):
        self.e['geometry_proofs'][0]['export_verified']=False
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'FAIL')
    def test_not_inspected(self):
        self.e['views'][0]['inspected']=False
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'FAIL')
    def test_waiver_needs_user_authorization(self):
        self.e['views'].pop(0);self.e['user_waived_views']=['front']
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'FAIL')
        self.e['waiver_authorized_by_user']=True
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'PASS')
    def test_critical_blocker(self):
        self.e['critical_blockers']=[{'id':'lost-leg','severity':'fatal'}]
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'FAIL')
    def test_png_missing(self):
        (self.root/'qa/qa.png').unlink()
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'FAIL')
    def test_fake_blend_detected(self):
        (self.root/'deliverables/final.blend').write_bytes(b'not blender')
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'FAIL')
    def test_bad_glb_detected(self):
        (self.root/'deliverables/final.glb').write_bytes(b'glTF' + b'x'*24)
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'FAIL')
    def test_glb_reimport_required(self):
        self.e['deliverables'][1]['roundtrip_checked']=False
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'FAIL')
    def test_approval_gates_required(self):
        self.e['gates']['G3']['state']='PENDING'
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'FAIL')
    def test_approval_signature_required(self):
        self.e['final_review']['reviewer']=''
        self.assertEqual(check_evidence(self.p,self.e,self.root)['status'],'FAIL')
    def test_manifest_sha_success_and_corruption(self):
        m=build_manifest(self.root,['deliverables/final.blend','deliverables/final.glb'])
        self.assertEqual(verify_manifest(self.root,m)['status'],'PASS')
        (self.root/'deliverables/final.glb').write_bytes(b'bad')
        self.assertEqual(verify_manifest(self.root,m)['status'],'FAIL')
    def test_manifest_traversal_rejected(self):
        with self.assertRaises(ValueError):build_manifest(self.root,['../../secrets.txt'])
    def test_duplicate_manifest_path(self):
        with self.assertRaises(ValueError):build_manifest(self.root,['qa/qa.png','qa/qa.png'])


@unittest.skipUnless(importlib.util.find_spec('PIL') is not None,'Pillow optional')
class ComparisonTests(unittest.TestCase):
    def setUp(self):
        from PIL import Image,ImageDraw
        self.d=tempfile.TemporaryDirectory();self.root=Path(self.d.name)
        a=Image.new('L',(100,100),0);b=Image.new('L',(100,100),0)
        ImageDraw.Draw(a).rectangle((20,20,70,70),fill=255)
        ImageDraw.Draw(b).rectangle((25,20,75,70),fill=255)
        a.save(self.root/'a.png');b.save(self.root/'b.png')
        self.cal={'reference_id':'ref-front','view':'front','same_projection':True,'same_scale':True,'same_crop':True,'verified_by':'fixture author'}
    def tearDown(self):self.d.cleanup()
    def test_equal_masks_exact(self):
        self.assertEqual(compare(self.root/'a.png',self.root/'a.png',self.cal)['foreground_iou'],1)
    def test_shift_detected(self):
        res=compare(self.root/'a.png',self.root/'b.png',self.cal,self.root/'overlay.png')
        self.assertLess(res['foreground_iou'],1);self.assertTrue((self.root/'overlay.png').is_file())
    def test_uncalibrated_blocked(self):
        c=dict(self.cal,same_scale=False)
        self.assertEqual(compare(self.root/'a.png',self.root/'b.png',c)['status'],'INDETERMINATE')
    def test_no_reviewer_blocked(self):
        c=dict(self.cal,verified_by='')
        self.assertEqual(compare(self.root/'a.png',self.root/'b.png',c)['status'],'INDETERMINATE')
    def test_size_mismatch(self):
        from PIL import Image
        Image.new('L',(50,50),255).save(self.root/'small.png')
        self.assertEqual(compare(self.root/'a.png',self.root/'small.png',self.cal)['status'],'INDETERMINATE')


class PackagingAndRoutingTests(unittest.TestCase):
    def test_exactly_eight_skills_and_manifests(self):
        expected={'reference-analyst','geometry-architect','sculpt-surface','material-specialist',
                  'topology-engineer','rigging-specialist','fidelity-auditor','export-engineer'}
        self.assertEqual({x.name for x in (ROOT/'skills').iterdir() if x.is_dir()},expected)
        for slug in expected:
            d=ROOT/'skills'/slug
            source=(d/'SKILL.md').read_text()
            self.assertTrue(source.startswith('---\nname: '+slug+'\n'))
            self.assertIn('description: ',source)
            self.assertIn('## Production procedure',source)
            self.assertTrue((d/'references/acceptance-checklist.md').is_file())
            self.assertTrue((d/'agents/openai.yaml').is_file())
    def test_plugin_manifests_version(self):
        for f in ('plugin.json','.codex-plugin/plugin.json'):
            self.assertEqual(read_json(ROOT/f)['version'],'1.4.0')
    def test_shared_references_present(self):
        for f in ('workflow-gates','project-contract','fidelity-rubric','geometric-detail-proof','target-profiles','blender-execution','benchmark-plan','file-layout'):
            self.assertTrue((ROOT/'references'/f'{f}.md').is_file())
    def test_bridge_rejects_arbitrary_task(self):
        with self.assertRaises(ValueError):prepare_argv('/usr/bin/blender','execute-untrusted-script',Path('/tmp'))
    def test_bridge_requires_source(self):
        with self.assertRaises(ValueError):prepare_argv('/usr/bin/blender','inspect',Path('/tmp'))
    def test_bridge_no_overwrite_original(self):
        args=prepare_argv('/usr/bin/blender','diagnostic-sample',Path('/tmp'))
        self.assertIn('--disable-autoexec',args)
        self.assertTrue(args[args.index('--python')+1].endswith('blender_worker.py'))
    def test_bridge_doctor_graceful_if_missing(self):
        p=subprocess.run([sys.executable,str(ROOT/'scripts/blender_bridge.py'),'doctor','--blender','definitely-not-a-blender-xyz'],capture_output=True,text=True)
        self.assertEqual(p.returncode,3)
        self.assertIn('UNAVAILABLE',p.stdout)
    def test_default_example_metadata_probe(self):
        proc=subprocess.run([sys.executable,str(ROOT/'scripts/forge.py'),'validate-project','examples/projects/demo_chair.json','--root','.'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(proc.returncode,0)
    def test_compiles_bpy_worker_without_import(self):
        import py_compile
        py_compile.compile(str(ROOT/'scripts/blender_worker.py'),doraise=True)

if __name__=='__main__':unittest.main()

class BaselineLockTests(unittest.TestCase):
    def setUp(self):
        from check_baseline import compare
        self.compare=compare
        part={'name':'seat_upholstery','part_id':'seat','world_mesh_fingerprint':'a'*64,
              'world_bbox_min_m':[0,0,0],'world_bbox_max_m':[1,1,1],
              'materials':['fabric']}
        self.old={'status':'MEASURED_NOT_APPROVED','parts':[part]}
        self.new=copy.deepcopy(self.old)
        self.locks={'locked_parts':[{'part_id':'seat','lock_geometry':True,'max_bbox_delta_mm':1,'lock_materials':True}]}
    def test_identical_locked_mesh_passes(self):
        self.assertEqual(self.compare(self.old,self.new,self.locks)['status'],'PASS')
    def test_changed_world_mesh_fails(self):
        self.new['parts'][0]['world_mesh_fingerprint']='b'*64
        self.assertEqual(self.compare(self.old,self.new,self.locks)['status'],'FAIL')
    def test_move_within_tolerance(self):
        self.new['parts'][0]['world_bbox_min_m'][0]=0.0005
        self.assertEqual(self.compare(self.old,self.new,self.locks)['status'],'PASS')
    def test_bbox_beyond_tolerance(self):
        self.new['parts'][0]['world_bbox_max_m'][0]=1.015
        self.assertEqual(self.compare(self.old,self.new,self.locks)['status'],'FAIL')
    def test_material_change(self):
        self.new['parts'][0]['materials']=['gold']
        self.assertEqual(self.compare(self.old,self.new,self.locks)['status'],'FAIL')
    def test_material_change_not_locked(self):
        self.locks['locked_parts'][0]['lock_materials']=False
        self.new['parts'][0]['materials']=['gold']
        self.assertEqual(self.compare(self.old,self.new,self.locks)['status'],'PASS')
    def test_mesh_large_unverifiable(self):
        self.new['parts'][0]['world_mesh_fingerprint']='NOT_COMPUTED_LARGE'
        self.assertEqual(self.compare(self.old,self.new,self.locks)['status'],'FAIL')
    def test_missing_part_fails(self):
        self.new['parts']=[]
        self.assertEqual(self.compare(self.old,self.new,self.locks)['status'],'FAIL')
    def test_wrong_report_status_fails(self):
        self.old['status']='FAKE'
        self.assertEqual(self.compare(self.old,self.new,self.locks)['status'],'FAIL')
    def test_no_locks_fails(self):
        self.assertEqual(self.compare(self.old,self.new,{'locked_parts':[]})['status'],'FAIL')
    def test_geometry_proof_task_requires_feature(self):
        with self.assertRaisesRegex(ValueError,'feature-id'):
            prepare_argv('/usr/bin/blender','geometry-proof',Path('/tmp'),'nonexistent.blend')
    def test_geometry_proof_blocks_bad_feature_id(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'sample.blend';f.write_bytes(b'BLENDER' + b'1'*20)
            with self.assertRaisesRegex(ValueError,'safe --feature-id'):
                prepare_argv('/usr/bin/blender','geometry-proof',Path(d),f, '../bad')
            x=prepare_argv('/usr/bin/blender','geometry-proof',Path(d),f,'seam_01')
            self.assertIn('--feature-id',x)

class ImageIntegrityTests(unittest.TestCase):
    def setUp(self):
        from image_integrity import inspect
        self.inspect=inspect
        self.d=tempfile.TemporaryDirectory();self.root=Path(self.d.name)
        self.correct=(ROOT/'examples/reference_images/chair_front.png').read_bytes()
        (self.root/'good.png').write_bytes(self.correct)
    def tearDown(self):self.d.cleanup()
    def test_generated_reference_png_has_real_integrity(self):
        self.assertEqual(self.inspect(self.root/'good.png')['status'],'PASS')
    def test_png_header_only_is_rejected(self):
        (self.root/'bad.png').write_bytes(self.correct[:26])
        self.assertEqual(self.inspect(self.root/'bad.png')['status'],'FAIL')
    def test_crc_corruption_fails(self):
        bad=bytearray(self.correct);bad[120]=bad[120]^1
        (self.root/'bad.png').write_bytes(bad)
        self.assertEqual(self.inspect(self.root/'bad.png')['status'],'FAIL')
    def test_fake_jpg_mismatch_fails(self):
        (self.root/'bad.jpg').write_bytes(self.correct)
        self.assertNotEqual(self.inspect(self.root/'bad.jpg')['status'],'PASS')
    def test_missing_reference_fails(self):
        self.assertEqual(self.inspect(self.root/'none.png')['status'],'FAIL')
    def test_png_trailing_bytes_fails(self):
        (self.root/'bad.png').write_bytes(self.correct+b'garbage')
        self.assertEqual(self.inspect(self.root/'bad.png')['status'],'FAIL')

@unittest.skipUnless(importlib.util.find_spec('trimesh') is not None, 'trimesh optional integration')
class ExternalGLBIntegrationTests(unittest.TestCase):
    def test_real_trimesh_export_has_one_box_twelve_triangles(self):
        import trimesh
        mesh=trimesh.creation.box(extents=(.4,.3,.2))
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'sample.glb';dest.write_bytes(mesh.export(file_type='glb'))
            report=analyze(dest)
            self.assertEqual(report['status'],'PASS',report)
            self.assertEqual(report['counts']['estimated_triangles'],12)
