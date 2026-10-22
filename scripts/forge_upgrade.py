#!/usr/bin/env python3
"""Forge Pro V1.3: safe JSON spec validation, alignment, visual regression and benchmarks.

The CLI validates contracts; real geometry is produced ONLY inside Blender using
blender_bridge.py and fixed bpy tasks. No successful validation means final art.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from forge_core import read_json
from forge_v13_core import (validate_recipe,validate_repair,validate_lod,
                            validate_variant_config,resolve_variant,validate_assembly,audit_assembly)
from reference_alignment import align
from regress_views import analyze
from benchmark_runner import validate_run,compare_runs


def main():
    p=argparse.ArgumentParser(description='Forge V1.3 spec and evidence validation')
    p.add_argument('action',choices=['recipe','repair','lod','variant-config','variant-selection',
                                     'assembly','assembly-report','align-reference','regress-360','benchmark','snapshot-hash'])
    p.add_argument('file');p.add_argument('--root',default='.');p.add_argument('--selection')
    p.add_argument('--inspection');p.add_argument('--baseline');p.add_argument('--out')
    a=p.parse_args()
    try:
        data=read_json(Path(a.file));root=Path(a.root)
        if a.action=='recipe':result=validate_recipe(data)
        elif a.action=='repair':result=validate_repair(data)
        elif a.action=='lod':result=validate_lod(data)
        elif a.action=='variant-config':result=validate_variant_config(data)
        elif a.action=='variant-selection':
            if not a.selection:raise ValueError('variant-selection requires --selection')
            result=resolve_variant(data,read_json(Path(a.selection)))
        elif a.action=='assembly':result=validate_assembly(data)
        elif a.action=='assembly-report':
            if not a.inspection:raise ValueError('assembly-report requires --inspection')
            result=audit_assembly(data,read_json(Path(a.inspection)))
        elif a.action=='align-reference':result=align(data)
        elif a.action=='regress-360':result=analyze(data,root)
        elif a.action=='snapshot-hash':
            if data.get('status')!='MEASURED_NOT_APPROVED' or not isinstance(data.get('parts'),list):
                raise ValueError('snapshot-hash requires actual Blender inspect report')
            digest=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()
            result={'status':'HASH_COMPUTED_NOT_QA','expected_snapshot_sha256':digest}
        elif a.action=='benchmark':
            result=compare_runs(read_json(Path(a.baseline)),data,root) if a.baseline else validate_run(data,root)
    except (KeyError,ValueError,TypeError,OSError,json.JSONDecodeError) as e:
        result={'status':'ERROR','error':str(e)}
    txt=json.dumps(result,indent=2,ensure_ascii=False)+'\n';print(txt,end='')
    if a.out:
        path=Path(a.out)
        if path.exists():
            print('ERROR: refuse overwrite existing report')
            return 3
        if not path.parent.is_dir():print('ERROR: output parent missing');return 3
        path.write_text(txt,encoding='utf-8')
    return 0 if result['status'] not in ('ERROR','FAIL','BLOCKED','INDETERMINATE','NOT_EXECUTED') else 2

if __name__=='__main__':raise SystemExit(main())
