"""Fixed, reviewed bpy geometric operators for Forge 1.3. Called only by trusted worker.

Requires Blender Python. Input JSON recipes are validated with forge_v13_core:
NO arbitrary Python, drivers, external file paths, node expressions or code evaluation.
Each task saves a NEW .blend checkpoint and produces PENDING_VISUAL_QA artifacts.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector
from forge_v13_core import (validate_recipe, validate_repair, validate_lod,
                            validate_variant_config, resolve_variant, validate_assembly, audit_assembly)


def object_by_id(pid):
    matches=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('forge_part_id')==pid]
    if len(matches)!=1:raise RuntimeError(f'part {pid}: expected exactly one mesh, found {len(matches)}')
    return matches[0]


def select(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj


def mark(ob, op):
    ob.name=op['part_id'];ob['forge_part_id']=op['part_id']
    if op.get('feature_id'):
        ob['forge_feature_ids']=op['feature_id']
        ob['forge_geometry_proof_type']='evaluated_mesh_geometry'
    return ob


def material_from_recipe(entry):
    m=bpy.data.materials.new(entry['id']);m.diffuse_color=entry['color_rgba'];m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        for key,value in [('Base Color',entry['color_rgba']),('Roughness',entry.get('roughness',0.65)),('Metallic',entry.get('metallic',0))]:
            if key in bsdf.inputs:bsdf.inputs[key].default_value=value
    return m


def give_material(ob, mid):
    mat=bpy.data.materials.get(mid)
    if mat is None:raise RuntimeError('unknown material in scene: '+mid)
    if len(ob.data.materials):ob.data.materials[0]=mat
    else:ob.data.materials.append(mat)


def curve_mesh(op):
    name=op['part_id'];curve=bpy.data.curves.new(name+'_profile','CURVE')
    curve.dimensions='3D';curve.resolution_u=12;curve.bevel_depth=op['radius_m']
    curve.bevel_resolution=min(6,max(1,op.get('segments',8)//3))
    spline=curve.splines.new('POLY');spline.points.add(len(op['points_m'])-1)
    for a,point in zip(spline.points,op['points_m']):a.co=(*point,1)
    obj=bpy.data.objects.new(name,curve);bpy.context.scene.collection.objects.link(obj)
    select(obj);bpy.ops.object.convert(target='MESH')
    return bpy.context.object


def loft_mesh(op):
    rings=op['rings'];segs=int(op.get('segments',24))
    verts=[];faces=[]
    for ring in rings:
        cx,cy,cz=ring['center_m'];rx=ring['radius_x_m'];ry=ring['radius_y_m']
        for j in range(segs):
            t=2*math.pi*j/segs;verts.append((cx+rx*math.cos(t),cy+ry*math.sin(t),cz))
    faces.append(tuple(range(segs-1,-1,-1)))
    for i in range(len(rings)-1):
        for j in range(segs):
            n=(j+1)%segs;faces.append((i*segs+j,i*segs+n,(i+1)*segs+n,(i+1)*segs+j))
    faces.append(tuple((len(rings)-1)*segs+j for j in range(segs)))
    mesh=bpy.data.meshes.new(op['part_id']+'_mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(op['part_id'],mesh);bpy.context.scene.collection.objects.link(ob)
    return ob


def quilt_mesh(op):
    """Closed, actual vertex displacement: seam depressions + cell pillow bulge.

    Axis-aligned XY panel with Z thickness; does not simulate fabric physics.
    """
    cx,cy,cz=op['center_m'];width,depth,thick=op['size_m']
    cells_x=int(op['cells_x']);cells_y=int(op['cells_y'])
    subdivisions=int(op.get('subdivisions',6))
    nx=cells_x*subdivisions+1;ny=cells_y*subdivisions+1
    indent=op['indent_depth_m'];bulge=op.get('bulge_height_m',0)
    seam_width=op['seam_width_m']
    verts=[];faces=[]
    # Upper surface: physically deform vertices, not normals/material shading.
    for j in range(ny):
        v=j/(ny-1);py=cy+(v-0.5)*depth
        fy=(v*cells_y)%1
        dist_y=min(fy,1-fy)*depth/cells_y
        for i in range(nx):
            u=i/(nx-1);px=cx+(u-0.5)*width
            fx=(u*cells_x)%1
            dist_x=min(fx,1-fx)*width/cells_x
            seam=math.exp(-(dist_x/seam_width)**2)+math.exp(-(dist_y/seam_width)**2)
            displacement=-indent*min(1.0,seam)+bulge*max(0,math.sin(math.pi*fx)*math.sin(math.pi*fy))
            verts.append((px,py,cz+thick/2+displacement))
    half=nx*ny
    for j in range(ny):
        v=j/(ny-1);py=cy+(v-0.5)*depth
        for i in range(nx):
            u=i/(nx-1);px=cx+(u-0.5)*width
            verts.append((px,py,cz-thick/2))
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i;b=a+1;c=a+nx+1;d=a+nx
            faces.append((a,b,c,d))
            faces.append((half+d,half+c,half+b,half+a))
    # Side walls make the panel a closed solid.
    for j in range(ny-1):
        for i in (0,nx-1):
            a=j*nx+i;b=(j+1)*nx+i
            faces.append((a,b,half+b,half+a) if i==nx-1 else (b,a,half+a,half+b))
    for i in range(nx-1):
        for j in (0,ny-1):
            a=j*nx+i;b=a+1
            faces.append((b,a,half+a,half+b) if j==0 else (a,b,half+b,half+a))
    mesh=bpy.data.meshes.new(op['part_id']+'_quilt_mesh')
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(op['part_id'],mesh)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build_op(op):
    kind=op['op']
    if kind=='box':
        bpy.ops.mesh.primitive_cube_add(size=1,location=op['center_m'])
        ob=bpy.context.object;ob.dimensions=op['size_m']
        select(ob);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    elif kind=='cylinder':
        bpy.ops.mesh.primitive_cylinder_add(vertices=int(op.get('vertices',32)),radius=op['radius_m'],depth=op['depth_m'],location=op['center_m'])
        ob=bpy.context.object
    elif kind=='uv_sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=int(op.get('segments',24)),ring_count=max(8,int(op.get('segments',24))//2),radius=1,location=op['center_m'])
        ob=bpy.context.object;ob.scale=[v*0.5 for v in op['size_m']];select(ob)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    elif kind=='tube':ob=curve_mesh(op)
    elif kind=='loft':ob=loft_mesh(op)
    elif kind=='quilt_panel':ob=quilt_mesh(op)
    elif kind in ('groove_box','groove_cylinder'):
        target=object_by_id(op['target_part_id'])
        if kind=='groove_box':
            bpy.ops.mesh.primitive_cube_add(size=1,location=op['center_m'])
            cutter=bpy.context.object;cutter.dimensions=op['size_m'];select(cutter)
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        else:
            bpy.ops.mesh.primitive_cylinder_add(vertices=int(op.get('vertices',32)),radius=op['radius_m'],depth=op['depth_m'],location=op['center_m'])
            cutter=bpy.context.object
        modifier=target.modifiers.new('FORGE_RECESSED_'+op['feature_id'],'BOOLEAN')
        modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
        select(target)
        deps=bpy.context.evaluated_depsgraph_get()
        pre=target.evaluated_get(deps).to_mesh()
        try:pre_count=len(pre.polygons) if pre else 0
        finally:target.evaluated_get(deps).to_mesh_clear()
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        post_count=len(target.data.polygons)
        bpy.data.objects.remove(cutter,do_unlink=True)
        if post_count<=0 or post_count==pre_count:
            raise RuntimeError(f'Groove operation {op["feature_id"]} did not measurably change topology; inspect Boolean overlap')
        original=target.get('forge_feature_ids','')
        target['forge_feature_ids']=','.join(filter(None,[original,op['feature_id']]))
        target['forge_geometry_proof_type']='boolean_real_mesh_recess'
        return target
    else:raise RuntimeError('unsupported geometry operator')
    if 'rotation_deg' in op:
        ob.rotation_euler=[math.radians(x) for x in op['rotation_deg']]
    if op.get('bevel_m',0)>0:
        m=ob.modifiers.new('FORGE_BEVEL','BEVEL')
        m.width=op['bevel_m'];m.segments=3
    mark(ob,op);give_material(ob,op['material_id'])
    if kind=='quilt_panel':ob['forge_geometry_proof_type']='real_vertex_displacement_quilting'
    return ob


def _save(out, filename):
    dst=out/filename
    if dst.exists():raise RuntimeError('refuse overwrite existing scene: '+str(dst))
    bpy.ops.wm.save_as_mainfile(filepath=str(dst),check_existing=False)
    if not dst.is_file() or dst.stat().st_size<100:raise RuntimeError('scene output missing')
    return str(dst)


def build_recipe(spec, out):
    summary=validate_recipe(spec)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    scene['forge_project_id']=spec['project_id'];scene['forge_recipe_schema']='1.3'
    scene['forge_artistic_status']='PENDING_VISUAL_QA'
    for m in spec.get('materials',[]):material_from_recipe(m)
    produced=[]
    for op in spec['operators']:
        result=build_op(op)
        produced.append({'operation':op['op'],'id':op['part_id'],'resulting_mesh':result.name})
    return {'status':'MODEL_CREATED_PENDING_VISUAL_QA','scene_file':_save(out,'forge_recipe.blend'),
            'operators_executed':produced,'spec_preflight':summary,
            'note':'Procedural geometry is not proof of likeness, accurate dimensions or finished art.'}


def snapshot_digest(inspection):
    return hashlib.sha256(json.dumps(inspection,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()


def _part_summary(parts):
    return {p.get('part_id'):p for p in parts if p.get('part_id')}


def apply_repair(spec, out, inspection_function):
    before=inspection_function();lookups=_part_summary(before['parts'])
    if len(lookups)!=len(before['parts']):
        raise RuntimeError('repair requires unique, complete forge_part_id for every visible mesh')
    locked={o.get('forge_part_id') for o in bpy.context.scene.objects if o.get('forge_locked') is True}
    validate_repair(spec,set(lookups),locked)
    if spec['expected_snapshot_sha256']!=snapshot_digest(before):
        raise RuntimeError('stale before-snapshot digest: refuse edit before saving')
    targets={c['part_id'] for c in spec['changes']}
    for ch in spec['changes']:
        ob=object_by_id(ch['part_id'])
        if 'translation_m' in ch:
            for i,x in enumerate(ch['translation_m']):ob.location[i]+=x
        if 'scale_xyz' in ch:
            for i,x in enumerate(ch['scale_xyz']):ob.scale[i]*=x
        if 'material_id' in ch:give_material(ob,ch['material_id'])
    bpy.context.view_layer.update()
    after=inspection_function();post=_part_summary(after['parts'])
    if len(post)!=len(after['parts']) or len(post)!=len(lookups):
        raise RuntimeError('object inventory changed unexpectedly during repair')
    for part,entry in lookups.items():
        if part in targets:continue
        newer=post.get(part)
        if not newer:raise RuntimeError('unrelated mesh disappeared: '+part)
        for key in ('world_mesh_fingerprint','world_bbox_min_m','world_bbox_max_m','materials','evaluated_triangles'):
            if entry.get(key)!=newer.get(key):raise RuntimeError('unrelated mesh changed: '+part+' key '+key)
        if entry.get('world_mesh_fingerprint')=='NOT_COMPUTED_LARGE':
            raise RuntimeError('unrelated mesh too large for safe fingerprint comparison: '+part)
    for part in targets:
        if part not in post:raise RuntimeError('repair target disappeared: '+part)
    bpy.context.scene['forge_artistic_status']='PENDING_VISUAL_QA'
    return {'status':'CANDIDATE_PENDING_VISUAL_QA','scene_file':_save(out,'forge_repaired_candidate.blend'),
            'changed_part_ids':sorted(targets),'unchanged_part_ids':sorted(set(lookups)-targets),
            'before_hash':snapshot_digest(before),'after_hash':snapshot_digest(after),
            'note':'Only declared parts edited and unmodified parts checked; art QA remains mandatory.'}


def make_lods(spec,out,inspection_function):
    info=validate_lod(spec);before=inspection_function()
    originals=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
    if not originals:raise RuntimeError('LOD requires actual visible meshes')
    protected=set(spec.get('protected_part_ids',[]))
    # Never auto-decimate an object marked as real geometry evidence.
    protected.update(o.get('forge_part_id') for o in originals if o.get('forge_feature_ids'))
    oldids={o.get('forge_part_id') for o in originals}
    if not protected.issubset(oldids):raise RuntimeError('protected part not in scene')
    if before['evaluated_triangles_total']>5_000_000:
        raise RuntimeError('LOD scene exceeds automatic 5 million-triangle safety limit')
    if spec.get('max_triangles_lod0') and before['evaluated_triangles_total']>spec['max_triangles_lod0']:
        raise RuntimeError('source master triangle count exceeds declared LOD0 budget')
    produced=[]
    for i,ratio in enumerate(spec['ratios'],1):
        col=bpy.data.collections.new('FORGE_LOD_'+str(i))
        bpy.context.scene.collection.children.link(col)
        count=0
        for ob in originals:
            copy=ob.copy();copy.data=ob.data.copy();col.objects.link(copy)
            copy.name=ob.name+'_LOD'+str(i)
            copy['forge_lod_level']=i
            copy['forge_source_part_id']=ob.get('forge_part_id')
            if ob.get('forge_part_id') not in protected:
                md=copy.modifiers.new('FORGE_DECIMATE','DECIMATE');md.ratio=ratio
                select(copy);bpy.ops.object.modifier_apply(modifier=md.name)
            # Stage output hidden until user selects specific LOD for export.
            copy.hide_render=True;copy.hide_set(True)
            count+=len(copy.data.polygons)
        produced.append({'collection':col.name,'ratio_requested':ratio,'total_polygons_after':count,
                         'protected_ids_undecimated':sorted(protected)})
    after=inspection_function()
    for p in before['parts']:
        source=next((q for q in after['parts'] if q['name']==p['name']),None)
        if not source or source['world_mesh_fingerprint']!=p['world_mesh_fingerprint']:
            raise RuntimeError('highpoly master changed during LOD generation')
    bpy.context.scene['forge_artistic_status']='LOD_PENDING_VISUAL_QA'
    return {'status':'LOD_CANDIDATES_PENDING_VISUAL_QA','scene_file':_save(out,'forge_lod_candidates.blend'),
            'lods':produced,'source_master_unchanged':True,
            'note':'LOD candidates are in hidden collections; inspect silhouette, geometric requirements and export each intended LOD separately.'}


def build_variant(spec,out):
    if set(spec)-{'schema_version','project_id','variant_family','selection'}:
        raise ValueError('variant build unknown keys')
    if spec.get('schema_version')!='1.3':raise ValueError('variant build schema must be 1.3')
    config=spec.get('variant_family');selection=spec.get('selection')
    resolved=resolve_variant(config,selection)
    if resolved['status']!='VALIDATED_SELECTION_NOT_BUILT':raise RuntimeError('variant constraints fail: '+str(resolved['reasons']))
    touched=set(resolved['show_part_ids']+resolved['hide_part_ids']+list(resolved['material_overrides']))
    mapping={k:object_by_id(k) for k in touched}
    for ob in mapping.values():
        if ob.get('forge_locked') is True:raise RuntimeError('variant touches protected part '+ob.get('forge_part_id','?'))
    for mid in resolved['material_overrides'].values():
        if bpy.data.materials.get(mid) is None:raise RuntimeError('missing material: '+mid)
    for part in resolved['show_part_ids']:
        mapping[part].hide_render=False;mapping[part].hide_set(False)
    for part in resolved['hide_part_ids']:
        mapping[part].hide_render=True;mapping[part].hide_set(True)
    for part,mat in resolved['material_overrides'].items():give_material(mapping[part],mat)
    bpy.context.scene['forge_variant_family_id']=config['family_id']
    bpy.context.scene['forge_artistic_status']='VARIANT_PENDING_VISUAL_QA'
    return {'status':'VARIANT_CANDIDATE_PENDING_VISUAL_QA','scene_file':_save(out,'forge_variant_candidate.blend'),
            'selection':selection,'resolved':resolved,
            'note':'Single validated variant built; no promise of hidden combo generation or visual/export approval.'}
