#!/usr/bin/env python3
"""Portable CLI for Blender Forge Pro metadata validation and handoff."""
from __future__ import annotations
import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from forge_core import read_json, validate_project, route_project, check_evidence, build_manifest, verify_manifest


def emit(obj, output=None):
    s=json.dumps(obj,indent=2,ensure_ascii=False)+'\n'
    if output:
        Path(output).parent.mkdir(parents=True,exist_ok=True)
        Path(output).write_text(s,encoding='utf-8')
    print(s,end='')


def main():
    p=argparse.ArgumentParser(description='Blender Forge Pro portable validation CLI')
    sub=p.add_subparsers(dest='command',required=True)
    doctor=sub.add_parser('doctor')
    doctor.add_argument('--json',action='store_true')
    v=sub.add_parser('validate-project');v.add_argument('project');v.add_argument('--root',default='.');v.add_argument('--allow-missing-references',action='store_true');v.add_argument('--out')
    ro=sub.add_parser('route');ro.add_argument('project');ro.add_argument('--out')
    ev=sub.add_parser('check-evidence');ev.add_argument('project');ev.add_argument('--evidence',required=True);ev.add_argument('--root',default='.');ev.add_argument('--out')
    init=sub.add_parser('init-output');init.add_argument('project');init.add_argument('--out',required=True)
    mf=sub.add_parser('manifest');mf.add_argument('--root',required=True);mf.add_argument('--paths',nargs='+',required=True);mf.add_argument('--out',required=True)
    vm=sub.add_parser('verify-manifest');vm.add_argument('manifest');vm.add_argument('--root',required=True)
    args=p.parse_args()
    try:
        if args.command=='doctor':
            emit({'python':sys.version.split()[0],'python_ok':sys.version_info>=(3,10),'blender_on_path':bool(shutil.which('blender')),
                  'optional_modules':{x:importlib.util.find_spec(x) is not None for x in ('PIL','numpy','trimesh')},
                  'note':'Blender availability and an actual scene are required for model creation and art QA.'});return 0
        if args.command=='validate-project':
            result=validate_project(read_json(Path(args.project)),Path(args.root),allow_missing_refs=args.allow_missing_references)
            emit(result,args.out);return 0 if result['status']=='PASS' else 2
        if args.command=='route':
            emit(route_project(read_json(Path(args.project))),args.out);return 0
        if args.command=='check-evidence':
            result=check_evidence(read_json(Path(args.project)),read_json(Path(args.evidence)),Path(args.root))
            emit(result,args.out);return 0 if result['status']=='PASS' else 2
        if args.command=='init-output':
            pr=read_json(Path(args.project)); folder=Path(args.out).resolve();
            if not folder.exists() and folder.parent.is_dir(): folder.mkdir()
            if not folder.is_dir():raise ValueError('destination needs existing parent directory')
            for part in ['input','planning','work/checkpoints','deliverables','qa/views','qa/geo_proofs']:
                (folder/part).mkdir(parents=True,exist_ok=True)
            dst=folder/'planning'/'project.json'
            if dst.exists():raise ValueError('planning/project.json already exists; refuse overwrite')
            dst.write_text(json.dumps(pr,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            emit({'status':'PASS','output_root':str(folder),'manifest_plan':str(dst)});return 0
        if args.command=='manifest':
            result=build_manifest(Path(args.root),args.paths);emit(result,args.out);return 0
        if args.command=='verify-manifest':
            result=verify_manifest(Path(args.root),read_json(Path(args.manifest)));emit(result);return 0 if result['status']=='PASS' else 2
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as e:
        emit({'status':'ERROR','error':str(e)});return 3
    return 3


if __name__=='__main__':
    sys.exit(main())
