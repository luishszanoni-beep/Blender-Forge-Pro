#!/usr/bin/env python3
"""Run only the trusted bundled Blender worker via a local, explicit Blender exe.

No arbitrary script arguments or auto installation. Full content/artistic QA
requires actual Blender + visual inspection beyond this bridge.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

TRUSTED_TASKS={'diagnostic-sample','inspect','render-views','export-glb','geometry-proof',
               'build-recipe','apply-repair','create-lods','build-variant','assembly-audit'}
SPEC_TASKS={'build-recipe','apply-repair','create-lods','build-variant','assembly-audit'}
BLEND_NOT_REQUIRED={'diagnostic-sample','build-recipe'}
WORKER=(Path(__file__).resolve().parent/'blender_worker.py').resolve()


def resolve_exe(value: str):
    exe=shutil.which(value)
    if not exe:
        p=Path(value).expanduser()
        if p.is_file():exe=str(p.resolve())
    return exe


def prepare_argv(exe: str, task: str, out: Path, blend=None, feature_id=None, spec=None) -> list[str]:
    if task not in TRUSTED_TASKS:
        raise ValueError('unsupported task; arbitrary script execution forbidden')
    if task not in BLEND_NOT_REQUIRED and not blend:
        raise ValueError('this task requires --blend')
    if task in SPEC_TASKS:
        if not spec or not Path(spec).is_file() or Path(spec).suffix.lower()!='.json':
            raise ValueError('task requires a readable --spec JSON file')
        if Path(spec).stat().st_size>256000:
            raise ValueError('spec JSON exceeds 256 KB limit')
    elif spec:
        raise ValueError('--spec is only permitted for declared spec-driven tasks')
    if task=='geometry-proof' and (not feature_id or not isinstance(feature_id,str) or not feature_id.replace('-', '').replace('_','').isalnum() or len(feature_id)>64):
        raise ValueError('geometry-proof requires safe --feature-id')
    if blend and (not Path(blend).is_file() or Path(blend).suffix.lower()!='.blend'):
        raise ValueError('--blend must be a real .blend file')
    if not out.is_absolute():
        raise ValueError('--out must be absolute, explicit project-owned output path')
    if not WORKER.is_file():
        raise ValueError('trusted Blender worker not found')
    args=[str(exe),'--background','--factory-startup','--disable-autoexec','--python',str(WORKER),'--','--task',task,'--out',str(out)]
    if blend:args.extend(['--blend',str(Path(blend).resolve())])
    if feature_id:args.extend(['--feature-id',feature_id])
    if spec:args.extend(['--spec',str(Path(spec).resolve())])
    return args


def main():
    p=argparse.ArgumentParser(description='Restricted Blender subprocess bridge')
    p.add_argument('action',choices=['doctor','run']);p.add_argument('--blender',default='blender')
    p.add_argument('--task',choices=sorted(TRUSTED_TASKS));p.add_argument('--blend')
    p.add_argument('--out');p.add_argument('--feature-id');p.add_argument('--spec');p.add_argument('--timeout',type=int,default=480)
    p.add_argument('--air-project-root');p.add_argument('--air-holder');p.add_argument('--air-token')
    a=p.parse_args()
    exe=resolve_exe(a.blender)
    if not exe:
        print(json.dumps({'status':'UNAVAILABLE','error':'Blender executable not found. No scene was edited.'},indent=2))
        return 3
    if a.action=='doctor':
        try:
            completed=subprocess.run([exe,'--version'],capture_output=True,text=True,timeout=15,check=False)
            print(json.dumps({'status':'PASS' if completed.returncode==0 else 'FAIL','executable':exe,
                              'version_output':'\n'.join(completed.stdout.splitlines()[:3]),'returncode':completed.returncode},indent=2))
            return 0 if completed.returncode==0 else 2
        except (OSError,subprocess.TimeoutExpired) as e:
            print(json.dumps({'status':'FAIL','error':str(e)}));return 3
    try:
        if not a.out:raise ValueError('run requires --out')
        if not a.task:raise ValueError('run requires --task')
        if not 10<=a.timeout<=1800:raise ValueError('timeout must be 10..1800 seconds')
        out=Path(a.out).expanduser().resolve()
        # Optional AIR-managed cooperative lease; mandatory in AIR-managed mode.
        managed=os.environ.get('FORGE_AIR_MANAGED','0')=='1'
        fields=[a.air_project_root,a.air_holder,a.air_token]
        if managed and not all(fields):
            raise ValueError('AIR-managed Blender execution requires project-root/holder/token lease')
        if any(fields):
            if not all(fields):raise ValueError('partial AIR lease arguments refused')
            from air_core import require_lease
            require_lease(a.air_project_root,a.air_holder,a.air_token)
            root=Path(a.air_project_root).expanduser().resolve(strict=True)
            if not out.is_relative_to(root):raise ValueError('AIR output must remain inside project root')
            for user_path in (a.blend,a.spec):
                if user_path and not Path(user_path).expanduser().resolve(strict=True).is_relative_to(root):
                    raise ValueError('AIR blend/spec path must be inside project root')
        # The caller explicitly controls output root. Do not use a shell and never pass user Python.
        if out.exists() and not out.is_dir():raise ValueError('output is not a directory')
        if not out.exists():
            if not out.parent.is_dir():raise ValueError('output directory parent does not exist')
            out.mkdir()
        argv=prepare_argv(exe,a.task,out,a.blend,a.feature_id,a.spec)
        env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
        cp=subprocess.run(argv,capture_output=True,text=True,timeout=a.timeout,check=False,env=env,cwd=str(out))
        record={'status':'PASS' if cp.returncode==0 else 'FAIL','returncode':cp.returncode,
                'task':a.task,'executable':exe,'output_dir':str(out),'stdout_tail':cp.stdout[-8000:],
                'stderr_tail':cp.stderr[-8000:]}
        log_path=out/f'bridge_{a.task}_log.json'
        if log_path.exists():raise ValueError(f'refuse to overwrite existing log: {log_path}')
        log_path.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(json.dumps(record,indent=2,ensure_ascii=False))
        return 0 if cp.returncode==0 else 2
    except subprocess.TimeoutExpired as e:
        print(json.dumps({'status':'TIMEOUT','error':str(e)}));return 3
    except (ValueError,OSError) as e:
        print(json.dumps({'status':'ERROR','error':str(e)}));return 3

if __name__=='__main__':sys.exit(main())
