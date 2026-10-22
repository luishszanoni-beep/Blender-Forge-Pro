#!/usr/bin/env python3
"""Compare measured bpy inspection snapshots for locked part regressions."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def groups(snapshot):
    by={}
    for obj in snapshot.get('parts',[]):
        if not isinstance(obj,dict) or not obj.get('part_id'):
            continue
        by.setdefault(obj['part_id'],[]).append(obj)
    return by


def compare(before, after, locks):
    errors=[];warnings=[]
    if not isinstance(locks,dict) or not isinstance(locks.get('locked_parts'),list):
        return {'status':'FAIL','errors':['lock spec must contain locked_parts array'],'warnings':[]}
    b,a=groups(before),groups(after)
    if before.get('status')!='MEASURED_NOT_APPROVED' or after.get('status')!='MEASURED_NOT_APPROVED':
        errors.append('both snapshots must be actual Blender mesh_inspect results')
    seen=set()
    for lock in locks['locked_parts']:
        if not isinstance(lock,dict):errors.append('bad locked part entry');continue
        pid=lock.get('part_id')
        if not pid or pid in seen:
            errors.append('locked part_id invalid or repeated');continue
        seen.add(pid)
        old=b.get(pid,[]);new=a.get(pid,[])
        if len(old)!=len(new) or not old:
            errors.append(f'{pid} missing or object count changed');continue
        old=sorted(old,key=lambda p:p.get('name',''));new=sorted(new,key=lambda p:p.get('name',''))
        if [x.get('name') for x in old]!=[x.get('name') for x in new]:
            warnings.append(f'{pid} object names changed; tracking uses IDs and list order')
        for i,(x,y) in enumerate(zip(old,new)):
            if lock.get('lock_geometry',True):
                ah,bh=x.get('world_mesh_fingerprint'),y.get('world_mesh_fingerprint')
                if not ah or not bh or ah=='NOT_COMPUTED_LARGE' or bh=='NOT_COMPUTED_LARGE':
                    errors.append(f'{pid}[{i}] missing verifiable mesh fingerprint')
                elif ah!=bh:
                    errors.append(f'{pid}[{i}] mesh geometry fingerprint changed')
            tol=lock.get('max_bbox_delta_mm',0)
            if not isinstance(tol,(int,float)) or isinstance(tol,bool) or tol<0:
                errors.append(f'{pid} bbox tolerance invalid');continue
            bb=x.get('world_bbox_min_m',[])+x.get('world_bbox_max_m',[])
            aa=y.get('world_bbox_min_m',[])+y.get('world_bbox_max_m',[])
            if len(aa)!=6 or len(bb)!=6:
                errors.append(f'{pid}[{i}] missing world bbox');continue
            if any(not isinstance(v,(int,float)) for v in aa+bb):
                errors.append(f'{pid}[{i}] malformed bbox');continue
            if max(abs(u-v) for u,v in zip(aa,bb))*1000>tol+1e-7:
                errors.append(f'{pid}[{i}] bbox moved beyond {tol}mm')
            if lock.get('lock_materials',False) and x.get('materials')!=y.get('materials'):
                errors.append(f'{pid}[{i}] material assignment changed')
    if not seen:errors.append('no locked parts declared')
    return {'status':'FAIL' if errors else 'PASS','errors':errors,'warnings':warnings,
            'note':'Geometric/assignment regression checks; not a perceptual reference or shader-node fidelity guarantee.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('before');p.add_argument('after');p.add_argument('--locks',required=True);p.add_argument('--out');args=p.parse_args()
    try:
        a=json.loads(Path(args.before).read_text());b=json.loads(Path(args.after).read_text())
        c=json.loads(Path(args.locks).read_text());result=compare(a,b,c)
    except (ValueError,OSError,TypeError,json.JSONDecodeError) as e:result={'status':'ERROR','errors':[str(e)]}
    text=json.dumps(result,indent=2,ensure_ascii=False)+'\n';print(text,end='')
    if args.out:Path(args.out).write_text(text,encoding='utf-8')
    return 0 if result['status']=='PASS' else 2

if __name__=='__main__':sys.exit(main())
