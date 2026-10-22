#!/usr/bin/env python3
"""Explicit geometry detail allocation under destination triangle budgets.

Uses supplied projected pixel sizes; no fake calibration or camera-distance estimates.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from forge_v13_core import num,ident,strict_keys


def plan(spec: dict) -> dict:
    strict_keys(spec,{'schema_version','project_id','destination','triangle_budget','base_triangles','features'},'detail plan')
    if spec.get('schema_version')!='1.3':raise ValueError('detail schema must be 1.3')
    ident(spec.get('project_id'),'project_id')
    if spec.get('destination') not in ('render','web_glb','roblox','general'):
        raise ValueError('destination invalid')
    budget=int(num(spec.get('triangle_budget'),'triangle_budget',1,10000000))
    base=int(num(spec.get('base_triangles'),'base_triangles',0,budget))
    features=spec.get('features')
    if not isinstance(features,list) or not 1<=len(features)<=200:raise ValueError('features must be 1..200')
    seen=set();entries=[]
    for f in features:
        strict_keys(f,{'id','representation','projected_size_px','triangle_cost','priority','method'},'feature')
        fid=ident(f.get('id'),'feature.id')
        if fid in seen:raise ValueError('duplicate feature')
        seen.add(fid)
        rep=f.get('representation')
        if rep not in ('geometry','either','material'):raise ValueError('representation invalid')
        projected=num(f.get('projected_size_px'),'projected_size_px',0,100000)
        triangles=int(num(f.get('triangle_cost'),'triangle_cost',0,10000000))
        priority=f.get('priority','normal')
        if priority not in ('critical','high','normal','low'):raise ValueError('invalid priority')
        method=f.get('method','mesh')
        if method not in ('mesh','quilt_panel','seam_mesh','groove_boolean','material_bake'):
            raise ValueError('unsupported detail method')
        if rep=='geometry' and (triangles==0 or method=='material_bake'):
            raise ValueError('geometry required; actual mesh triangle budget and method required')
        entries.append({'id':fid,'representation':rep,'projected_size_px':projected,
                        'triangle_cost':triangles,'priority':priority,'method':method})
    mandatory=sum(f['triangle_cost'] for f in entries if f['representation']=='geometry')
    if base+mandatory>budget:
        return {'status':'BLOCKED_GEOMETRY_BUDGET','base_triangles':base,'required_geometry_triangles':mandatory,
                'budget':budget,'overage':base+mandatory-budget,
                'note':'Must revise triangle budget or obtain user approval to change geometry requirements.'}
    used=base+mandatory;decisions=[]
    for f in entries:
        if f['representation']=='geometry':
            decisions.append({'id':f['id'],'route':'ACTUAL_GEOMETRY_REQUIRED','triangle_cost':f['triangle_cost']})
    optional=sorted((f for f in entries if f['representation']!='geometry'),
                    key=lambda f:({'critical':0,'high':1,'normal':2,'low':3}[f['priority']],-f['projected_size_px'],f['id']))
    for f in optional:
        if f['representation']=='material':
            route='MATERIAL_ONLY_AS_SPECIFIED';cost=0
        elif f['projected_size_px']>=6 and used+f['triangle_cost']<=budget and f['method']!='material_bake':
            route='GEOMETRY_PLANNED';cost=f['triangle_cost'];used+=cost
        else:
            route='APPEARANCE_DETAIL_IF_ALLOWED';cost=0
        decisions.append({'id':f['id'],'route':route,'triangle_cost':cost})
    return {'status':'DETAIL_ALLOCATION_PROPOSED_NOT_RENDERED','destination':spec['destination'],
            'triangle_budget':budget,'triangle_count_planned':used,
            'decisions':decisions,
            'note':'Heuristic allocation; projected size and triangle costs must come from measured data or declared assumptions. No Blender scene was created.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('spec');p.add_argument('--out');a=p.parse_args()
    try:r=plan(json.loads(Path(a.spec).read_text(encoding='utf-8')))
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as e:r={'status':'ERROR','error':str(e)}
    s=json.dumps(r,indent=2,ensure_ascii=False)+'\n';print(s,end='')
    if a.out:Path(a.out).write_text(s,encoding='utf-8')
    return 0 if r['status']=='DETAIL_ALLOCATION_PROPOSED_NOT_RENDERED' else 2
if __name__=='__main__':raise SystemExit(main())
