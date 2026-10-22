"""Deterministic mesh and adaptive-budget tests with a fake bpy mesh sink.

Mocked Blender API verifies mesh math and manifold edge counts, NOT actual bpy runtime.
"""
from __future__ import annotations
import copy
import importlib.util
import sys
import tempfile
import types
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from detail_budget import plan
from forge_v13_core import validate_recipe


def fixture():
    import json
    return json.loads((ROOT/'examples/upgrades/chair_detail_budget.json').read_text())


class DetailAllocationTests(unittest.TestCase):
    def setUp(self):self.doc=fixture()
    def test_geometry_never_downgrades(self):
        result=plan(self.doc)
        self.assertEqual(result['status'],'DETAIL_ALLOCATION_PROPOSED_NOT_RENDERED')
        mapping={d['id']:d['route'] for d in result['decisions']}
        self.assertEqual(mapping['seat_quilt_geometry'],'ACTUAL_GEOMETRY_REQUIRED')
        self.assertEqual(mapping['seat_fine_grain'],'APPEARANCE_DETAIL_IF_ALLOWED')
    def test_budget_blocker_is_explicit(self):
        self.doc['triangle_budget']=12000
        self.assertEqual(plan(self.doc)['status'],'BLOCKED_GEOMETRY_BUDGET')
    def test_optional_high_pixel_geometry_planned(self):
        self.doc['features'][-1]['representation']='either'
        self.doc['features'][-1]['projected_size_px']=20
        report=plan(self.doc)
        mapping={d['id']:d['route'] for d in report['decisions']}
        self.assertEqual(mapping['seat_seam_geometry'],'GEOMETRY_PLANNED')
    def test_required_normal_map_is_refused(self):
        self.doc['features'][0]['method']='material_bake'
        with self.assertRaises(ValueError):plan(self.doc)
    def test_zero_triangle_cost_required_refused(self):
        self.doc['features'][0]['triangle_cost']=0
        with self.assertRaises(ValueError):plan(self.doc)
    def test_no_pixel_projection_fabrication(self):
        self.doc['features'][0].pop('projected_size_px')
        with self.assertRaises(ValueError):plan(self.doc)
    def test_missing_budget(self):
        self.doc.pop('triangle_budget')
        with self.assertRaises(ValueError):plan(self.doc)
    def test_negative_triangle_count(self):
        self.doc['base_triangles']=-1
        with self.assertRaises(ValueError):plan(self.doc)
    def test_geometry_cost_exceeds_budget(self):
        self.doc['features'][0]['triangle_cost']=58000
        self.assertEqual(plan(self.doc)['status'],'BLOCKED_GEOMETRY_BUDGET')
    def test_untrusted_user_script_rejected(self):
        self.doc['features'][0]['python']='exec'
        with self.assertRaises(ValueError):plan(self.doc)
    def test_duplicate_feature_rejected(self):
        self.doc['features'][1]['id']=self.doc['features'][0]['id']
        with self.assertRaises(ValueError):plan(self.doc)
    def test_exceeding_budget_for_optional_material(self):
        self.doc['features'][1]['projected_size_px']=200
        self.doc['features'][1]['triangle_cost']=50000
        r=plan(self.doc)
        m={d['id']:d['route'] for d in r['decisions']}
        self.assertEqual(m['seat_fine_grain'],'APPEARANCE_DETAIL_IF_ALLOWED')
    def test_material_only_stays_material(self):
        self.doc['features'][1]['representation']='material'
        self.doc['features'][1]['projected_size_px']=400
        r=plan(self.doc)
        m={d['id']:d['route'] for d in r['decisions']}
        self.assertEqual(m['seat_fine_grain'],'MATERIAL_ONLY_AS_SPECIFIED')


class FakeMesh:
    def __init__(self,name):self.name=name;self.vertices=[];self.faces=[]
    def from_pydata(self,points,edges,faces):self.vertices=points;self.faces=faces
    def update(self):pass

class FakeObject:
    def __init__(self,name,mesh):self.name=name;self.data=mesh

class FakeMeshes:
    def new(self,name):return FakeMesh(name)
class FakeObjects:
    def new(self,name,mesh):return FakeObject(name,mesh)
class FakeLink:
    def __init__(self):self.linked=[]
    def link(self,obj):self.linked.append(obj)


def load_fake_modeling():
    fake_link=FakeLink()
    bpy=types.SimpleNamespace(data=types.SimpleNamespace(meshes=FakeMeshes(),objects=FakeObjects()),
        context=types.SimpleNamespace(scene=types.SimpleNamespace(collection=types.SimpleNamespace(objects=fake_link))))
    old_bpy=sys.modules.get('bpy');old_mu=sys.modules.get('mathutils')
    sys.modules['bpy']=bpy;sys.modules['mathutils']=types.SimpleNamespace(Vector=lambda x:x)
    try:
        name='__forge_v13_mocked_blender_modeling'
        spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/blender_modeling.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    finally:
        if old_bpy is None:sys.modules.pop('bpy',None)
        else:sys.modules['bpy']=old_bpy
        if old_mu is None:sys.modules.pop('mathutils',None)
        else:sys.modules['mathutils']=old_mu
    return mod,fake_link


class MeshMathTests(unittest.TestCase):
    def setUp(self):
        import json
        self.recipe=json.loads((ROOT/'examples/upgrades/chair_procedural_demo.json').read_text())
        self.quilt=next(x for x in self.recipe['operators'] if x['op']=='quilt_panel')
    def test_quilt_validated_as_real_geometry(self):
        info=validate_recipe(self.recipe)
        self.assertIn('seat_quilt_geometry',info['feature_ids'])
    def test_quilt_vertices_are_actually_displaced(self):
        model,_=load_fake_modeling()
        mesh=model.quilt_mesh(self.quilt).data
        nx=self.quilt['cells_x']*self.quilt['subdivisions']+1
        ny=self.quilt['cells_y']*self.quilt['subdivisions']+1
        self.assertEqual(len(mesh.vertices),2*nx*ny)
        z=[v[2] for v in mesh.vertices[:nx*ny]]
        self.assertGreater(max(z)-min(z),self.quilt['indent_depth_m']*.8)
        self.assertGreater(min(z),min(v[2] for v in mesh.vertices[nx*ny:]))
    def test_quilt_is_closed_manifold_topology(self):
        model,link=load_fake_modeling()
        obj=model.quilt_mesh(self.quilt)
        self.assertIn(obj,link.linked)
        mesh=obj.data
        edge_counts=Counter()
        for face in mesh.faces:
            self.assertEqual(len(face),4)
            for a,b in zip(face,face[1:]+face[:1]):
                edge_counts[tuple(sorted((a,b)))]+=1
        self.assertTrue(edge_counts)
        self.assertTrue(all(count==2 for count in edge_counts.values()),
                        'closed quad mesh requires exactly two faces per undirected edge')
    def test_quilt_depth_limited_by_actual_panel_thickness(self):
        self.quilt['indent_depth_m']=.08
        with self.assertRaises(ValueError):validate_recipe(self.recipe)
    def test_quilt_not_a_shader_texture(self):
        model,_=load_fake_modeling()
        actual=model.quilt_mesh(self.quilt).data
        self.assertGreater(len(actual.vertices),100)
        self.assertGreater(len(set(round(v[2],6) for v in actual.vertices)),2)
    def test_quilt_cell_counts_bound(self):
        self.quilt['cells_x']=100
        with self.assertRaises(ValueError):validate_recipe(self.recipe)
    def test_quilt_cost_bound(self):
        many=copy.deepcopy(self.quilt)
        many['cells_x']=16;many['cells_y']=16;many['subdivisions']=8
        many['feature_id']='unique_feature'
        self.recipe['operators'].append(many)
        for i in range(30):
            clone=copy.deepcopy(many);clone['part_id']=f'panel_{i:03}';clone['feature_id']=f'feature_{i:03}'
            self.recipe['operators'].append(clone)
        with self.assertRaises(ValueError):validate_recipe(self.recipe)
    def test_loft_geometry_has_end_caps(self):
        model,_=load_fake_modeling()
        ob=next(op for op in self.recipe['operators'] if op['op']=='loft')
        mesh=model.loft_mesh(ob).data
        self.assertEqual(len(mesh.vertices),len(ob['rings'])*ob['segments'])
        self.assertEqual(len(mesh.faces),(len(ob['rings'])-1)*ob['segments']+2)


if __name__=='__main__':unittest.main()
