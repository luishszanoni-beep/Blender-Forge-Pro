#!/usr/bin/env python3
"""AIR V1.4 CLI: offline model registry / quality-first task routing / scene leases.

NO LLM calls, agent creation, model override or Blender edits are performed here.
"""
from __future__ import annotations

import argparse
import json
import sys
import shutil
from pathlib import Path

from air_core import (acquire_lease, escalation, make_plan, record_benchmark,
                      release_lease, require_lease, validate_ledger,validate_registry,
                      validate_tasks,route_task)


def read_json(path):
    p=Path(path)
    if p.stat().st_size > 2_000_000:
        raise ValueError('input JSON exceeds 2 MB')
    return json.loads(p.read_text(encoding='utf-8'))


def emit(value,out=None):
    text=json.dumps(value,indent=2,ensure_ascii=False)+'\n'
    if out:
        path=Path(out)
        if path.exists():raise ValueError('refuse to overwrite output')
        if not path.parent.is_dir():raise ValueError('output directory parent missing')
        with path.open('x',encoding='utf-8') as stream:stream.write(text)
    print(text,end='')


def main(argv=None):
    p=argparse.ArgumentParser(description='Blender Forge AIR: offline capacity/cost router (no actual subagent spawning)')
    s=p.add_subparsers(dest='command',required=True)
    d=s.add_parser('doctor');d.add_argument('--registry')
    r=s.add_parser('validate-registry');r.add_argument('registry')
    t=s.add_parser('validate-tasks');t.add_argument('tasks')
    q=s.add_parser('route');q.add_argument('tasks');q.add_argument('--registry',required=True)
    q.add_argument('--ledger');q.add_argument('--out')
    e=s.add_parser('escalate');e.add_argument('tasks');e.add_argument('--registry',required=True)
    e.add_argument('--ledger');e.add_argument('--task-id',required=True)
    e.add_argument('--previous-route',required=True)
    e.add_argument('--reason',required=True,choices=['QUALITY_FAIL','TOOL_FAILURE','REFERENCE_GAP','BUDGET_FAILURE','SCOPE_VIOLATION'])
    e.add_argument('--attempts',required=True,type=int)
    b=s.add_parser('record');b.add_argument('record');b.add_argument('--ledger',required=True)
    b.add_argument('--root',required=True);b.add_argument('--evidence');b.add_argument('--out',required=True)
    for name in ('lease-acquire','lease-check','lease-release'):
        sub=s.add_parser(name);sub.add_argument('--project-root',required=True)
        sub.add_argument('--holder',required=True)
        if name!='lease-acquire':sub.add_argument('--token',required=True)
    a=p.parse_args(argv)
    try:
        if a.command=='doctor':
            result={'status':'ADVISORY_ONLY_NOT_HOST_VERIFIED',
                    'python_version':sys.version.split()[0],
                    'blender_executable_on_path':bool(shutil.which('blender')),
                    'provider_model_inventory_observed':False,
                    'subagent_spawn_capability_observed':False,
                    'effort_override_capability_observed':False,
                    'note':'AIR does not query model accounts or APIs; attach an authorized host adapter for real delegation.'}
            if a.registry:
                result['declared_registry']=validate_registry(read_json(a.registry))
        elif a.command=='validate-registry':
            doc=read_json(a.registry);result=validate_registry(doc)
        elif a.command=='validate-tasks':
            result=validate_tasks(read_json(a.tasks))
        elif a.command=='route':
            reg=read_json(a.registry);task=read_json(a.tasks)
            ledger=read_json(a.ledger) if a.ledger else None
            result=make_plan(task,reg,ledger)
            emit(result,a.out)
            return 0 if result['status']=='PLANNED_NOT_EXECUTED' else 2
        elif a.command=='escalate':
            reg=read_json(a.registry);task_doc=read_json(a.tasks)
            validate_tasks(task_doc);validate_registry(reg)
            task=next((t for t in task_doc['tasks'] if t['id']==a.task_id),None)
            if task is None:raise ValueError('task_id not found')
            prev=read_json(a.previous_route)
            if 'routes' in prev:
                prev=next((r for r in prev['routes'] if r['task_id']==a.task_id),None)
                if prev is None:raise ValueError('task not found in previous plan')
            ledger=read_json(a.ledger) if a.ledger else None
            result=escalation(task,prev,a.reason,a.attempts,reg,ledger)
        elif a.command=='record':
            record=read_json(a.record)
            ledger=read_json(a.ledger) if Path(a.ledger).is_file() else {'schema_version':'1.4','records':[]}
            result=record_benchmark(ledger,record,a.evidence,a.root)
            emit(result,a.out)
            return 0
        elif a.command=='lease-acquire':
            result=acquire_lease(a.project_root,a.holder)
        elif a.command=='lease-check':
            result=require_lease(a.project_root,a.holder,a.token)
        elif a.command=='lease-release':
            result=release_lease(a.project_root,a.holder,a.token)
        else:raise ValueError('unsupported command')
        emit(result)
        return 0
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as exc:
        print(json.dumps({'status':'ERROR','error':str(exc)},ensure_ascii=False,indent=2))
        return 3


if __name__=='__main__':sys.exit(main())
