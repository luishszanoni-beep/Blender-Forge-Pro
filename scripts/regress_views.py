#!/usr/bin/env python3
"""Conservative multi-view render regression, not a similarity-to-reference score."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from forge_core import inside
from forge_v13_core import num


def analyze(spec: dict, root: Path, *, make_diff: bool=False) -> dict:
    views=spec.get('views')
    if spec.get('schema_version')!='1.3' or not isinstance(views,list) or not views:
        raise ValueError('regression needs schema_version 1.3 and nonempty views')
    if not isinstance(spec.get('render_profile'),str) or len(spec['render_profile'])<5:
        raise ValueError('render_profile must identify fixed lighting/camera/color management')
    if not spec.get('camera_verified') is True:
        return {'status':'INDETERMINATE','reason':'camera/crop/render settings not independently verified'}
    try:from PIL import Image,ImageChops
    except ImportError:return {'status':'INDETERMINATE','reason':'Pillow not available'}
    max_fraction=num(spec.get('max_changed_fraction',0.002),'max_changed_fraction',0,1)
    tol=int(num(spec.get('pixel_tolerance',6),'pixel_tolerance',0,255))
    findings=[];seen=set();passed=True;coverage=set()
    for view in views:
        name=view.get('name')
        if name not in ('front','back','left','right','top','bottom','front_left','front_right','back_left','back_right') or name in seen:
            raise ValueError('view name invalid or repeated')
        seen.add(name);coverage.add(name)
        before=inside(root,view.get('before'),must_exist=True)
        after=inside(root,view.get('after'),must_exist=True)
        mask_path=inside(root,view['protected_mask'],must_exist=True) if view.get('protected_mask') else None
        with Image.open(before) as b, Image.open(after) as a:
            b.load();a.load()
            if b.size!=a.size:raise ValueError(f'view {name} canvas changed')
            if b.width*b.height>16_000_000:raise ValueError('view too large for bounded regression')
            bb=b.convert('RGBA').tobytes();aa=a.convert('RGBA').tobytes()
            if mask_path:
                with Image.open(mask_path) as im:
                    im.load()
                    if im.size!=b.size:raise ValueError('mask dimensions differ')
                    mm=im.convert('L').tobytes()
            else:mm=b'\xff'*(b.width*b.height)
            compared=changed=0;maxdelta=0
            for i,m in enumerate(mm):
                if m<128:continue
                compared+=1
                v=4*i
                delta=max(abs(bb[v+k]-aa[v+k]) for k in range(4))
                if delta>tol:changed+=1
                maxdelta=max(maxdelta,delta)
            if not compared:raise ValueError('protected mask contains no compared pixels')
            fraction=changed/compared
            ok=fraction<=max_fraction
            passed=passed and ok
            findings.append({'view':name,'status':'PASS_MEASURED' if ok else 'FAIL_REGRESSION',
                             'pixels_compared':compared,'changed_pixels':changed,
                             'changed_fraction':round(fraction,8),'max_channel_delta':maxdelta})
    expected=set(spec.get('required_views',['front','back','left','right','top','bottom']))
    if not expected.issubset(coverage):
        return {'status':'INDETERMINATE','reason':'missing mandatory views','missing_views':sorted(expected-coverage),'findings':findings}
    return {'status':'PASS_MEASURED_NOT_ARTISTIC_QA' if passed else 'FAIL',
            'findings':findings,'note':'Only same-camera pixel regression. Does not certify model likeness or geometry fidelity.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('spec');p.add_argument('--root',required=True);p.add_argument('--out');a=p.parse_args()
    try:r=analyze(json.loads(Path(a.spec).read_text(encoding='utf-8')),Path(a.root))
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as e:r={'status':'ERROR','error':str(e)}
    s=json.dumps(r,ensure_ascii=False,indent=2)+'\n';print(s,end='')
    if a.out:Path(a.out).write_text(s,encoding='utf-8')
    return 0 if r['status']=='PASS_MEASURED_NOT_ARTISTIC_QA' else 2
if __name__=='__main__':raise SystemExit(main())
