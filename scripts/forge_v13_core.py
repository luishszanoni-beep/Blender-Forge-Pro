"""Blender Forge 1.3 strict, portable specs (NO bpy and NO code evaluation).

Technical preflight only. Artistic and export fidelity always need real Blender renders.
"""
from __future__ import annotations
import math
import re
from collections import Counter
from typing import Any

ID = re.compile(r'^[a-z][a-z0-9_-]{2,59}$')
OPS={'box','cylinder','uv_sphere','loft','tube','quilt_panel','groove_box','groove_cylinder'}
FINITE_LIMIT=1000.0  # +/- 1km in scene meters per coordinate, opt out not supported


def ident(v: Any, label='id') -> str:
    if not isinstance(v, str) or not ID.fullmatch(v):
        raise ValueError(f'{label} must be lowercase safe ID 3..60 characters')
    return v


def num(v: Any, label='value', lo=-FINITE_LIMIT, hi=FINITE_LIMIT) -> float:
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:
        raise ValueError(f'{label} must be finite number in [{lo}, {hi}]')
    return float(v)


def vec(v: Any, n: int, label='vector', lo=-FINITE_LIMIT, hi=FINITE_LIMIT) -> list[float]:
    if not isinstance(v,list) or len(v)!=n:
        raise ValueError(f'{label} must be {n}-element list')
    return [num(x, f'{label}[{i}]',lo,hi) for i,x in enumerate(v)]


def strict_keys(obj: dict, allowed: set[str], label: str) -> None:
    if not isinstance(obj,dict):
        raise ValueError(f'{label} must be object')
    extra=set(obj)-allowed
    if extra:raise ValueError(f'{label} unknown keys: {sorted(extra)}')


def validates_materials(mats):
    if not isinstance(mats,list) or len(mats)>64:raise ValueError('materials must be <=64 elements')
    seen=set()
    for i,m in enumerate(mats):
        strict_keys(m,{'id','color_rgba','roughness','metallic'},f'materials[{i}]')
        mid=ident(m.get('id'),'material.id')
        if mid in seen:raise ValueError('duplicate material: '+mid)
        seen.add(mid)
        vec(m.get('color_rgba'),4,'color_rgba',0,1)
        num(m.get('roughness',0.65),'roughness',0,1)
        num(m.get('metallic',0),'metallic',0,1)
    return seen


def validate_recipe(payload: dict) -> dict:
    strict_keys(payload,{'schema_version','project_id','materials','operators','description'},'recipe')
    if payload.get('schema_version')!='1.3':raise ValueError('recipe schema_version must be 1.3')
    ident(payload.get('project_id'),'project_id')
    if 'description' in payload and (not isinstance(payload['description'],str) or len(payload['description'])>300):raise ValueError('description invalid')
    materials=validates_materials(payload.get('materials',[]))
    ops=payload.get('operators')
    if not isinstance(ops,list) or not 1<=len(ops)<=300:raise ValueError('operators must be 1..300')
    existing=set();geometric=set();feature_ids=set();estimated_quads=0
    common={'op','part_id','material_id','rotation_deg','bevel_m','feature_id'}
    allowed_by_kind={
        'box':common|{'center_m','size_m'},
        'cylinder':common|{'center_m','radius_m','depth_m','vertices'},
        'uv_sphere':common|{'center_m','size_m','segments'},
        'loft':common|{'rings','segments'},
        'tube':common|{'points_m','radius_m','segments'},
        'quilt_panel':common|{'center_m','size_m','cells_x','cells_y','subdivisions',
                              'indent_depth_m','bulge_height_m','seam_width_m'},
        'groove_box':{'op','part_id','target_part_id','feature_id','center_m','size_m'},
        'groove_cylinder':{'op','part_id','target_part_id','feature_id','center_m','radius_m','depth_m','vertices'},
    }
    for i,op in enumerate(ops):
        if not isinstance(op,dict):raise ValueError(f'operators[{i}] must be object')
        kind=op.get('op')
        if kind not in OPS:raise ValueError(f'operators[{i}].op unsupported')
        strict_keys(op,allowed_by_kind[kind],f'operators[{i}]')
        name=ident(op.get('part_id'),'operator.part_id')
        if kind.startswith('groove_'):
            target=ident(op.get('target_part_id'),'target_part_id')
            if target not in existing:raise ValueError('groove target must be an existing earlier object')
            if op.get('feature_id') is None:raise ValueError('groove requires feature_id')
            feature=ident(op['feature_id'],'feature_id')
            if feature in feature_ids:raise ValueError('feature_id repeated')
            feature_ids.add(feature)
            if kind=='groove_box':
                vec(op.get('center_m'),3,'groove.center_m')
                vec(op.get('size_m'),3,'groove.size_m',0.00005,100)
            else:
                vec(op.get('center_m'),3,'groove.center_m')
                num(op.get('radius_m'),'groove.radius_m',0.00005,20)
                num(op.get('depth_m'),'groove.depth_m',0.00005,100)
                if int(num(op.get('vertices',32),'groove.vertices',12,256))!=op.get('vertices',32):
                    raise ValueError('groove.vertices must be integer')
            if name in existing:raise ValueError('groove label collides with existing part_id')
            continue
        if name in existing:raise ValueError('duplicate geometric part_id: '+name)
        existing.add(name);geometric.add(name)
        if op.get('material_id') not in materials:raise ValueError('material_id missing/unknown for '+name)
        if kind in ('box','cylinder','uv_sphere'):
            vec(op.get('center_m'),3,'center_m')
            if kind=='box':
                vec(op.get('size_m'),3,'size_m',0.00005,100)
            elif kind=='cylinder':
                num(op.get('radius_m'),'radius_m',0.00005,100)
                num(op.get('depth_m'),'depth_m',0.00005,100)
                if int(num(op.get('vertices',32),'vertices',12,256))!=op.get('vertices',32):
                    raise ValueError('vertices must be integer')
            else:
                vec(op.get('size_m'),3,'size_m',0.00005,100)
                if int(num(op.get('segments',24),'segments',12,128))!=op.get('segments',24):
                    raise ValueError('segments must be integer')
        elif kind=='tube':
            points=op.get('points_m')
            if not isinstance(points,list) or not 2<=len(points)<=512:raise ValueError('tube needs 2..512 control points')
            for point in points:vec(point,3,'points_m')
            num(op.get('radius_m'),'tube.radius_m',0.00005,10)
            if int(num(op.get('segments',8),'tube.segments',3,24))!=op.get('segments',8):
                raise ValueError('tube.segments must be integer')
        elif kind=='quilt_panel':
            vec(op.get('center_m'),3,'panel.center_m')
            size=vec(op.get('size_m'),3,'panel.size_m',0.001,100)
            cells_x=num(op.get('cells_x'),'cells_x',1,16)
            cells_y=num(op.get('cells_y'),'cells_y',1,16)
            subdivisions=num(op.get('subdivisions',6),'subdivisions',2,8)
            if any(int(x)!=x for x in (cells_x,cells_y,subdivisions)):
                raise ValueError('cells_x/y and subdivisions must be integers')
            depth=num(op.get('indent_depth_m'),'indent_depth_m',0.0001,0.05)
            num(op.get('bulge_height_m',0.0),'bulge_height_m',0,0.05)
            width=num(op.get('seam_width_m'),'seam_width_m',0.0001,0.1)
            if depth>size[2]*0.4 or width>min(size[0]/cells_x,size[1]/cells_y)*0.4:
                raise ValueError('quilt relief depth/seam_width exceeds panel dimensions')
            estimated_quads+=2*(int(cells_x*subdivisions))*(int(cells_y*subdivisions))
            if 'feature_id' not in op:raise ValueError('quilt panel requires feature_id')
        elif kind=='loft':
            rings=op.get('rings')
            if not isinstance(rings,list) or not 2<=len(rings)<=64:raise ValueError('loft requires 2..64 rings')
            for r in rings:
                strict_keys(r,{'center_m','radius_x_m','radius_y_m'},'ring')
                vec(r.get('center_m'),3,'ring.center_m')
                num(r.get('radius_x_m'),'ring.radius_x_m',0.00005,100)
                num(r.get('radius_y_m'),'ring.radius_y_m',0.00005,100)
            if int(num(op.get('segments',24),'loft.segments',8,128))!=op.get('segments',24):
                raise ValueError('loft.segments must be integer')
        if 'rotation_deg' in op:vec(op['rotation_deg'],3,'rotation_deg',-360,360)
        if 'bevel_m' in op:
            width=num(op['bevel_m'],'bevel_m',0,5)
            if kind=='box' and width>=min(op['size_m'])/2:
                raise ValueError('bevel_m cannot exceed half minimum box dimension')
        if 'feature_id' in op:
            fid=ident(op['feature_id'],'feature_id')
            if fid in feature_ids:raise ValueError('feature_id repeated')
            feature_ids.add(fid)
    if estimated_quads>300000:raise ValueError('quilt panels exceed bounded polygon estimate (300k)')
    return {'status':'VALIDATED_SPEC_NOT_EXECUTED','operators':len(ops),'parts':sorted(existing),
            'feature_ids':sorted(feature_ids),'note':'No Blender geometry created or validated.'}


def validate_repair(spec: dict, available: set[str] | None=None, locked: set[str] | None=None) -> dict:
    strict_keys(spec,{'schema_version','project_id','changes','reason','expected_snapshot_sha256','protected_part_ids'},'repair')
    if spec.get('schema_version')!='1.3':raise ValueError('repair schema_version must be 1.3')
    ident(spec.get('project_id'),'project_id')
    protected=spec.get('protected_part_ids',[])
    if not isinstance(protected,list):raise ValueError('protected_part_ids must be array')
    for part in protected:ident(part,'protected_part_ids')
    if len(protected)!=len(set(protected)):raise ValueError('duplicate protected part')
    changes=spec.get('changes')
    if not isinstance(changes,list) or not 1<=len(changes)<=50:raise ValueError('changes must be 1..50')
    affected=set()
    for i,c in enumerate(changes):
        strict_keys(c,{'part_id','translation_m','scale_xyz','material_id'},f'changes[{i}]')
        pid=ident(c.get('part_id'),'changes.part_id')
        if pid in affected:raise ValueError('duplicate repair target')
        if available is not None and pid not in available:raise ValueError('repair target not found: '+pid)
        if (locked and pid in locked) or pid in protected:raise ValueError('locked part cannot be a repair target: '+pid)
        affected.add(pid)
        if not any(k in c for k in ('translation_m','scale_xyz','material_id')):raise ValueError('repair change has no operation')
        if 'translation_m' in c:vec(c['translation_m'],3,'translation_m',-100,100)
        if 'scale_xyz' in c:vec(c['scale_xyz'],3,'scale_xyz',0.001,100)
        if 'material_id' in c:ident(c['material_id'],'material_id')
    if 'reason' in spec and (not isinstance(spec['reason'],str) or len(spec['reason'])>500):raise ValueError('reason invalid')
    if not re.fullmatch(r'[a-f0-9]{64}',str(spec.get('expected_snapshot_sha256',''))):
        raise ValueError('expected_snapshot_sha256 required; capture hash of stable before-inspect JSON')
    return {'status':'VALIDATED_SPEC_NOT_EXECUTED','affected_parts':sorted(affected)}


def validate_lod(spec: dict) -> dict:
    strict_keys(spec,{'schema_version','project_id','ratios','protected_part_ids','max_triangles_lod0'},'lod')
    if spec.get('schema_version')!='1.3':raise ValueError('lod schema_version must be 1.3')
    ident(spec.get('project_id'),'project_id')
    ratios=spec.get('ratios')
    if not isinstance(ratios,list) or not 1<=len(ratios)<=4:raise ValueError('LOD requires 1..4 ratios')
    prev=1.0
    for r in ratios:
        x=num(r,'lod.ratio',0.02,0.99)
        if x>=prev:raise ValueError('LOD ratios must strictly decrease')
        prev=x
    parts=spec.get('protected_part_ids',[])
    if not isinstance(parts,list) or len(parts)>100:raise ValueError('protected_part_ids invalid')
    for p in parts:ident(p,'protected_part_ids')
    if len(parts)!=len(set(parts)):raise ValueError('duplicate protected part')
    if 'max_triangles_lod0' in spec:num(spec['max_triangles_lod0'],'max_triangles_lod0',1,10000000)
    return {'status':'VALIDATED_SPEC_NOT_EXECUTED','lod_count':len(ratios)+1,'protected_parts':parts}


def validate_variant_config(config: dict) -> dict:
    strict_keys(config,{'schema_version','family_id','slots','rules'},'variant config')
    if config.get('schema_version')!='1.3':raise ValueError('variant config schema_version must be 1.3')
    ident(config.get('family_id'),'family_id')
    slots=config.get('slots')
    if not isinstance(slots,dict) or not 1<=len(slots)<=24:raise ValueError('slots must be 1..24')
    total=1
    for key,entry in slots.items():
        ident(key,'slot')
        strict_keys(entry,{'options'},'slot definition')
        opts=entry.get('options')
        if not isinstance(opts,dict) or not 1<=len(opts)<=30:raise ValueError('slot.options invalid')
        for choice,meta in opts.items():
            ident(choice,'option');strict_keys(meta,{'show_part_ids','hide_part_ids','material_overrides'},'option')
            visible=meta.get('show_part_ids',[]);hidden=meta.get('hide_part_ids',[])
            if not isinstance(visible,list) or not isinstance(hidden,list):raise ValueError('part ID arrays required')
            for p in visible+hidden:ident(p,'part')
            if set(visible)&set(hidden):raise ValueError('same part shown and hidden')
            maps=meta.get('material_overrides',{})
            if not isinstance(maps,dict):raise ValueError('material_overrides must be object')
            for k,v in maps.items():ident(k,'part');ident(v,'material_id')
        total*=len(opts)
        if total>1000000:raise ValueError('variant family exceeds safe upper bound')
    rules=config.get('rules',[])
    if not isinstance(rules,list) or len(rules)>100:raise ValueError('rules must be <=100')
    for rule in rules:
        strict_keys(rule,{'when','require','forbid'},'rule')
        for key in ('when','require','forbid'):
            choices=rule.get(key,{})
            if not isinstance(choices,dict):raise ValueError(f'rule {key} must be mapping')
            for slot,choice in choices.items():
                if slot not in slots or choice not in slots[slot]['options']:
                    raise ValueError(f'rule {key} invalid slot/choice: {slot}/{choice}')
        if not rule.get('when') or not (rule.get('require') or rule.get('forbid')):
            raise ValueError('rule requires when and require/forbid')
    return {'status':'VALIDATED_SPEC_NOT_EXECUTED','theoretical_combinations':total}


def resolve_variant(config: dict, selected: dict) -> dict:
    info=validate_variant_config(config)
    if not isinstance(selected,dict) or set(selected)!=set(config['slots']):raise ValueError('selection must contain exactly one option per slot')
    for slot,value in selected.items():
        if value not in config['slots'][slot]['options']:raise ValueError('invalid variant selection '+slot)
    reasons=[]
    for i,rule in enumerate(config.get('rules',[])):
        if all(selected[k]==v for k,v in rule['when'].items()):
            if any(selected[k]!=v for k,v in rule.get('require',{}).items()):reasons.append(f'rule[{i}] required combination violated')
            if any(selected[k]==v for k,v in rule.get('forbid',{}).items()):reasons.append(f'rule[{i}] forbidden combination')
    show=set();hide=set();materials={}
    for slot,choice in selected.items():
        detail=config['slots'][slot]['options'][choice]
        show.update(detail.get('show_part_ids',[]));hide.update(detail.get('hide_part_ids',[]))
        for k,v in detail.get('material_overrides',{}).items():
            if k in materials and materials[k]!=v:reasons.append(f'conflicting materials for {k}')
            materials[k]=v
    if show&hide:reasons.append('conflicting part visibility: '+','.join(sorted(show&hide)))
    return {'status':'BLOCKED' if reasons else 'VALIDATED_SELECTION_NOT_BUILT',
            'selected':selected,'show_part_ids':sorted(show),'hide_part_ids':sorted(hide),
            'material_overrides':materials,'reasons':reasons,'theoretical_combinations':info['theoretical_combinations']}


def validate_assembly(spec: dict) -> dict:
    strict_keys(spec,{'schema_version','project_id','constraints'},'assembly')
    if spec.get('schema_version')!='1.3':raise ValueError('assembly schema_version must be 1.3')
    ident(spec.get('project_id'),'project_id')
    constraints=spec.get('constraints')
    if not isinstance(constraints,list) or not 1<=len(constraints)<=200:raise ValueError('assembly constraints must be 1..200')
    seen_constraints=set()
    for c in constraints:
        cid=ident(c.get('id'),'constraint.id')
        if cid in seen_constraints:raise ValueError('duplicate assembly constraint id')
        seen_constraints.add(cid)
        strict_keys(c,{'id','part_a','part_b','kind','min_clearance_mm','max_gap_mm','axis','tolerance_mm'},'constraint')
        a=ident(c.get('part_a'),'part_a');b=ident(c.get('part_b'),'part_b')
        if a==b:raise ValueError('assembly constraint must reference distinct parts')
        kind=c.get('kind')
        if kind not in ('clearance','proximity','align_center'):raise ValueError('unsupported assembly kind')
        if kind=='clearance':num(c.get('min_clearance_mm'),'min_clearance_mm',0,100000)
        if kind=='proximity':num(c.get('max_gap_mm'),'max_gap_mm',0,100000)
        if kind=='align_center':
            if c.get('axis') not in ('x','y','z'):raise ValueError('align_center requires axis')
            num(c.get('tolerance_mm'),'tolerance_mm',0,100000)
    return {'status':'VALIDATED_SPEC_NOT_EXECUTED','constraints':len(constraints)}


def _bbox(p):
    lo=p.get('world_bbox_min_m');hi=p.get('world_bbox_max_m')
    return vec(lo,3,'bbox_min'),vec(hi,3,'bbox_max')


def audit_assembly(spec: dict, inspect: dict) -> dict:
    validate_assembly(spec)
    if inspect.get('status')!='MEASURED_NOT_APPROVED':raise ValueError('requires actual Blender inspect data')
    lookup={}
    for p in inspect.get('parts',[]):
        if p.get('part_id'):
            lookup.setdefault(p['part_id'],[]).append(p)
    results=[]
    for c in spec['constraints']:
        a=lookup.get(c['part_a'],[]);b=lookup.get(c['part_b'],[])
        if len(a)!=1 or len(b)!=1:
            results.append({'id':c['id'],'status':'INDETERMINATE','reason':'missing or ambiguous part id'});continue
        alo,ahi=_bbox(a[0]);blo,bhi=_bbox(b[0])
        gaps=[max(blo[i]-ahi[i],alo[i]-bhi[i],0) for i in range(3)]
        # Upper-bound gap between AABB boxes; overlapping AABBs are NOT mesh contact proof.
        gap=math.sqrt(sum(x*x for x in gaps))*1000
        overlaps=[max(0,min(ahi[i],bhi[i])-max(alo[i],blo[i])) for i in range(3)]
        if c['kind']=='proximity':
            ok=gap<=c['max_gap_mm'];note='AABB proximity proxy; exact mesh contact not established'
        elif c['kind']=='clearance':
            # If boxes overlap, cannot infer exact clearance, so INDETERMINATE not false FAIL.
            if not gap:
                results.append({'id':c['id'],'status':'INDETERMINATE','reason':'AABBs overlap; exact clearance requires mesh-level inspection'});continue
            ok=gap>=c['min_clearance_mm'];note='AABB gap lower-bound; exact mesh clearance may be larger'
        else:
            idx={'x':0,'y':1,'z':2}[c['axis']]
            delta=abs((alo[idx]+ahi[idx]-blo[idx]-bhi[idx])*500)
            ok=delta<=c['tolerance_mm'];note='AABB center alignment only'
        results.append({'id':c['id'],'status':'PASS_PROXY' if ok else 'FAIL_PROXY','gap_mm':round(gap,3),
                        'axis_overlap_mm':[round(x*1000,3) for x in overlaps],'note':note})
    s='FAIL' if any(r['status']=='FAIL_PROXY' for r in results) else 'INDETERMINATE' if any(r['status']=='INDETERMINATE' for r in results) else 'PROXY_CHECKED_NOT_CERTIFIED'
    return {'status':s,'results':results,'note':'Bounding boxes are broadphase proxies, not proof of physically valid assembly or manufacturing tolerances.'}
