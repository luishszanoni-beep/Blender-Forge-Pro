"""Run inside authorized Blender, never ordinary Python.
Blender background entrypoint:
  blender --background --python scripts/gcb_blender.py -- --spec planning/gcb/gcb_spec.json --out work/gcb_blockout
Creates only a technical BLOCKOUT and evidence. It does not approve likeness or export a final model.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from gcb_core import load_spec, primitive_mesh, validate, world_anchor, write_json  # noqa


def args_parse():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    ap=argparse.ArgumentParser()
    ap.add_argument('--spec',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    return ap.parse_args(args)


def setup_material(name,color):
    mat=bpy.data.materials.new(name=name)
    mat.diffuse_color=(*color,1)
    mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    if bs:
        bs.inputs['Base Color'].default_value=(*color,1)
        bs.inputs['Roughness'].default_value=0.75
    return mat


def set_camera(scene,camera,world_points,view):
    coords=[Vector(p) for p in world_points]
    mins=Vector([min(p[i] for p in coords) for i in range(3)])
    maxs=Vector([max(p[i] for p in coords) for i in range(3)])
    center=(mins+maxs)/2
    diameter=max((maxs-mins).length,0.5)
    dirs={'front':Vector((0,-1,0)),'back':Vector((0,1,0)),
          'side':Vector((1,0,0)),'top':Vector((0,0,1)),
          'three_quarter':Vector((1,-1,0.85))}
    direction=dirs[view].normalized()
    camera.location=center+direction*diameter*2.4
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=diameter*1.45
    scene.camera=camera


def main():
    args=args_parse();spec=load_spec(args.spec);check=validate(spec)
    if check['errors']:raise RuntimeError('GCB blocked: '+ '; '.join(check['errors']))
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC' if spec['units']['mode']=='mm' else 'NONE'
    conversion=0.001 if spec['units']['mode']=='mm' else 1.0
    clay=setup_material('GCB_neutral_clay',(0.4,0.49,0.58))
    highlight=setup_material('GCB_new_parts',(0.09,0.78,0.7))
    scene.render.resolution_x=1024;scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    for engine in ('BLENDER_WORKBENCH','BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
        try:scene.render.engine=engine;break
        except (TypeError,ValueError):continue
    world_points=[];objects={}
    for part in spec['parts']:
        ident=part['id']
        dummy={**part,'position':[0,0,0],'rotation_deg':[0,0,0]}
        vertices,faces=primitive_mesh(dummy)
        mesh=bpy.data.meshes.new('GCB_'+ident+'_mesh')
        pivot=part.get('pivot',[0,0,0])
        # Keep world-space geometry unchanged while placing the real Blender origin at the declared rig pivot.
        mesh.from_pydata([[(c-pivot[i])*conversion for i,c in enumerate(v)] for v in vertices],[],[list(face) for face in faces])
        mesh.update()
        obj=bpy.data.objects.new(ident,mesh)
        bpy.context.collection.objects.link(obj)
        obj.location=[c*conversion for c in world_anchor(part,pivot)]
        obj.rotation_euler=[math.radians(c) for c in part['rotation_deg']]
        obj['forge_part_id']=ident
        obj['gcb_confidence']=part['confidence'];obj['gcb_stage']=part['stage']
        obj['gcb_pivot_local']=list(pivot)
        obj.data.materials.append(clay)
        objects[ident]=obj
        true_vertices,_=primitive_mesh(part)
        world_points.extend([[v*conversion for v in xyz] for xyz in true_vertices])
    bpy.context.view_layer.update()
    for part in spec['parts']:
        parent=part.get('parent')
        if parent:
            obj=objects[part['id']]
            world=obj.matrix_world.copy()
            obj.parent=objects[parent]
            obj.matrix_world=world  # Preserve authored WORLD coordinates when parented
    bpy.context.view_layer.update()
    bpy.ops.object.camera_add(location=(3,3,4))
    camera=bpy.context.object;camera.name='GCB_OrthoCamera'
    bpy.ops.object.light_add(type='AREA', location=(5,-6,10))
    light=bpy.context.object;light.data.energy=2200;light.data.shape='DISK';light.data.size=8
    scene.world.color=(0.17,0.17,0.17)
    images=[]
    stages=[('all',{p['id'] for p in spec['parts']},set())]
    already=set()
    for step in spec['steps']:
        already |= set(step['parts'])
        stages.append((step['id'],set(already),set(step['parts'])))
    for stage,visible,new_parts in stages:
        for ident,obj in objects.items():
            obj.hide_render=ident not in visible
            obj.data.materials.clear()
            obj.data.materials.append(highlight if ident in new_parts else clay)
        for view in ('front','side','top','three_quarter'):
            set_camera(scene,camera,world_points,view)
            scene.render.filepath=str(out / ('blockout_'+stage+'_'+view+'.png'))
            bpy.ops.render.render(write_still=True)
            images.append(str(Path(scene.render.filepath).name))
    for obj in objects.values():
        obj.hide_render=False;obj.data.materials.clear();obj.data.materials.append(clay)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'gcb_blockout.blend'))
    write_json(out/'gcb_blender_evidence.json',{
        'status':'BLOCKOUT_RENDERED_PENDING_INDEPENDENT_VISUAL_QA',
        'source_spec':str(args.spec.resolve()),
        'blend':str(out/'gcb_blockout.blend'),
        'part_ids':sorted(objects),'rendered_images':images,
        'units_mode':spec['units']['mode'],
        'qualifications':['not artwork-faithfulness proof','not final materials/rigging/export proof',
                          'primitive/blockout geometry only']
    })
    print('GCB_BLOCKOUT_SAVED',str(out/'gcb_blockout.blend'))


if __name__=='__main__':main()
