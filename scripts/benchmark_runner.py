#!/usr/bin/env python3
"""Truthful production benchmark evidence audit; does NOT manufacture quality scores."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from forge_core import inside
from forge_v13_core import num
from check_glb import analyze as check_glb
from image_integrity import inspect as inspect_image

CASES={'TECH-CHAIR','HARD-SURFACE','STYLIZED-RIG','SCULPT-RELIEF'}
REQUIRED_METRICS={'dimension_error_mm','missing_required_parts','triangle_count','correction_cycles','minutes_elapsed'}


def validate_run(run: dict, root: Path) -> dict:
    errors=[]
    if run.get('schema_version')!='1.3':errors.append('schema_version must be 1.3')
    if run.get('case_id') not in CASES:errors.append('unknown case_id')
    if run.get('state') not in ('NOT_EXECUTED','EXECUTED_PENDING_VISUAL','VISUALLY_REVIEWED'):
        errors.append('invalid benchmark state')
    if run.get('state')=='NOT_EXECUTED':
        return {'status':'NOT_EXECUTED' if not errors else 'FAIL','errors':errors,'case_id':run.get('case_id'),
                'note':'No Blender execution or artistic quality evidence was provided.'}
    if run.get('engine')!='Blender' or not isinstance(run.get('blender_version'),str) or not run['blender_version'].strip():
        errors.append('real Blender run requires engine/version provenance')
    if not isinstance(run.get('source_reference_ids'),list) or not run['source_reference_ids']:
        errors.append('references missing')
    if not isinstance(run.get('operator_log'),list) or not run['operator_log']:
        errors.append('operation history missing')
    metrics=run.get('metrics',{})
    if not isinstance(metrics,dict):metrics={};errors.append('metrics must be object')
    for key in REQUIRED_METRICS:
        try:num(metrics[key],key,0,100000000)
        except (KeyError,ValueError,TypeError):errors.append('required metric missing or invalid: '+key)
    artifacts=run.get('artifacts',[])
    if not isinstance(artifacts,list) or not artifacts:
        artifacts=[];errors.append('artifacts missing')
    valid_formats=[]
    for a in artifacts:
        try:
            fp=inside(root,a['path'],must_exist=True)
            if not fp.stat().st_size:raise ValueError('empty file')
            digest=hashlib.sha256()
            with fp.open('rb') as fh:
                for chunk in iter(lambda:fh.read(1048576),b''):
                    digest.update(chunk)
            if a.get('sha256')!=digest.hexdigest():raise ValueError('sha256 mismatch')
            suffix=fp.suffix.lower()
            if suffix=='.glb' and check_glb(fp)['status']!='PASS':
                raise ValueError('invalid GLB structural contents')
            if suffix=='.blend':
                with fp.open('rb') as fh:
                    if fh.read(7)!=b'BLENDER':
                        raise ValueError('not a valid Blender file signature')
            if suffix in ('.png','.jpg','.jpeg','.webp'):
                report=inspect_image(fp)
                if report['status']!='PASS':
                    raise ValueError('invalid/unverified benchmark image: '+str(report.get('reason')))
            if suffix not in ('.blend','.glb','.fbx','.png','.jpg','.jpeg','.webp','.json'):
                raise ValueError('unsupported benchmark artifact extension')
            valid_formats.append(suffix)
        except (KeyError,ValueError,TypeError,OSError) as e:errors.append('artifact invalid: '+str(e))
    if not any(x in valid_formats for x in ('.blend','.glb')):
        errors.append('at least one 3D artifact (BLEND or structurally valid GLB) required')
    if run['state']=='VISUALLY_REVIEWED':
        if not any(x in valid_formats for x in ('.png','.jpg','.jpeg','.webp')):
            errors.append('visual review requires an actual view image artifact')
        reviewers=run.get('reviewers',[])
        if not isinstance(reviewers,list) or len(reviewers)<2 or len(set(reviewers))<2:
            errors.append('two distinct reviewers required for benchmark artistic scoring')
        scores=run.get('artistic_scores',[])
        if not isinstance(scores,list) or len(scores)<2:errors.append('at least two independent artistic scores required')
        else:
            for score in scores:
                try:
                    if score.get('reviewer') not in reviewers:raise ValueError('reviewer mismatch')
                    num(score.get('reference_fidelity_0_100'),'score',0,100)
                except (ValueError,TypeError,AttributeError) as e:errors.append('invalid artistic score: '+str(e))
    return {'status':'FAIL' if errors else 'READY_FOR_COMPARATIVE_ANALYSIS' if run['state']=='VISUALLY_REVIEWED' else 'EXECUTED_PENDING_VISUAL',
            'case_id':run.get('case_id'),'errors':errors,
            'note':'A validated measurement record is not proof the plugin outperforms a baseline.'}


def compare_runs(baseline: dict, candidate: dict, root: Path) -> dict:
    a=validate_run(baseline,root);b=validate_run(candidate,root)
    if a['status']!='READY_FOR_COMPARATIVE_ANALYSIS' or b['status']!='READY_FOR_COMPARATIVE_ANALYSIS':
        return {'status':'INDETERMINATE','reason':'both records require validated real Blender runs and two reviewers','baseline':a,'candidate':b}
    if baseline['case_id']!=candidate['case_id'] or baseline.get('source_reference_ids')!=candidate.get('source_reference_ids'):
        return {'status':'INDETERMINATE','reason':'reference benchmark inputs differ'}
    changes={}
    for key in REQUIRED_METRICS:
        changes[key]=round(candidate['metrics'][key]-baseline['metrics'][key],6)
    return {'status':'COMPARISON_MEASURED_NOT_CAUSAL','deltas_candidate_minus_baseline':changes,
            'note':'Differences are descriptive; controlled repeat trials required before claiming causal performance gains.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('record');p.add_argument('--root',required=True);p.add_argument('--baseline');p.add_argument('--out');a=p.parse_args()
    try:
        candidate=json.loads(Path(a.record).read_text(encoding='utf-8'))
        r=compare_runs(json.loads(Path(a.baseline).read_text(encoding='utf-8')),candidate,Path(a.root)) if a.baseline else validate_run(candidate,Path(a.root))
    except (KeyError,ValueError,TypeError,OSError,json.JSONDecodeError) as e:r={'status':'ERROR','error':str(e)}
    s=json.dumps(r,indent=2,ensure_ascii=False)+'\n';print(s,end='')
    if a.out:Path(a.out).write_text(s,encoding='utf-8')
    return 0 if r['status'] in ('READY_FOR_COMPARATIVE_ANALYSIS','EXECUTED_PENDING_VISUAL','COMPARISON_MEASURED_NOT_CAUSAL') else 2
if __name__=='__main__':raise SystemExit(main())
