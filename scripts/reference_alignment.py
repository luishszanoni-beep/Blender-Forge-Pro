#!/usr/bin/env python3
"""Measured 2D landmark alignment for a known orthographic view (NOT camera recovery).

Input consists of corresponding projected model-space coordinates and pixels.
Camera orientation, crop and orthographic assumption MUST be independently verified.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from forge_v13_core import num, vec, ident, strict_keys


def align(doc: dict) -> dict:
    strict_keys(doc,{'schema_version','reference_id','view','projection','image_size_px','camera_verified',
                     'landmarks','max_rms_px','max_residual_px','verified_by'},'alignment')
    if doc.get('schema_version')!='1.3':raise ValueError('alignment schema_version must be 1.3')
    ident(doc.get('reference_id'),'reference_id')
    if doc.get('view') not in ('front','back','left','right','top','bottom'):
        raise ValueError('orthographic alignment requires explicit named cardinal view')
    img=vec(doc.get('image_size_px'),2,'image_size_px',1,20000)
    if any(x!=int(x) for x in img):raise ValueError('image dimensions must be integers')
    landmarks=doc.get('landmarks')
    if not isinstance(landmarks,list) or not 3<=len(landmarks)<=60:raise ValueError('3..60 matching landmarks required')
    src=[];dst=[];names=set()
    for x in landmarks:
        strict_keys(x,{'id','model_xy_m','pixel_xy'},'landmark')
        name=ident(x.get('id'),'landmark.id')
        if name in names:raise ValueError('duplicate landmark')
        names.add(name)
        a=vec(x.get('model_xy_m'),2,'model_xy_m',-1000,1000)
        b=vec(x.get('pixel_xy'),2,'pixel_xy',-100000,100000)
        src.append(a);dst.append(b)
    threshold=num(doc.get('max_rms_px',5),'max_rms_px',0.01,1000)
    residual_threshold=num(doc.get('max_residual_px',10),'max_residual_px',0.01,1000)
    sx=sum(x[0] for x in src)/len(src);sy=sum(x[1] for x in src)/len(src)
    tx=sum(x[0] for x in dst)/len(src);ty=sum(x[1] for x in dst)/len(src)
    a=sum((p[0]-sx)*(q[0]-tx)+(p[1]-sy)*(q[1]-ty) for p,q in zip(src,dst))
    b=sum((p[0]-sx)*(q[1]-ty)-(p[1]-sy)*(q[0]-tx) for p,q in zip(src,dst))
    denom=sum((p[0]-sx)**2+(p[1]-sy)**2 for p in src)
    if denom<1e-12:raise ValueError('model landmarks degenerate or identical')
    cx=a/denom;cy=b/denom
    scale=math.hypot(cx,cy)
    if not 0.01<=scale<=1000000:raise ValueError('scale unsupported or degenerate')
    move_x=tx-cx*sx+cy*sy
    move_y=ty-cy*sx-cx*sy
    errors=[]
    for p,q in zip(src,dst):
        x=cx*p[0]-cy*p[1]+move_x;y=cy*p[0]+cx*p[1]+move_y
        errors.append(math.hypot(x-q[0],y-q[1]))
    rms=math.sqrt(sum(e*e for e in errors)/len(errors));worst=max(errors)
    aligned=bool(doc.get('projection')=='orthographic' and doc.get('camera_verified') is True and
                 isinstance(doc.get('verified_by'),str) and doc['verified_by'].strip())
    status='LANDMARK_ALIGNED_PENDING_VISUAL' if aligned and rms<=threshold and worst<=residual_threshold else 'INDETERMINATE'
    return {'status':status,'reference_id':doc['reference_id'],'view':doc['view'],
            'pixels_per_meter':round(scale,6),'rotation_deg':round(math.degrees(math.atan2(cy,cx)),6),
            'matrix_model_to_pixel':[[cx,-cy,move_x],[cy,cx,move_y]],
            'rms_error_px':round(rms,5),'max_error_px':round(worst,5),
            'image_size_px':img,'individual_errors_px':[round(e,5) for e in errors],
            'camera_verified':aligned,
            'note':'2D similarity alignment of DECLARED landmarks. Does not infer camera pose or certify 3D reference fidelity.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('spec');p.add_argument('--out');a=p.parse_args()
    try:r=align(json.loads(Path(a.spec).read_text(encoding='utf-8')))
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as e:r={'status':'ERROR','error':str(e)}
    s=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
    if a.out:Path(a.out).write_text(s,encoding='utf-8')
    print(s,end='');return 0 if r['status']=='LANDMARK_ALIGNED_PENDING_VISUAL' else 3
if __name__=='__main__':raise SystemExit(main())
