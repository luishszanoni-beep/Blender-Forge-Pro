"""Trusted Blender-side bpy worker (requires Python inside Blender).

Diagnostic, evidence, and reviewed fixed-spec geometric build/repair/variants/LOD.
DO NOT label diagnostic scene as a production model or visual-fidelity pass.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
import hashlib
from pathlib import Path

try:
    import bpy
    import bmesh
    from mathutils import Vector
except ImportError as e:
    raise RuntimeError('This worker requires Blender bpy; call through blender_bridge.py') from e


def write_json(dst, payload):
    p=Path(dst)
    if p.exists():raise RuntimeError('refuse overwrite of existing output: '+str(p))
    p.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def material(name,color,roughness=0.7,metallic=0.0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        for inp, val in [('Base Color',color),('Roughness',roughness),('Metallic',metallic)]:
            if bsdf.inputs.get(inp):bsdf.inputs[inp].default_value=val
    m.diffuse_color=color
    return m


def assigned(obj, part_id, mat, feature_id=None):
    obj.name=part_id
    obj['forge_part_id']=part_id
    if feature_id:obj['forge_feature_ids']=feature_id
    if obj.type=='MESH' and mat:obj.data.materials.append(mat)
    return obj


def cube(name,loc,dim,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    ob=bpy.context.object;ob.dimensions=dim
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assigned(ob,name,mat)
    m=ob.modifiers.new('Real chamfered edges','BEVEL');m.width=min(dim)*0.12;m.segments=3
    n=ob.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return ob


def cylinder(name,loc,radius,depth,mat,rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=depth,location=loc)
    ob=bpy.context.object;assigned(ob,name,mat)
    if rotation:ob.rotation_euler=rotation
    bevel=ob.modifiers.new('edge fillet','BEVEL');bevel.width=min(radius*0.12,0.004);bevel.segments=2
    return ob


def geometric_seam(points,mat,part_id,feature_id):
    # A curve with real bevel and explicit conversion to MESH => physical raised stitch.
    curve=bpy.data.curves.new(part_id+'_curve','CURVE')
    curve.dimensions='3D';curve.resolution_u=12;curve.bevel_depth=0.0022;curve.bevel_resolution=3
    poly=curve.splines.new('POLY');poly.points.add(len(points)-1)
    for p,co in zip(poly.points,points):p.co=(*co,1.0)
    poly.use_cyclic_u=True
    ob=bpy.data.objects.new(part_id,curve);bpy.context.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.convert(target='MESH')
    ob=bpy.context.object;assigned(ob,part_id,mat,feature_id)
    ob['forge_geometry_proof_type']='real_mesh_curve_bevel'
    return ob


def diagnostic_sample(out):
    # This is a known geometric diagnostic fixture, NOT source-image-to-model generation.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    sc['forge_diagnostic_only']=True
    wood=material('Demo | painted support',(0.10,0.12,0.14,1),0.40,0.35)
    fabric=material('Demo | upholstery',(0.50,0.30,0.18,1),0.83,0)
    stitch=material('Demo | stitched thread',(0.78,0.68,0.48,1),0.85,0)
    for x in (-0.275,0.275):
        for y in (-0.205,0.205):
            cube('leg_'+('left' if x<0 else 'right')+'_'+('front' if y<0 else 'back'),(x,y,0.217),(.043,.043,.435),wood)
    cube('seat_support',(0,0,0.439),(.64,.5,.052),wood)
    cube('seat_upholstery',(0,0,0.49),(.65,.53,.08),fabric)
    cube('back_support',(0,0.226,0.755),(.62,.07,.55),wood)
    cube('back_cushion',(0,0.175,0.765),(.60,.055,.50),fabric)
    seam=[(-.295,-.225,.539),(.295,-.225,.539),(.295,.225,.539),(-.295,.225,.539)]
    geometric_seam(seam,stitch,'seat_perimeter_stitch','seat_raised_seam')
    for x in (-0.22,0.22):
        cylinder('detail_bolt_'+str(x), (x,0.254,0.59),0.014,0.015,wood,rotation=(math.pi/2,0,0))
    for o in bpy.data.objects:
        if o.type=='MESH':o.select_set(False)
    sc['forge_demo_notice']='Not reference matched; diagnostic fixture only'
    dst=out/'diagnostic.blend'
    if dst.exists():raise RuntimeError('diagnostic.blend exists; refuse overwrite')
    bpy.ops.wm.save_as_mainfile(filepath=str(dst),check_existing=False)
    return {'status':'PASS','note':'Diagnostic only; no source-reference fidelity proof.','scene_file':str(dst),'mesh_count':sum(o.type=='MESH' for o in bpy.data.objects)}


def load_scene(blend):
    # Scripts saved inside a .blend are not automatically executed.
    bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()),load_ui=False,use_scripts=False)


def all_meshes():
    return [o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]


def bounds(objects=None):
    objects=all_meshes() if objects is None else objects
    xyz=[o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    if not xyz:raise RuntimeError('No renderable mesh objects in scene')
    lows=Vector(tuple(min(v[k] for v in xyz) for k in range(3)))
    highs=Vector(tuple(max(v[k] for v in xyz) for k in range(3)))
    return lows,highs


def mesh_inspect():
    deps=bpy.context.evaluated_depsgraph_get();parts=[];total_tris=0
    for obj in all_meshes():
        ev=obj.evaluated_get(deps)
        mesh=ev.to_mesh()
        if mesh is None:continue
        try:
            mesh.calc_loop_triangles()
            tris=len(mesh.loop_triangles);total_tris+=tris
            bm=bmesh.new()
            try:
                bm.from_mesh(mesh)
                nm=sum(not e.is_manifold for e in bm.edges)
                loose=sum(e.is_wire for e in bm.edges)
            finally:bm.free()
            # World-space fingerprint preserves evidence of exact geometry changes.
            # Do not pretend that partial hashes prove an unchanged highpoly mesh.
            if len(mesh.vertices)<=50000:
                pts=sorted(tuple(round(float(v),6) for v in (obj.matrix_world @ vert.co)) for vert in mesh.vertices)
                h=hashlib.sha256()
                for pt in pts:h.update((','.join(f'{x:.6f}' for x in pt)+';').encode('ascii'))
                fp=h.hexdigest()
            else:fp='NOT_COMPUTED_LARGE'
            oblo,obhi=bounds([obj])
            parts.append({'name':obj.name,'part_id':obj.get('forge_part_id'),
                          'world_mesh_fingerprint':fp,
                          'world_bbox_min_m':list(oblo),'world_bbox_max_m':list(obhi),
                          'feature_ids':obj.get('forge_feature_ids',''),
                          'geometry_proof_type':obj.get('forge_geometry_proof_type'),
                          'evaluated_vertices':len(mesh.vertices),'evaluated_triangles':tris,
                          'nonmanifold_edges':nm,'loose_edges':loose,
                          'materials':[m.name if m else None for m in obj.data.materials]})
        finally:ev.to_mesh_clear()
    lo,hi=bounds()
    return {'status':'MEASURED_NOT_APPROVED','blender_version':bpy.app.version_string,
            'scene_is_diagnostic':bool(bpy.context.scene.get('forge_diagnostic_only',False)),
            'scene_bounds_min_m':list(lo),'scene_bounds_max_m':list(hi),
            'scene_dimensions_mm':[round((hi[i]-lo[i])*1000,3) for i in range(3)],
            'mesh_object_count':len(parts),'evaluated_triangles_total':total_tris,'parts':parts,
            'note':'Mesh metrics are NOT proof of visual reference match or physical relief by themselves.'}


def setup_render(out):
    scene=bpy.context.scene
    # WORKBENCH is intentionally material-neutral for shape/fidelity blockout.
    scene.render.engine='BLENDER_WORKBENCH'
    shading=scene.display.shading
    shading.light='STUDIO'
    shading.color_type='SINGLE'
    shading.single_color=(0.72,0.74,0.78)
    scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False


def render_views(out):
    scene=bpy.context.scene;setup_render(out)
    lo,hi=bounds();center=(lo+hi)/2
    scale=max(hi[i]-lo[i] for i in range(3))*1.8
    if scale<=0:raise RuntimeError('invalid scene bbox')
    cams={
        'front':Vector((0,-1,0)), 'back':Vector((0,1,0)),
        'left':Vector((-1,0,0)),'right':Vector((1,0,0)),
        'top':Vector((0,0,1)),'bottom':Vector((0,0,-1)),
        'front_left':Vector((-1,-1,0.7)), 'front_right':Vector((1,-1,0.7)),
        'back_left':Vector((-1,1,0.7)),'back_right':Vector((1,1,0.7))}
    cdat=bpy.data.cameras.new('Forge neutral QA camera');camera=bpy.data.objects.new('Forge neutral QA camera',cdat)
    scene.collection.objects.link(camera);scene.camera=camera;cdat.type='ORTHO';cdat.ortho_scale=scale
    result=[]
    for name,direction in cams.items():
        camera.location=center+direction.normalized()*max(scale*2.0,0.1)
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        img=out/(name+'.png')
        if img.exists():raise RuntimeError('refuse existing render: '+str(img))
        scene.render.filepath=str(img);bpy.ops.render.render(write_still=True)
        if not img.is_file() or img.stat().st_size<100:raise RuntimeError('render missing/empty: '+str(img))
        result.append({'view':name,'path':str(img),'camera_projection':'orthographic','note':'Uncalibrated against source unless a separate alignment record exists'})
    return {'status':'RENDERED_PENDING_VISUAL_REVIEW','files':result,'note':'Neutral views must be viewed and compared to actual references.'}


def export_glb(out):
    src=mesh_inspect()
    path=out/'model.glb'
    if path.exists():raise RuntimeError('refuse overwrite of existing model.glb')
    if not hasattr(bpy.ops.export_scene,'gltf'):
        raise RuntimeError('Blender GLB exporter unavailable in this build')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB')
    if not path.is_file() or path.stat().st_size<100:
        raise RuntimeError('glb export failed to produce file')
    # Reimport into new scene to ensure the serialized model is at least usable in Blender.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if not hasattr(bpy.ops.import_scene,'gltf'):
        return {'status':'EXPORTED_UNVERIFIED_ROUNDTRIP','path':str(path),
                'reason':'glTF importer unavailable','source':src}
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported=mesh_inspect()
    pre=src['evaluated_triangles_total'];post=imported['evaluated_triangles_total']
    if imported['mesh_object_count']<1 or post<1:
        st='FAIL';reasons=['no mesh recovered']
    else:
        reasons=[]
        if pre!=post:reasons.append(f'triangle total changed after GLB roundtrip: {pre}->{post}')
        for i in range(3):
            p=src['scene_dimensions_mm'][i];q=imported['scene_dimensions_mm'][i]
            if abs(p-q)>max(1.0,p*0.015):
                reasons.append(f'axis {i} bounds changed beyond tolerance {p}->{q}mm')
        st='PASS_TECHNICAL_ONLY' if not reasons else 'REVIEW_REQUIRED'
    return {'status':st,'path':str(path),'bytes':path.stat().st_size,'source_triangles':pre,
            'reimport_triangles':post,'reimport_meshes':imported['mesh_object_count'],
            'reasons':reasons,'note':'Technical reimport check. Material/render/reference visual QA is separate.'}



def geometry_proof(out, feature_id):
    """Produce measured mesh report + neutral closeups for a tagged geometry feature.

    Output is INCONCLUSIVE pending human comparison; generated mesh stats do not
    prove perceptual fidelity to a photograph.
    """
    tagged=[]
    for ob in all_meshes():
        val=ob.get('forge_feature_ids','')
        names=[t.strip() for t in str(val).replace(';',',').split(',') if t.strip()]
        if feature_id in names:
            tagged.append(ob)
    if not tagged:
        return {'status':'BLOCKED_MISSING_FEATURE','feature_id':feature_id,
                'reason':'No actual mesh tagged with this feature ID.'}
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    measured=[]
    for ob in tagged:
        ev=ob.evaluated_get(deps);mesh=ev.to_mesh()
        if mesh is None:continue
        try:
            measured.append({'object':ob.name,'part_id':ob.get('forge_part_id'),
                             'evaluated_vertex_count':len(mesh.vertices),
                             'evaluated_polygon_count':len(mesh.polygons),
                             'mesh_bounds_m':[list(ob.matrix_world @ Vector(c)) for c in ob.bound_box],
                             'geometry_proof_type':ob.get('forge_geometry_proof_type'),
                             'note':'Data demonstrates evaluated vertex mesh exists; does NOT alone prove actual relief/accuracy.'})
        finally:ev.to_mesh_clear()
    if not measured:
        return {'status':'BLOCKED_NO_EVALUATED_MESH','feature_id':feature_id}
    for ob in all_meshes():
        if ob not in tagged:ob.hide_render=True
    setup_render(out)
    scene=bpy.context.scene
    shade=scene.display.shading
    if hasattr(shade,'show_cavity'):shade.show_cavity=True
    lo,hi=bounds(tagged);center=(lo+hi)*0.5
    diag=max(hi[i]-lo[i] for i in range(3))
    if diag<0.00001: return {'status':'BLOCKED_DEGENERATE_FEATURE','feature_id':feature_id}
    cd=bpy.data.cameras.new('Forge geometry proof camera');cam=bpy.data.objects.new('Forge geometry proof camera',cd)
    scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=diag*1.8
    files=[]
    for name,vec in {'detail_top':Vector((0,0,1)),'detail_oblique':Vector((1,-1,0.85))}.items():
        cam.location=center+vec.normalized()*diag*3.5
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        dst=out/(feature_id+'_'+name+'.png')
        if dst.exists():raise RuntimeError('geometry proof image exists; refuse overwrite: '+str(dst))
        scene.render.filepath=str(dst)
        bpy.ops.render.render(write_still=True)
        if not dst.is_file() or dst.stat().st_size<100:raise RuntimeError('missing detail screenshot')
        files.append(str(dst))
    return {'status':'READY_FOR_VISUAL_QA','feature_id':feature_id,'measured_meshes':measured,
            'clay_evidence_files':files,
            'wireframe_visual_review_required':True,
            'export_persistence_review_required':True,
            'note':'Actual evaluated mesh and neutral closeup exist. Additional edit-mode wireframe/mesh section and reference comparison required before G3 APPROVED.'}


def main():
    kinds=('diagnostic-sample','inspect','render-views','export-glb','geometry-proof',
           'build-recipe','apply-repair','create-lods','build-variant','assembly-audit')
    p=argparse.ArgumentParser();p.add_argument('--task',required=True,choices=kinds)
    p.add_argument('--blend');p.add_argument('--feature-id');p.add_argument('--spec');p.add_argument('--out',required=True);a=p.parse_args()
    out=Path(a.out).resolve()
    if not out.is_dir():raise RuntimeError('existing out directory required')
    if a.task in ('diagnostic-sample','build-recipe'):
        if a.task=='diagnostic-sample':result=diagnostic_sample(out)
        else:
            if not a.spec:raise RuntimeError('--spec required')
            from blender_modeling import build_recipe
            result=build_recipe(json.loads(Path(a.spec).read_text(encoding='utf-8')),out)
    else:
        if not a.blend:raise RuntimeError('--blend required')
        load_scene(a.blend)
        if a.task=='inspect':result=mesh_inspect()
        elif a.task=='render-views':result=render_views(out)
        elif a.task=='geometry-proof':
            if not a.feature_id:raise RuntimeError('geometry-proof requires --feature-id')
            result=geometry_proof(out,a.feature_id)
        elif a.task=='export-glb':result=export_glb(out)
        else:
            if not a.spec:raise RuntimeError('--spec required')
            spec=json.loads(Path(a.spec).read_text(encoding='utf-8'))
            from blender_modeling import apply_repair,make_lods,build_variant
            from forge_v13_core import audit_assembly
            if a.task=='apply-repair':result=apply_repair(spec,out,mesh_inspect)
            elif a.task=='create-lods':result=make_lods(spec,out,mesh_inspect)
            elif a.task=='build-variant':result=build_variant(spec,out)
            elif a.task=='assembly-audit':result=audit_assembly(spec,mesh_inspect())
            else:raise RuntimeError('unknown task')
    dst=out/(a.task.replace('-','_')+'.json')
    write_json(dst,result)
    print('FORGE_RESULT='+json.dumps({'status':result['status'],'report_file':str(dst)},ensure_ascii=False))
    if result['status'].startswith('BLOCKED') or result['status']=='FAIL':
        raise RuntimeError('requested geometric evidence was not produced; '+result['status'])


if __name__=='__main__':
    # This code is executed INSIDE Blender where bpy is actually present.
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    sys.argv=[sys.argv[0]]+argv
    main()
