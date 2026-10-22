"""Atlas v1.8 tests: deterministic retrieval/handoff, NOT Blender or visual QA."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from blender_tool_router import INDEX, load_index, route, plan_gcb, report_markdown, version_state

class AtlasToolSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index=load_index()

    def test_exact_inventory(self):
        i=self.index
        self.assertEqual(i['tool_count'],407)
        self.assertEqual([x['id'] for x in i['tools']],list(range(1,408)))
        self.assertEqual(i['chapter_count'],16)
        self.assertEqual(len(i['workspaces']),11)
        self.assertEqual(len(set(x['name'] for x in i['workspaces'])),11)

    def test_every_entry_has_traceable_fields(self):
        for item in self.index['tools']:
            for field in ('name','function','applications','when','reason','correct_usage','life_hack','page','chapter_id'):
                self.assertTrue(item[field],f'{item["id"]} missing {field}')
            self.assertTrue(5<=item['page']<=68)

    def test_pdf_hash_matches_immutable_source(self):
        p=ROOT/self.index['source']['pdf_path']
        self.assertTrue(p.is_file())
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.index['source']['sha256'])

    def test_critical_entries_correct_and_on_source_pages(self):
        names={i:x['name'] for i,x in enumerate(self.index['tools'],1)}
        self.assertEqual(names[72],'Solidify Modifier')
        self.assertEqual(names[392],'Export FBX')
        self.assertEqual(names[393],'Export glTF 2.0 / GLB')
        self.assertEqual(names[403],'Roblox Studio Import Validation')

    def test_wing_modeling_prefers_geometry_not_export(self):
        r=route(self.index,'asa membrana dragão espessura',stage='G2',target='roblox',limit=4)
        ids=[t['tool_id'] for t in r['tools']]
        self.assertIn(72,ids)
        self.assertNotIn(403,ids)
        self.assertNotIn(392,ids)
        self.assertEqual(r['status'],'RECOMMENDATIONS_ONLY_NOT_EXECUTED')
        self.assertTrue(all(x['bpy_operator_verified'] is False for x in r['tools']))

    def test_export_roblox_suggests_export_and_import_validation(self):
        r=route(self.index,'exportar rig FBX para Roblox',stage='G8',target='roblox',limit=8)
        ids=[v['tool_id'] for v in r['tools']]
        self.assertIn(392,ids)
        self.assertIn(403,ids)

    def test_skin_material_routes_in_shading_gate(self):
        r=route(self.index,'material PBR magma emission',stage='G4',target='roblox',limit=8)
        ids=[v['tool_id'] for v in r['tools']]
        self.assertIn(189,ids)
        self.assertIn(211,ids)

    def test_mismatch_does_not_claim_api_support(self):
        r=route(self.index,'Boolean para recorte',stage='G2',installed_version='4.5.0')
        self.assertEqual(r['runtime']['status'],'VERSION_MISMATCH')
        self.assertFalse(r['tools'][0]['bpy_operator_verified'])
        self.assertEqual(version_state('5.2.2','5.2.3')['status'],'FAMILY_MATCH_API_UNVERIFIED')
        self.assertEqual(version_state('5.2.2',None)['status'],'UNVERIFIED_RUNTIME')

    def test_rejects_bad_request(self):
        for kwargs in ({'query':''},{'query':'face','stage':'G999'},{'query':'face','target':'unk'},{'query':'face','limit':0}):
            with self.assertRaises(ValueError):route(self.index,**kwargs)

    def test_gcb_plan_preserves_stage_parts_and_is_advisory(self):
        spec=json.loads((ROOT/'examples/gcb/demo_bloxy_plant.json').read_text(encoding='utf-8'))
        p=plan_gcb(self.index,spec,installed_version='5.2.2')
        self.assertEqual(p['status'],'ADVISORY_UNVERIFIED_API_NOT_EXECUTED')
        self.assertEqual(len(p['steps']),len(spec['steps']))
        self.assertEqual(p['project_id'],spec['project_id'])
        self.assertIn('API',report_markdown(p))

    def test_cli_verify_index(self):
        proc=subprocess.run([sys.executable,str(ROOT/'scripts/blender_tool_router.py'),'verify-index'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertEqual(json.loads(proc.stdout)['status'],'VALID_INDEX_PDF_MATCH')

    def test_cli_gcb_prepare_writes_handoff_without_green_qa(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'gcb'
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/gcb.py'),'prepare',
                str(ROOT/'examples/gcb/demo_bloxy_plant.json'),'--out',str(path)],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            self.assertTrue((path/'blender_tool_plan.json').is_file())
            self.assertTrue((path/'blender_tool_plan.md').is_file())
            self.assertIn('blender_tool_plan.json',(path/'gcb_handoff.md').read_text())
            pre=json.loads((path/'gcb_preflight.json').read_text())
            self.assertEqual(pre['atlas_tool_selection'],'ADVISORY_UNVERIFIED_API_NOT_EXECUTED')
            self.assertEqual(pre['g1_5_approval'],'PENDING_INDEPENDENT_AUDIT')
            self.assertFalse(pre['blender_executed'])

    def test_corrupted_index_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'atlas.json'
            index=json.loads(INDEX.read_text(encoding='utf-8'))
            index['tools'][10]['id']=999
            p.write_text(json.dumps(index),encoding='utf-8')
            with self.assertRaises(ValueError):load_index(p)

    def test_pdf_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'atlas.json'
            index=json.loads(INDEX.read_text(encoding='utf-8'))
            index['source']['sha256']='0'*64
            p.write_text(json.dumps(index),encoding='utf-8')
            with self.assertRaises(ValueError):load_index(p)

    def test_builder_reproduces_identical_index(self):
        try:
            import fitz  # optional build-time dependency, not used by router or GCB
        except ImportError:
            self.skipTest('PyMuPDF is not installed; prebuilt index and PDF hash already covered')
        from build_blender_atlas_index import build
        fresh=build(ROOT/self.index['source']['pdf_path'])
        self.assertEqual(fresh,self.index)

if __name__=='__main__':unittest.main()
