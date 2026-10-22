#!/usr/bin/env python3
"""Comparison of already-calibrated binary silhouette masks, not semantic likeness."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path


def compare(src: Path, dst: Path, calibration: dict, overlay=None) -> dict:
    required=('reference_id','view','same_projection','same_scale','same_crop','verified_by')
    if any(k not in calibration for k in required) or not all(calibration.get(k) is True for k in ('same_projection','same_scale','same_crop')) or not calibration.get('verified_by'):
        return {'status':'INDETERMINATE','error':'calibration missing or projections/crop/scale not independently aligned'}
    try:
        from PIL import Image
    except ImportError:
        return {'status':'INDETERMINATE','error':'Pillow unavailable'}
    with Image.open(src) as a,Image.open(dst) as b:
        a.load();b.load()
        if a.size!=b.size:
            return {'status':'INDETERMINATE','error':'mask dimensions differ; align/crop without stretching'}
        if not a.size[0] or not a.size[1]:
            return {'status':'INDETERMINATE','error':'invalid mask size'}
        ma=a.convert('L');mb=b.convert('L');wa,ha=a.size
        pa=ma.tobytes();pb=mb.tobytes()
        for label,px in [('source',pa),('model',pb)]:
            if sum(16<v<240 for v in px) / len(px) > 0.01:
                return {'status':'INDETERMINATE','error':f'{label} contains substantial midtones; supply a binary silhouette mask, not a photograph'}
        # White foreground required, black background. Avoid ambiguous alpha assumptions.
        sa={i for i,x in enumerate(pa) if x>=128};sb={i for i,x in enumerate(pb) if x>=128}
        if not sa or not sb:
            return {'status':'INDETERMINATE','error':'empty foreground mask'}
        inter=len(sa & sb);union=len(sa|sb)
        ax=sum(i%wa for i in sa)/len(sa);ay=sum(i//wa for i in sa)/len(sa)
        bx=sum(i%wa for i in sb)/len(sb);by=sum(i//wa for i in sb)/len(sb)
        report={'status':'MEASURED','reference_id':calibration['reference_id'],'view':calibration['view'],
                'foreground_iou':round(inter/union,6),'centroid_delta_px':round(math.hypot(ax-bx,ay-by),3),
                'pixel_count_reference':len(sa),'pixel_count_model':len(sb),
                'note':'Pixel mask agreement at declared calibrated view. NOT full semantic/3D likeness.'}
        if overlay:
            o=Image.new('RGB',a.size); pix=[]
            for i in range(wa*ha):
                av=i in sa;bv=i in sb
                pix.append((235,235,235) if av and bv else ((248,93,91) if av else ((69,124,231) if bv else (22,24,30))))
            o.putdata(pix);Path(overlay).parent.mkdir(parents=True,exist_ok=True);o.save(overlay)
        return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--source-mask',required=True);p.add_argument('--model-mask',required=True)
    p.add_argument('--calibration',required=True);p.add_argument('--overlay');p.add_argument('--out');a=p.parse_args()
    try:
        cal=json.loads(Path(a.calibration).read_text(encoding='utf-8'))
        res=compare(Path(a.source_mask),Path(a.model_mask),cal,a.overlay)
    except (OSError,ValueError,json.JSONDecodeError) as e:res={'status':'INDETERMINATE','error':str(e)}
    s=json.dumps(res,indent=2,ensure_ascii=False)+'\n';print(s,end='')
    if a.out:Path(a.out).write_text(s,encoding='utf-8')
    return 0 if res['status']=='MEASURED' else 3

if __name__=='__main__':raise SystemExit(main())
