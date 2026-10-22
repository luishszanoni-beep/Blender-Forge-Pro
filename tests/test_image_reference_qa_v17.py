"""G1-R structure and handoff tests. Never interpret these as semantic image/anatomy tests."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from gcb_image_qa import evaluate, handoff

# PNG dimensions/header sufficient for offline file signature smoke checks.
PNG_HEADER=bytes.fromhex('89504e470d0a1a0a') + (13).to_bytes(4,'big') + b'IHDR' + (1).to_bytes(4,'big') + (1).to_bytes(4,'big') + bytes(16)


class ImageReferenceQATests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'input').mkdir()
        (self.root/'input/front.png').write_bytes(PNG_HEADER)
        self.manifest={
            'schema_version':'1.0','project_id':'dragon_demo','subject_type':'creature',
            'purpose':'image_references_for_3d',
            'images':[{'id':'R1','path':'input/front.png','view':'front','projection':'unknown','origin':'generated_design','confidence':'inferred','calibrated':False}],
            'parts':[{'id':'BODY','label':'Corpo','image_ids':['R1'],'primitive':'box','confidence':'inferred',
                      'structural_note':'Montagem central e apoio dos membros','build_instruction':'Gerar base em box, ajustar faces e eixos',
                      'connection_ids':[],'moving':False,'separate_mesh':True,'pivot':None},
                     {'id':'HEAD','label':'Cabeca','image_ids':['R1'],'primitive':'wedge','confidence':'inferred',
                      'structural_note':'Haste ligada ao pescoco','build_instruction':'Criar cunha separada com loops de borda',
                      'connection_ids':['BODY'],'moving':True,'separate_mesh':True,'pivot':[0,0,0]}],
            'modeling_steps':[{'id':'S1','part_ids':['BODY'],'instruction':'Modelar bloco base','acceptance':'Conferir silhueta e tamanho'},
                              {'id':'S2','part_ids':['HEAD'],'instruction':'Adicionar cabeca independente','acceptance':'Pivo posicionado e corpo sem fusao'}],
            'checks':[{'category':c,'status':'PASS','image_ids':['R1'],'part_ids':['BODY'],
                       'note':'Inspecao em render validou coerencia nominal'} for c in
                     ('identity','anatomy','connections','articulation','views','geometry','surface','handoff')],
            'review':{'status':'approved','reviewer_role':'fidelity-auditor',
                      'inspected_image_ids':['R1'],'notes':'Pecas verificadas contra a referencia visual','blockers':[]}
        }

    def evaluate(self, data=None):
        return evaluate(data if data is not None else self.manifest, self.root)

    def test_approved_contract_records_review_not_fake_image_test(self):
        r=self.evaluate()
        self.assertEqual(r['status'],'REVIEW_DECLARED_APPROVED')
        self.assertTrue(r['ready_for_gcb'])
        self.assertFalse(r['visual_anatomy_tested_by_script'])
        self.assertEqual(len(r['image_files']),1)

    def test_pending_does_not_release(self):
        self.manifest['review']['status']='pending'
        r=self.evaluate()
        self.assertEqual(r['status'],'PENDING_VISUAL_QA')
        self.assertFalse(r['ready_for_gcb'])

    def test_rejected_does_not_release(self):
        self.manifest['review']['status']='rejected'
        self.manifest['review']['blockers']=['pata extra no plano frontal']
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_fake_artwork_file_cannot_pass(self):
        (self.root/'input/front.png').write_text('I am not a PNG')
        self.assertTrue(any('malformed' in e for e in self.evaluate()['errors']))

    def test_missing_file_blocked(self):
        self.manifest['images'][0]['path']='input/not-here.png'
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_path_escape_blocked(self):
        self.manifest['images'][0]['path']='../../secrets.png'
        self.assertTrue(any('unsafe path' in e for e in self.evaluate()['errors']))

    def test_symlink_escape_blocked(self):
        self.manifest['images'][0]['path']='input/outside.png'
        outside=self.root.parent/'secret-outside.png'
        outside.write_bytes(PNG_HEADER)
        self.addCleanup(lambda:outside.unlink(missing_ok=True))
        (self.root/'input/outside.png').symlink_to(outside)
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_duplicate_images_block(self):
        self.manifest['images'].append(dict(self.manifest['images'][0]))
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_inferred_image_cannot_claim_observed(self):
        self.manifest['images'][0].update(origin='generated_inferred',confidence='observed')
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_inferred_generated_view_requires_source_id(self):
        self.manifest['images'][0]['origin']='generated_inferred'
        self.assertFalse(self.evaluate()['ready_for_gcb'])
        self.manifest['images'][0]['based_on_ids']=['R0']
        self.assertFalse(self.evaluate()['ready_for_gcb'])
        self.manifest['images'].insert(0,{'id':'R0','path':'input/front.png','view':'side',
             'projection':'unknown','origin':'user_original','confidence':'observed','calibrated':False})
        self.manifest['review']['inspected_image_ids']=['R0','R1']
        self.assertTrue(self.evaluate()['ready_for_gcb'])

    def test_generated_art_cannot_claim_calibrated_mm(self):
        self.manifest['images'][0]['calibrated']=True
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_duplicate_part_id_blocked(self):
        self.manifest['parts'][1]['id']='BODY'
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_required_separate_articulated_mesh(self):
        self.manifest['parts'][1]['separate_mesh']=False
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_unknown_connection_blocked(self):
        self.manifest['parts'][1]['connection_ids']=['UNKNOWN_PART']
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_missing_step_for_part_blocked(self):
        self.manifest['modeling_steps'].pop()
        self.assertTrue(any('unplanned part' in x for x in self.evaluate()['errors']))

    def test_missing_qa_category_blocked(self):
        self.manifest['checks']=[x for x in self.manifest['checks'] if x['category']!='anatomy']
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_failed_check_cannot_be_approved(self):
        self.manifest['checks'][1]['status']='FAIL'
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_no_reviewed_images_cannot_be_approved(self):
        self.manifest['review']['inspected_image_ids']=[]
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_manifest_image_hash_mismatch(self):
        self.manifest['images'][0]['sha256']='0'*64
        self.assertFalse(self.evaluate()['ready_for_gcb'])

    def test_optional_gcb_id_must_exist(self):
        self.manifest['parts'][0]['gcb_part_id']='MISSING'
        gcb={'parts':[{'id':'BODY'},{'id':'HEAD'}]}
        r=evaluate(self.manifest,self.root,gcb)
        self.assertFalse(r['ready_for_gcb'])

    def test_handoff_lists_steps_and_parts(self):
        r=self.evaluate()
        txt=handoff(self.manifest,r)
        self.assertIn('HEAD',txt)
        self.assertIn('S2',txt)
        self.assertIn('input/front.png',txt)
        self.assertIn('nunca validado apenas por imagem',txt)

    def test_cli_preflight_and_handoff(self):
        manifest=self.root/'imgqa.json'
        manifest.write_text(json.dumps(self.manifest),encoding='utf-8')
        out=self.root/'qa_report.json'
        cmd=[sys.executable,str(ROOT/'scripts/gcb_image_qa.py'),'validate',str(manifest),'--root',str(self.root),'--out',str(out)]
        p=subprocess.run(cmd,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        rep=json.loads(out.read_text())
        self.assertTrue(rep['ready_for_gcb'])
        text_path=self.root/'codex_image_reference_handoff.md'
        cmd=[sys.executable,str(ROOT/'scripts/gcb_image_qa.py'),'handoff',str(manifest),'--root',str(self.root),'--out',str(text_path)]
        p2=subprocess.run(cmd,text=True,capture_output=True)
        self.assertEqual(p2.returncode,0,p2.stdout+p2.stderr)
        self.assertIn('HEAD',text_path.read_text())

    def test_gcb_prepare_blocks_unreviewed_image_qa(self):
        source = ROOT/'examples/gcb/demo_bloxy_plant.json'
        if not source.exists():
            self.skipTest('GCB v1.5 base files not present until plugin overlay merge')
        report=self.root/'pending_reference_qa.json'
        report.write_text(json.dumps({'status':'PENDING_VISUAL_QA','ready_for_gcb':False,'project_id':'demo-bloxy-plant','image_files':[]}),encoding='utf-8')
        out=self.root/'gcb_out'
        p=subprocess.run([sys.executable,str(ROOT/'scripts/gcb.py'),'prepare',str(source),'--out',str(out),
                          '--reference-qa-report',str(report)],capture_output=True,text=True)
        self.assertEqual(p.returncode,5,p.stdout+p.stderr)
        self.assertFalse((out/'gcb_spec.json').exists())

    def test_gcb_prepare_rejects_unrelated_qa_project(self):
        source=ROOT/'examples/gcb/demo_bloxy_plant.json'
        if not source.exists():self.skipTest('base GCB fixture not present')
        report=self.root/'other_reference_qa.json'
        report.write_text(json.dumps({'status':'REVIEW_DECLARED_APPROVED','ready_for_gcb':True,'project_id':'unrelated_project',
                                      'errors':[],'image_files':[{'id':'R1','path':'input/front.png'}]}),encoding='utf-8')
        out=self.root/'gcb_out'
        p=subprocess.run([sys.executable,str(ROOT/'scripts/gcb.py'),'prepare',str(source),'--out',str(out),
                          '--reference-qa-report',str(report)],capture_output=True,text=True)
        self.assertEqual(p.returncode,5,p.stdout+p.stderr)

    def test_gcb_prepare_uses_approved_reference_qa_and_preserves_visual_qa_pending(self):
        source=ROOT/'examples/gcb/demo_bloxy_plant.json'
        if not source.exists():self.skipTest('base GCB fixture not present')
        report=self.root/'ok_reference_qa.json'
        report.write_text(json.dumps({'status':'REVIEW_DECLARED_APPROVED','ready_for_gcb':True,
                            'project_id':'demo-bloxy-plant','errors':[],
                            'image_files':[{'id':'R1','path':'input/front.png'}]}),encoding='utf-8')
        out=self.root/'gcb_out'
        p=subprocess.run([sys.executable,str(ROOT/'scripts/gcb.py'),'prepare',str(source),'--out',str(out),
                          '--reference-qa-report',str(report)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        preflight=json.loads((out/'gcb_preflight.json').read_text())
        self.assertEqual(preflight['reference_image_qa'],'REVIEW_DECLARED_APPROVED')
        self.assertEqual(preflight['g1_5_approval'],'PENDING_INDEPENDENT_AUDIT')

    def test_cli_pending_exit_nonzero(self):
        self.manifest['review']['status']='pending'
        manifest=self.root/'imgqa.json'
        manifest.write_text(json.dumps(self.manifest),encoding='utf-8')
        p=subprocess.run([sys.executable,str(ROOT/'scripts/gcb_image_qa.py'),'validate',str(manifest),'--root',str(self.root)],capture_output=True,text=True)
        self.assertEqual(p.returncode,4)


if __name__=='__main__':unittest.main()
