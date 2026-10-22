#!/usr/bin/env python3
"""Blender Forge Pro AIR v1.4: deterministic, advisory-first model/task routing.

No API calls, no Blender calls and no real agent spawning happen in this module.
An optional host adapter must separately verify and implement actual delegation.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = '1.4'
CLASSES = ('extra_basic', 'basic', 'medium', 'advanced', 'extra_advanced')
CLASS_LABELS = {'extra_basic':'Extra Basico', 'basic':'Basico', 'medium':'Medio',
                'advanced':'Avancado', 'extra_advanced':'Extra Avancado'}
EFFORTS = ('low', 'medium', 'high', 'extra_high')
DOMAINS = ('general','vision','spatial','code','surface','materials','topology',
           'rigging','audit','export')
SKILLS = ('reference-analyst','geometry-architect','sculpt-surface',
          'material-specialist','topology-engineer','rigging-specialist',
          'fidelity-auditor','export-engineer')
MODALITIES = ('text','image','audio','video')
TOOLS = ('none','blender','filesystem','image-inspection','reference-analysis','render')
QUALITY = ('standard','strict','critical')
ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$')
MODEL_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$')
SHA_RE = re.compile(r'^[a-f0-9]{64}$')
EFFORT_MULT = {'low':1.0,'medium':1.3,'high':1.8,'extra_high':2.5}


def ensure(ok, message):
    if not ok:
        raise ValueError(message)


def ident(value, label='id'):
    ensure(isinstance(value,str) and ID_RE.fullmatch(value) is not None,
           f'{label} must be safe identifier (1-80 chars)')
    return value


def model_ident(value, label='model_id'):
    ensure(isinstance(value,str) and MODEL_ID_RE.fullmatch(value) is not None and '..' not in value,
           f'{label} must be safe provider/model id (1-128 chars)')
    return value


def finite(value, label, lo=None, hi=None):
    ensure(type(value) in (int,float) and math.isfinite(value), f'{label} must be finite number')
    if lo is not None: ensure(value >= lo, f'{label} must be >= {lo}')
    if hi is not None: ensure(value <= hi, f'{label} must be <= {hi}')
    return float(value)


def str_enum(value, allowed, label):
    ensure(isinstance(value,str) and value in allowed, f'{label} must be one of {list(allowed)}')
    return value


def bounded_list(value, label, min_len=0, max_len=200):
    ensure(isinstance(value,list) and min_len<=len(value)<=max_len,
           f'{label} must be a list of {min_len}..{max_len} items')
    return value


def distinct_enum_list(value, allowed, label, min_len=0):
    bounded_list(value,label,min_len,30)
    ensure(all(isinstance(v,str) and v in allowed for v in value) and len(set(value)) == len(value),
           f'{label}: unsupported/duplicate value')
    return value


def _keys(obj, mandatory, optional, label):
    ensure(isinstance(obj,dict),f'{label} must be an object')
    keys=set(obj)
    ensure(set(mandatory)<=keys,f'{label}: missing {sorted(set(mandatory)-keys)}')
    ensure(keys<=set(mandatory)|set(optional),f'{label}: unknown {sorted(keys-set(mandatory)-set(optional))}')


def validate_registry(doc):
    _keys(doc,['schema_version','catalog_id','catalog_kind','models'],
          ['runtime','policy'], 'model catalog')
    ensure(doc['schema_version']==SCHEMA,'registry schema_version must equal 1.4')
    ident(doc['catalog_id'],'catalog_id')
    str_enum(doc['catalog_kind'],('fixture','production'),'catalog_kind')
    models=bounded_list(doc['models'],'models',0,150)
    ids=set()
    for m in models:
        _keys(m,['id','provider','enabled','domain_classes','modalities','tools','efforts',
                 'usd_per_1m_input','usd_per_1m_output','fixed_latency_s',
                 'seconds_per_1k_output','max_context_tokens'],
              ['effort_multiplier','effort_wire_values','notes'], 'model')
        model_ident(m['id'],'model.id');ident(m['provider'],'model.provider')
        ensure(m['id'] not in ids,'duplicate model id')
        ids.add(m['id'])
        ensure(type(m['enabled']) is bool,'model.enabled must be boolean')
        dc=m['domain_classes']
        ensure(isinstance(dc,dict) and dc,'domain_classes must be nonempty mapping')
        for domain,tier in dc.items():
            str_enum(domain,DOMAINS,'domain')
            str_enum(tier,CLASSES,'class')
        distinct_enum_list(m['modalities'],MODALITIES,'model.modalities',1)
        distinct_enum_list(m['tools'],TOOLS,'model.tools',0)
        distinct_enum_list(m['efforts'],EFFORTS,'model.efforts',1)
        for key in ('usd_per_1m_input','usd_per_1m_output','fixed_latency_s','seconds_per_1k_output'):
            finite(m[key],f'model.{key}',0,1000000)
        ensure(type(m['max_context_tokens']) is int and 512<=m['max_context_tokens']<=10000000,
               'max_context_tokens out of range')
        if 'effort_multiplier' in m:
            ensure(isinstance(m['effort_multiplier'],dict),'effort_multiplier must be object')
            for name,val in m['effort_multiplier'].items():
                str_enum(name,EFFORTS,'effort_multiplier key')
                finite(val,'effort_multiplier',0.2,10.0)
        if 'effort_wire_values' in m:
            ensure(isinstance(m['effort_wire_values'],dict),'effort_wire_values must be object')
            for alias,wire in m['effort_wire_values'].items():
                str_enum(alias,EFFORTS,'effort_wire_values key')
                ensure(alias in m['efforts'],'effort_wire_values cannot map unsupported effort')
                ensure(isinstance(wire,str) and re.fullmatch(r'[a-z][a-z0-9_-]{0,31}',wire),
                       'provider-native effort string must be short safe identifier')
        if 'notes' in m:
            ensure(isinstance(m['notes'],str) and len(m['notes'])<=800,'model.notes too long')
        if doc['catalog_kind']=='production':
            ensure(m['provider']!='fixture' and not m['id'].startswith('fixture.'),
                   'fixture profiles must never be included in production registry')
    runtime=doc.get('runtime',{'mode':'advisory','supports_subagents':False,
                               'supports_model_override':False,'supports_effort_override':False,
                               'verified_on_host':False})
    _keys(runtime,['mode','supports_subagents','supports_model_override',
                   'supports_effort_override','verified_on_host'],[], 'runtime')
    str_enum(runtime['mode'],('advisory','simulation','external_adapter'),'runtime.mode')
    for key in ('supports_subagents','supports_model_override','supports_effort_override','verified_on_host'):
        ensure(type(runtime[key]) is bool,f'runtime.{key} must be bool')
    if runtime['mode']=='simulation':
        ensure(doc['catalog_kind']=='fixture','simulation only permitted with fixture catalog')
    if runtime['mode']=='external_adapter':
        ensure(doc['catalog_kind']=='production','external_adapter requires production catalog')
    policy=doc.get('policy',{})
    _keys(policy,[],['max_parallel_readers','max_attempts','benchmark_min_samples',
                     'min_observed_pass_rate','latency_weight_usd_per_minute',
                     'max_estimated_cost_usd','max_estimated_seconds',
                     'max_project_estimated_cost_usd','max_project_estimated_seconds'], 'policy')
    for key,lo,hi in [('max_parallel_readers',1,16),('max_attempts',1,8),('benchmark_min_samples',3,100)]:
        if key in policy:ensure(type(policy[key]) is int and lo<=policy[key]<=hi,f'policy.{key} must be int {lo}..{hi}')
    for key,lo,hi in [('min_observed_pass_rate',0,1),('latency_weight_usd_per_minute',0,100),
                      ('max_estimated_cost_usd',0,100000),('max_estimated_seconds',0,1000000),
                      ('max_project_estimated_cost_usd',0,1000000),('max_project_estimated_seconds',0,10000000)]:
        if key in policy:finite(policy[key],f'policy.{key}',lo,hi)
    return {'status':'VALIDATED_CATALOG_NOT_PROVIDER_VERIFIED','catalog_id':doc['catalog_id'],
            'models':len(models),'enabled':sum(bool(m['enabled']) for m in models),
            'catalog_kind':doc['catalog_kind'],'runtime':runtime}


def validate_tasks(doc):
    _keys(doc,['schema_version','project_id','tasks'],[], 'task plan')
    ensure(doc['schema_version']==SCHEMA,'task schema_version must equal 1.4')
    ident(doc['project_id'],'project_id')
    tasks=bounded_list(doc['tasks'],'tasks',1,200)
    ids=set()
    for t in tasks:
        _keys(t,['id','skill','domain','complexity','uncertainty','impact','failure_cost',
                 'requires_modalities','requires_tools','tokens_in','tokens_out',
                 'writes_scene','depends_on','deterministic','quality'],
              ['explicit_min_effort','explicit_min_class','max_cost_usd','max_latency_s','preferred_model_id','notes','max_attempts'], 'task')
        ident(t['id'],'task.id')
        ensure(t['id'] not in ids,'duplicate task id')
        ids.add(t['id'])
        str_enum(t['skill'],SKILLS,'task.skill')
        str_enum(t['domain'],DOMAINS,'task.domain')
        for metric in ('complexity','uncertainty','impact','failure_cost'):
            ensure(type(t[metric]) is int and 1<=t[metric]<=5, f'task.{metric} must be integer 1..5')
        distinct_enum_list(t['requires_modalities'],MODALITIES,'task.requires_modalities',0)
        distinct_enum_list(t['requires_tools'],TOOLS,'task.requires_tools',0)
        for count in ('tokens_in','tokens_out'):
            ensure(type(t[count]) is int and 0<=t[count]<=10000000,f'task.{count} invalid')
        ensure(type(t['writes_scene']) is bool and type(t['deterministic']) is bool,
               'task writes_scene/deterministic must be boolean')
        if t['writes_scene']:
            ensure('blender' in t['requires_tools'], 'writes_scene requires blender tool')
        str_enum(t['quality'],QUALITY,'task.quality')
        bounded_list(t['depends_on'],'task.depends_on',0,200)
        ensure(all(isinstance(d,str) for d in t['depends_on']), 'dependencies must be identifiers')
        ensure(len(set(t['depends_on'])) == len(t['depends_on']),'duplicate task dependency')
        if 'explicit_min_effort' in t:str_enum(t['explicit_min_effort'],EFFORTS,'task.explicit_min_effort')
        if 'explicit_min_class' in t:str_enum(t['explicit_min_class'],CLASSES,'task.explicit_min_class')
        if 'max_cost_usd' in t:finite(t['max_cost_usd'],'max_cost_usd',0)
        if 'max_latency_s' in t:finite(t['max_latency_s'],'max_latency_s',0)
        if 'max_attempts' in t:
            ensure(type(t['max_attempts']) is int and 1<=t['max_attempts']<=8,'max_attempts invalid')
        if 'preferred_model_id' in t:model_ident(t['preferred_model_id'],'preferred_model_id')
        if 'notes' in t:ensure(isinstance(t['notes'],str) and len(t['notes'])<=1200,'notes invalid')
    for t in tasks:
        ensure(t['id'] not in t['depends_on'],'task cannot depend on itself')
        ensure(all(dep in ids for dep in t['depends_on']),f'task {t["id"]}: missing dependency')
    schedule=build_schedule(tasks,max_parallel_readers=4)
    return {'status':'VALIDATED_TASKS_NOT_DISPATCHED','tasks':len(tasks),
            'scene_writers':sum(t['writes_scene'] for t in tasks),'waves':len(schedule)}


def build_schedule(tasks,max_parallel_readers=4):
    ensure(type(max_parallel_readers) is int and 1<=max_parallel_readers<=16,'max_parallel_readers invalid')
    rem={t['id']:t for t in tasks}
    completed=set(); waves=[]
    while rem:
        ready=sorted((t for t in rem.values() if set(t['depends_on'])<=completed),key=lambda t:t['id'])
        ensure(ready,'task dependencies contain a cycle')
        # A writing operation is exclusive. Never mix scene readers and writers in a wave.
        readers=[t for t in ready if not t['writes_scene']]
        if readers:
            batch=readers[:max_parallel_readers]
            parallel='READ_ONLY_ONLY'
        else:
            batch=ready[:1]
            parallel='EXCLUSIVE_SCENE_WRITE'
        waves.append({'wave':len(waves)+1,'task_ids':[t['id'] for t in batch],
                      'policy':parallel,'max_concurrent':len(batch)})
        for t in batch:
            completed.add(t['id']);del rem[t['id']]
    return waves


def validate_ledger(doc):
    if doc is None:return {'schema_version':SCHEMA,'records':[]}
    _keys(doc,['schema_version','records'],[], 'performance ledger')
    ensure(doc['schema_version']==SCHEMA,'ledger schema_version must equal 1.4')
    for i,r in enumerate(bounded_list(doc['records'],'records',0,20000)):
        _keys(r,['task_id','model_id','domain','effort','result','elapsed_s','actual_cost_usd',
                 'evidence_sha256','reviewer','review_status','measured_at'],[],f'ledger.record.{i}')
        ident(r['task_id']);model_ident(r['model_id']);str_enum(r['domain'],DOMAINS,'ledger.domain')
        str_enum(r['effort'],EFFORTS,'ledger.effort')
        str_enum(r['result'],('PASS','FAIL','TOOL_FAILURE','NOT_TESTED'),'ledger.result')
        finite(r['elapsed_s'],'ledger.elapsed_s',0,1e7)
        finite(r['actual_cost_usd'],'ledger.actual_cost_usd',0,1e7)
        if r['evidence_sha256'] is not None:
            ensure(isinstance(r['evidence_sha256'],str) and SHA_RE.fullmatch(r['evidence_sha256']),
                   'evidence_sha256 must be sha256 hex or null')
        ensure(isinstance(r['reviewer'],str) and len(r['reviewer'])<=100,'reviewer invalid')
        str_enum(r['review_status'],('INDEPENDENT_REVIEW','SELF_REPORTED','NONE'),'review_status')
        ensure(isinstance(r['measured_at'],str) and len(r['measured_at'])<=60,'measured_at invalid')
        if r['result'] in ('PASS','FAIL'):
            ensure(r['review_status']=='INDEPENDENT_REVIEW' and r['evidence_sha256'] and r['reviewer'],
                   'PASS/FAIL quality observations require independently reviewed evidence and hash')
    return doc


def observed_stats(ledger, model_id, domain, effort, minimum):
    """Reported evidence has not been externally certified by this method."""
    entries=[r for r in ledger['records'] if r['model_id']==model_id and r['domain']==domain and
             r['effort']==effort and r['result'] in ('PASS','FAIL') and
             r['review_status']=='INDEPENDENT_REVIEW' and r['evidence_sha256']]
    n=len(entries)
    if n<minimum:return {'sample_size':n,'calibrated':False,'pass_rate':None,'rework_factor':1.4}
    passes=sum(r['result']=='PASS' for r in entries)
    rate=passes/n
    # Smoothed estimate for routing heuristic, not a fidelity/QA certificate.
    factor=min(4.0,(n+2)/(passes+1))
    return {'sample_size':n,'calibrated':True,'pass_rate':round(rate,3),'rework_factor':round(factor,3)}


def tier_risk(task):
    score=(.38*task['complexity']+.27*task['uncertainty']+
           .25*task['impact']+.10*task['failure_cost'])
    floor=(0 if score<1.7 else 1 if score<2.55 else 2 if score<3.4 else 3 if score<4.3 else 4)
    if task['quality']=='strict':floor=min(4,floor+1)
    if task['quality']=='critical':floor=min(4,floor+1)
    if 'explicit_min_class' in task:
        floor=max(floor,CLASSES.index(task['explicit_min_class']))
    preferred=('low' if score<1.8 else 'medium' if score<2.8 else
               'high' if score<4.3 else 'extra_high')
    if task['quality']=='critical' and EFFORTS.index(preferred)<2:preferred='high'
    if 'explicit_min_effort' in task and EFFORTS.index(task['explicit_min_effort'])>EFFORTS.index(preferred):
        preferred=task['explicit_min_effort']
    return {'score':round(score,3),'required_class':CLASSES[floor],
            'suggested_effort':preferred, 'policy':'QUALITY_FIRST_RISK_HEURISTIC_NOT_BENCHMARK'}


def _effort_choices(model, task, suggested):
    supported=sorted(model['efforts'],key=EFFORTS.index)
    lower_bound=EFFORTS.index(task.get('explicit_min_effort','low'))
    available=[e for e in supported if EFFORTS.index(e)>=lower_bound]
    if not available:return []
    # Try target effort, then nearest higher, then lower with explicitly reported fallback.
    return sorted(available,key=lambda e:(EFFORTS.index(e)<EFFORTS.index(suggested),
                 abs(EFFORTS.index(e)-EFFORTS.index(suggested)),EFFORTS.index(e)))


def estimate(model,task,effort):
    multiplier=model.get('effort_multiplier',{}).get(effort,EFFORT_MULT[effort])
    cost=multiplier*(task['tokens_in']*model['usd_per_1m_input']+
                     task['tokens_out']*model['usd_per_1m_output'])/1_000_000
    seconds=model['fixed_latency_s']+multiplier*task['tokens_out']/1000*model['seconds_per_1k_output']
    return {'estimated_cost_usd':round(cost,8),'estimated_seconds':round(seconds,3),
            'estimate_status':'UNVERIFIED_PROVIDER_ESTIMATE'}


def route_task(task,registry,ledger=None,exclude_model_ids=()):
    led=validate_ledger(ledger)
    risk=tier_risk(task)
    runtime=registry.get('runtime',{'mode':'advisory','supports_subagents':False,
               'supports_model_override':False,'supports_effort_override':False,'verified_on_host':False})
    if task['deterministic']:
        return {'task_id':task['id'],'status':'DETERMINISTIC_NO_LLM',
                'skill':task['skill'],'domain':task['domain'],'writes_scene':task['writes_scene'],
                'requires_tools':task['requires_tools'],'assignment':None,
                'note':'A known deterministic operator is required; no autonomous code generation or agent spawn.'}
    exclusions=set(exclude_model_ids)
    policies=registry.get('policy',{})
    min_n=policies.get('benchmark_min_samples',5)
    threshold=policies.get('min_observed_pass_rate',.65)
    choices=[]
    for m in registry['models']:
        if not m['enabled'] or m['id'] in exclusions:continue
        tier=m['domain_classes'].get(task['domain'])
        if tier not in CLASSES or CLASSES.index(tier)<CLASSES.index(risk['required_class']):continue
        if not set(task['requires_modalities'])<=set(m['modalities']):continue
        if not set(task['requires_tools'])<=set(m['tools']):continue
        if task['tokens_in']+task['tokens_out']>m['max_context_tokens']:continue
        for effort in _effort_choices(m,task,risk['suggested_effort']):
            stats=observed_stats(led,m['id'],task['domain'],effort,min_n)
            if stats['calibrated'] and stats['pass_rate']<threshold:continue
            perf=estimate(m,task,effort)
            max_cost=min(float(task.get('max_cost_usd',float('inf'))),
                         float(policies.get('max_estimated_cost_usd',float('inf'))))
            max_time=min(float(task.get('max_latency_s',float('inf'))),
                         float(policies.get('max_estimated_seconds',float('inf'))))
            if perf['estimated_cost_usd']>max_cost or perf['estimated_seconds']>max_time:continue
            penalty=1.2 if EFFORTS.index(effort)<EFFORTS.index(risk['suggested_effort']) else 1.0
            weight=policies.get('latency_weight_usd_per_minute',.02)
            objective=(perf['estimated_cost_usd']*stats['rework_factor']+float(weight)*
                       perf['estimated_seconds']/60)*penalty
            choices.append((objective,m,effort,perf,stats,penalty))
    if not choices:
        return {'task_id':task['id'],'status':'UNASSIGNED_QUALITY_OR_CAPABILITY_CONSTRAINT',
                'skill':task['skill'],'domain':task['domain'],'writes_scene':task['writes_scene'],
                'risk':risk,'assignment':None,
                'note':'No enabled model satisfies domain class, modalities, tools, context, effort and budget. Do not silently downgrade quality.'}
    # Do not select a cheaper under-reasoned variant if *any* acceptable model
    # can run at or above the suggested effort inside the task budget.
    sufficient=[c for c in choices if EFFORTS.index(c[2])>=EFFORTS.index(risk['suggested_effort'])]
    if sufficient:
        choices=sufficient
    # Prefer expected efficiency while preserving minimum domain capability.
    choices.sort(key=lambda x:(round(x[0],10), x[3]['estimated_cost_usd'], x[1]['id'],x[2]))
    preferred_model=task.get('preferred_model_id')
    # A preference can break a near-tie but must never override competence or budgets.
    preferred=[c for c in choices if c[1]['id']==preferred_model and c[0]<=choices[0][0]*1.03+1e-10]
    _,m,effort,perf,stats,penalty=preferred[0] if preferred else choices[0]
    downgrade=EFFORTS.index(effort)<EFFORTS.index(risk['suggested_effort'])
    # This code compiles a routing recommendation; no host delegation is performed.
    deployable=(registry['catalog_kind']=='production' and runtime['mode']=='external_adapter'
                 and runtime['verified_on_host'] and runtime['supports_subagents'] and
                 runtime['supports_model_override'] and runtime['supports_effort_override'])
    return {'task_id':task['id'],'status':'ROUTED_SIMULATION' if registry['catalog_kind']=='fixture'
            else ('HANDOFF_CANDIDATE_NOT_DISPATCHED' if deployable else 'ROUTED_ADVISORY_ONLY'),
            'skill':task['skill'],'domain':task['domain'],'writes_scene':task['writes_scene'],
            'risk':risk,
            'assignment':{'model_id':m['id'],'provider':m['provider'],
                          'domain_class':m['domain_classes'][task['domain']], 'effort':effort,
                          'provider_effort_value':m.get('effort_wire_values',{}).get(effort),
                          'model_preference_applied':bool(preferred),
                          **perf,'benchmark':stats,'effort_below_suggestion':downgrade,
                          'requires_independent_qa':True},
            'note':'Selection is a non-executed plan. Runtime flags are caller-declared and are NOT independently probed by this CLI. External host must verify and dispatch; QA gates remain authoritative.'}


def make_plan(tasks_doc,registry,ledger=None):
    validate_registry(registry)
    validate_tasks(tasks_doc)
    led=validate_ledger(ledger)
    policy=registry.get('policy',{})
    assignments=[route_task(task,registry,led) for task in tasks_doc['tasks']]
    schedule=build_schedule(tasks_doc['tasks'],policy.get('max_parallel_readers',3))
    statuses={a['status'] for a in assignments}
    missing=any(a['status']=='UNASSIGNED_QUALITY_OR_CAPABILITY_CONSTRAINT' for a in assignments)
    routes_by_id={a['task_id']:a for a in assignments}
    total_cost=round(sum((a.get('assignment') or {}).get('estimated_cost_usd',0.0) for a in assignments),8)
    llm_wave_time=round(sum(max(((routes_by_id[i].get('assignment') or {}).get('estimated_seconds',0.0))
                    for i in wave['task_ids']) for wave in schedule),3)
    budget_block=(total_cost>policy.get('max_project_estimated_cost_usd',float('inf')) or
                  llm_wave_time>policy.get('max_project_estimated_seconds',float('inf')))
    result_status=('BLOCKED_MISSING_CAPABILITY' if missing else
                   'BLOCKED_PROJECT_BUDGET' if budget_block else 'PLANNED_NOT_EXECUTED')
    return {'schema_version':SCHEMA,'project_id':tasks_doc['project_id'],
            'status':result_status,
            'estimated_project':{'llm_cost_usd':total_cost,'llm_minimum_wall_time_s':llm_wave_time,
                                 'excludes_blender_and_deterministic_execution':True,
                                 'provider_estimates_unverified':True},
            'catalog_id':registry['catalog_id'],'catalog_kind':registry['catalog_kind'],
            'runtime_capabilities':registry.get('runtime',{'mode':'advisory'}),
            'schedule':schedule,'routes':assignments,
            'execution_proof':None,'scene_edit_proof':None,'qa_approval':None,
            'note':'No subagent or Blender operation ran. Do not report plan as executed.'}


def escalation(task, previous_route, failure, attempts,registry,ledger=None):
    str_enum(failure,('QUALITY_FAIL','TOOL_FAILURE','REFERENCE_GAP','BUDGET_FAILURE',
                      'SCOPE_VIOLATION'),'failure')
    ensure(type(attempts) is int and 1<=attempts<=20,'attempts invalid')
    max_attempts=task.get('max_attempts',registry.get('policy',{}).get('max_attempts',2))
    if attempts>=max_attempts:
        return {'status':'STOP_MAX_ATTEMPTS','next_action':'Independent manual diagnosis required'}
    if failure=='TOOL_FAILURE':
        return {'status':'REPAIR_TOOL_ENVIRONMENT','next_action':'Retry after inspecting actual tool/runtime failure; do not spend more reasoning blindly'}
    if failure=='REFERENCE_GAP':
        return {'status':'NEEDS_REFERENCE_EVIDENCE','next_action':'Request/inspect missing camera views or dimensions before escalating'}
    if failure=='BUDGET_FAILURE':
        return {'status':'STOP_BUDGET','next_action':'Replan budget or deadline, preserving QA requirements'}
    if failure=='SCOPE_VIOLATION':
        return {'status':'ROLLBACK_SCENE','next_action':'Restore checkpoint and verify geometry lock before retry'}
    old=previous_route.get('assignment')
    if not old:
        return {'status':'NEEDS_MANUAL_ROUTING','next_action':'No prior valid model was assigned'}
    attempted=old['model_id']
    risk=tier_risk(task)
    previous_class=old['domain_class']
    previous_effort=old['effort']
    # A quality failure can only escalate to a stronger domain class or higher effort;
    # never silently retry a weaker model because it is cheaper.
    if CLASSES.index(previous_class)<len(CLASSES)-1:
        revised=dict(task,explicit_min_class=CLASSES[CLASSES.index(previous_class)+1],
                     explicit_min_effort=previous_effort)
        options=route_task(revised,registry,ledger,exclude_model_ids=[attempted])
        if options.get('assignment'):
            return {'status':'ESCALATED_CLASS','new_route':options,
                    'note':'New route has stronger domain class. Independent QA must verify targeted repair.'}
    if EFFORTS.index(previous_effort)<len(EFFORTS)-1:
        revised=dict(task,explicit_min_class=previous_class,
                     explicit_min_effort=EFFORTS[EFFORTS.index(previous_effort)+1])
        options=route_task(revised,registry,ledger)
        if options.get('assignment') and EFFORTS.index(options['assignment']['effort'])>EFFORTS.index(previous_effort):
            return {'status':'ESCALATED_EFFORT','new_route':options,
                    'note':'Higher reasoning effort was selected; QA approval is not automatic.'}
    # One model may fail while an equally capable peer with different strengths succeeds.
    revised=dict(task,explicit_min_class=previous_class,explicit_min_effort=previous_effort)
    options=route_task(revised,registry,ledger,exclude_model_ids=[attempted])
    if options.get('assignment'):
        return {'status':'ROUTED_TO_PEER_AFTER_FAILURE','new_route':options,
                'note':'Lateral retry, not capability escalation; inspect actual error before running.'}
    return {'status':'NEEDS_MANUAL_REVIEW','next_action':'No compatible stronger route; diagnose modeling/reference constraints before another attempt'}


def _lease_path(root):
    root=Path(root).expanduser().resolve(strict=True)
    ensure(root.is_dir(),'project root must be a real existing directory')
    folder=root/'.forge'
    ensure(not folder.is_symlink(),'refuse symlinked .forge directory')
    folder.mkdir(mode=0o700,exist_ok=True)
    ensure(folder.is_dir(),'invalid .forge directory')
    return folder/'scene_write_lease.json'


def acquire_lease(root,holder):
    ident(holder,'holder')
    path=_lease_path(root)
    token=secrets.token_hex(24)
    payload={'holder':holder,'token_sha256':hashlib.sha256(token.encode()).hexdigest(),
             'started_at_utc':datetime.now(timezone.utc).isoformat(),
             'policy':'MANUAL_RELEASE_REQUIRED','pid':os.getpid()}
    try:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError as e:
        raise ValueError('scene already has an active/cooperative AIR lease; do not overwrite') from e
    with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(payload,f,indent=2)
    return {'status':'LEASE_ACQUIRED','holder':holder,'token':token,'lease_path':str(path),
            'note':'Keep token secret. This cooperative lease does not lock external Blender GUI edits.'}


def require_lease(root,holder,token):
    path=_lease_path(root)
    ensure(path.is_file() and not path.is_symlink(),'no active safe scene lease')
    payload=json.loads(path.read_text(encoding='utf-8'))
    ensure(payload.get('holder')==holder,'lease holder mismatch')
    ensure(secrets.compare_digest(str(payload.get('token_sha256','')),
                                  hashlib.sha256(str(token).encode()).hexdigest()),'invalid lease token')
    return {'status':'LEASE_VERIFIED','holder':holder}


def release_lease(root,holder,token):
    result=require_lease(root,holder,token)
    path=_lease_path(root)
    path.unlink()
    return {'status':'LEASE_RELEASED','holder':holder}


def record_benchmark(ledger,record,evidence_path,root):
    """Evidence path is hashed, but an independent review claim is not authenticated."""
    ledger=validate_ledger(ledger)
    rec=dict(record)
    root=Path(root).resolve(strict=True)
    if rec.get('result') in ('PASS','FAIL'):
        ensure(evidence_path is not None,'PASS/FAIL quality record requires evidence_path')
        fp=Path(evidence_path).resolve(strict=True)
        ensure(fp.is_file() and fp.is_relative_to(root) and fp.stat().st_size>0,
               'evidence must be existing file inside project root')
        rec['evidence_sha256']=hashlib.sha256(fp.read_bytes()).hexdigest()
        ensure(rec.get('review_status')=='INDEPENDENT_REVIEW' and rec.get('reviewer'),
               'successful benchmark needs named independent reviewer')
    else:
        rec['evidence_sha256']=None
    doc={'schema_version':SCHEMA,'records':[ *ledger['records'],rec]}
    validate_ledger(doc)
    return doc
