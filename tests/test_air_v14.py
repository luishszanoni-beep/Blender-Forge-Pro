"""AIR V1.4 offline tests. NO agent hosting, API calls or Blender artistic QA."""
from __future__ import annotations
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from air_core import (validate_registry,validate_tasks,validate_ledger,route_task,
                       make_plan,build_schedule,tier_risk,escalation,estimate,
                       acquire_lease,require_lease,release_lease,record_benchmark,
                       observed_stats,CLASSES,EFFORTS)


def fixture(path):
    return json.loads((ROOT/'examples'/'air'/path).read_text('utf-8'))


class RegistryTests(unittest.TestCase):
    def setUp(self):self.doc=fixture('registry_simulation.json')
    def check_invalid(self):
        with self.assertRaises(ValueError):validate_registry(self.doc)
    def test_good_registry(self):self.assertEqual(validate_registry(self.doc)['models'],4)
    def test_five_classes(self):self.assertEqual(len(CLASSES),5)
    def test_four_efforts(self):self.assertEqual(len(EFFORTS),4)
    def test_empty_production_ok(self):self.assertEqual(validate_registry(fixture('registry_production_template.json'))['models'],0)
    def test_bad_schema(self):self.doc['schema_version']='1.3';self.check_invalid()
    def test_bad_catalog_kind(self):self.doc['catalog_kind']='unauthorized';self.check_invalid()
    def test_fake_prod_model_refused(self):self.doc['catalog_kind']='production';self.check_invalid()
    def test_duplicate_id(self):self.doc['models'].append(copy.deepcopy(self.doc['models'][0]));self.check_invalid()
    def test_missing_model_effort(self):self.doc['models'][0]['efforts']=[];self.check_invalid()
    def test_unknown_effort(self):self.doc['models'][0]['efforts']=['low','ultra'];self.check_invalid()
    def test_repeated_effort(self):self.doc['models'][0]['efforts']=['low','low'];self.check_invalid()
    def test_unknown_capability(self):self.doc['models'][0]['domain_classes']['magic']='extra_basic';self.check_invalid()
    def test_invalid_domain_class(self):self.doc['models'][0]['domain_classes']['export']='Godlike';self.check_invalid()
    def test_unknown_model_key_rejected(self):self.doc['models'][0]['python']='exec';self.check_invalid()
    def test_negative_model_cost(self):self.doc['models'][0]['usd_per_1m_input']=-1;self.check_invalid()
    def test_nan_cost(self):self.doc['models'][0]['usd_per_1m_input']=float('nan');self.check_invalid()
    def test_boolean_cost(self):self.doc['models'][0]['usd_per_1m_input']=True;self.check_invalid()
    def test_invalid_token_limit(self):self.doc['models'][0]['max_context_tokens']=5;self.check_invalid()
    def test_disabled_model_allowed(self):self.doc['models'][0]['enabled']=False;self.assertEqual(validate_registry(self.doc)['enabled'],3)
    def test_fake_mode_only_fixture(self):self.doc['catalog_kind']='production';self.doc['models']=[];self.check_invalid()
    def test_parallel_limit(self):self.doc['policy']['max_parallel_readers']=300;self.check_invalid()
    def test_unsupported_modality(self):self.doc['models'][0]['modalities'].append('filesystem');self.check_invalid()
    def test_invalid_runtime(self):self.doc['runtime']['verified_on_host']='yes';self.check_invalid()
    def test_provider_specific_effort_mult(self):
        self.doc['models'][0]['effort_multiplier']={'low':1.3}
        self.assertEqual(validate_registry(self.doc)['status'],'VALIDATED_CATALOG_NOT_PROVIDER_VERIFIED')


class TaskTests(unittest.TestCase):
    def setUp(self):self.doc=fixture('task_plan_chair.json')
    def check_invalid(self):
        with self.assertRaises(ValueError):validate_tasks(self.doc)
    def test_good_tasks(self):self.assertEqual(validate_tasks(self.doc)['tasks'],7)
    def test_bad_skill(self):self.doc['tasks'][0]['skill']='new-ninth-skill';self.check_invalid()
    def test_bad_complexity(self):self.doc['tasks'][0]['complexity']=0;self.check_invalid()
    def test_floating_complexity(self):self.doc['tasks'][0]['complexity']=3.5;self.check_invalid()
    def test_bool_complexity(self):self.doc['tasks'][0]['complexity']=True;self.check_invalid()
    def test_missing_id(self):self.doc['tasks'][0].pop('id');self.check_invalid()
    def test_duplicate_task(self):self.doc['tasks'].append(copy.deepcopy(self.doc['tasks'][0]));self.check_invalid()
    def test_dependency_missing(self):self.doc['tasks'][0]['depends_on']=['oops'];self.check_invalid()
    def test_dependency_cycle(self):self.doc['tasks'][0]['depends_on']=['export_hash'];self.check_invalid()
    def test_dependency_self(self):self.doc['tasks'][0]['depends_on']=['file_inventory'];self.check_invalid()
    def test_write_requires_blender(self):self.doc['tasks'][3]['requires_tools']=['none'];self.check_invalid()
    def test_deduplicates(self):self.doc['tasks'][1]['depends_on']=['file_inventory','file_inventory'];self.check_invalid()
    def test_max_tokens_limit(self):self.doc['tasks'][0]['tokens_in']=-2;self.check_invalid()
    def test_unknown_field(self):self.doc['tasks'][0]['run_python']='bad';self.check_invalid()
    def test_decomp_priority_not_skill_lock(self):
        t1=copy.deepcopy(self.doc['tasks'][1]);t2=copy.deepcopy(t1)
        t2.update(complexity=1,uncertainty=1,impact=1,failure_cost=1,quality='standard')
        self.assertNotEqual(tier_risk(t1)['required_class'],tier_risk(t2)['required_class'])
        self.assertEqual(t1['skill'],t2['skill'])
    def test_protected_min_effort(self):
        self.doc['tasks'][1]['explicit_min_effort']='extra_high'
        self.assertEqual(validate_tasks(self.doc)['tasks'],7)
    def test_invalid_explicit_min_class(self):self.doc['tasks'][1]['explicit_min_class']='godlike';self.check_invalid()
    def test_quality_enum(self):self.doc['tasks'][1]['quality']='100%';self.check_invalid()
    def test_dependency_waves_no_writes_with_readers(self):
        waves=build_schedule(self.doc['tasks'],3)
        lookup={t['id']:t for t in self.doc['tasks']}
        for w in waves:
            if any(lookup[i]['writes_scene'] for i in w['task_ids']):
                self.assertEqual(len(w['task_ids']),1)
    def test_cycle_detect_works_independently(self):
        with self.assertRaises(ValueError):build_schedule([{'id':'a','depends_on':['b'],'writes_scene':False},{'id':'b','depends_on':['a'],'writes_scene':False}])


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.registry=fixture('registry_simulation.json')
        self.tasks=fixture('task_plan_chair.json')
        self.mid=self.tasks['tasks'][1]
    def test_sample_plan(self):
        plan=make_plan(self.tasks,self.registry)
        self.assertEqual(plan['status'],'PLANNED_NOT_EXECUTED')
        self.assertIsNone(plan['execution_proof'])
        self.assertEqual(len(plan['routes']),7)
        self.assertEqual(plan['routes'][0]['status'],'DETERMINISTIC_NO_LLM')
    def test_vision_prefers_capable_model(self):
        routed=route_task(self.mid,self.registry)
        self.assertEqual(routed['assignment']['model_id'],'fixture.max')
    def test_easy_export_is_economical(self):
        routed=route_task(self.tasks['tasks'][2],self.registry)
        self.assertEqual(routed['assignment']['model_id'],'fixture.tiny')
    def test_critical_task_extra_high(self):
        routed=route_task(self.tasks['tasks'][5],self.registry)
        self.assertEqual(routed['assignment']['effort'],'extra_high')
    def test_no_models_blocks(self):
        reg=fixture('registry_production_template.json')
        self.assertEqual(route_task(self.mid,reg)['status'],'UNASSIGNED_QUALITY_OR_CAPABILITY_CONSTRAINT')
    def test_empty_production_plan_blocked(self):
        reg=fixture('registry_production_template.json')
        self.assertEqual(make_plan(self.tasks,reg)['status'],'BLOCKED_MISSING_CAPABILITY')
    def test_no_tool_blocks(self):
        self.mid['requires_tools']=['blender']
        reg=copy.deepcopy(self.registry)
        for m in reg['models']:m['tools']=[x for x in m['tools'] if x!='blender']
        self.assertIsNone(route_task(self.mid,reg)['assignment'])
    def test_no_image_support_blocks(self):
        for m in self.registry['models']:m['modalities']=['text']
        self.assertIsNone(route_task(self.mid,self.registry)['assignment'])
    def test_disabled_max_cannot_assume_quality(self):
        self.registry['models'][-1]['enabled']=False
        self.assertIsNone(route_task(self.mid,self.registry)['assignment'])
    def test_effort_explicit_min_requires_matching_support(self):
        self.mid['explicit_min_effort']='extra_high'
        for m in self.registry['models']:m['efforts']=[x for x in m['efforts'] if x!='extra_high']
        self.assertIsNone(route_task(self.mid,self.registry)['assignment'])
    def test_strict_budget_does_not_downgrade_class(self):
        self.mid['max_cost_usd']=0.001
        self.assertIsNone(route_task(self.mid,self.registry)['assignment'])
    def test_time_budget_does_not_downgrade(self):
        self.mid['max_latency_s']=0.1
        self.assertIsNone(route_task(self.mid,self.registry)['assignment'])
    def test_context_limit(self):
        self.mid['tokens_in']=200000
        self.assertIsNone(route_task(self.mid,self.registry)['assignment'])
    def test_model_selection_ignores_preferred_when_inadequate(self):
        self.mid['preferred_model_id']='fixture.tiny'
        self.assertEqual(route_task(self.mid,self.registry)['assignment']['model_id'],'fixture.max')
    def test_extra_high_supported_not_assumed(self):
        self.registry['models'][-1]['efforts']=['high']
        task=copy.deepcopy(self.tasks['tasks'][5]);task.pop('explicit_min_effort',None)
        result=route_task(task,self.registry)
        self.assertTrue(result['assignment']['effort_below_suggestion'])
        self.assertEqual(result['assignment']['effort'],'high')
    def test_no_cheaper_low_when_high_supported(self):
        t=copy.deepcopy(self.mid)
        t.update(complexity=3,uncertainty=3,impact=3,failure_cost=3,quality='standard')
        a=route_task(t,self.registry)['assignment']
        self.assertEqual(a['effort'],'high')
    def test_realtime_registry_never_spawns(self):
        reg=copy.deepcopy(self.registry)
        reg['catalog_kind']='production';reg['models']=[];reg['runtime']['mode']='external_adapter'
        reg['runtime']['verified_on_host']=True;reg['runtime']['supports_subagents']=True
        reg['runtime']['supports_model_override']=True;reg['runtime']['supports_effort_override']=True
        self.assertIsNone(route_task(self.mid,reg)['assignment'])
    def test_disabled_profile_not_selected(self):
        self.registry['models'][0]['enabled']=False
        assignment=route_task(self.tasks['tasks'][2],self.registry)['assignment']
        self.assertNotEqual(assignment['model_id'],'fixture.tiny')
    def test_excluded_model_not_selected(self):
        self.assertIsNone(route_task(self.mid,self.registry,exclude_model_ids=['fixture.max'])['assignment'])
    def test_quality_min_class_explicit(self):
        t=copy.deepcopy(self.tasks['tasks'][2]);t['explicit_min_class']='extra_advanced'
        self.assertEqual(route_task(t,self.registry)['assignment']['model_id'],'fixture.max')
    def test_model_cost_estimate_is_only_estimate(self):
        a=estimate(self.registry['models'][-1],self.mid,'high')
        self.assertGreater(a['estimated_cost_usd'],0)
        self.assertEqual(a['estimate_status'],'UNVERIFIED_PROVIDER_ESTIMATE')
    def test_router_cannot_certify_art(self):
        a=route_task(self.mid,self.registry)
        self.assertTrue(a['assignment']['requires_independent_qa'])
    def test_skill_does_not_hardlock(self):
        easy=copy.deepcopy(self.mid)
        easy.update(complexity=1,uncertainty=1,impact=1,failure_cost=1,quality='standard')
        self.assertNotEqual(route_task(easy,self.registry)['assignment']['model_id'],route_task(self.mid,self.registry)['assignment']['model_id'])


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.registry=fixture('registry_simulation.json')
        self.task=fixture('task_plan_chair.json')['tasks'][1]
        self.one={'task_id':'a','model_id':'fixture.max','domain':'vision','effort':'high',
                  'result':'PASS','elapsed_s':5.2,'actual_cost_usd':0.01,
                  'evidence_sha256':'a'*64,'reviewer':'qa-operator-1','review_status':'INDEPENDENT_REVIEW',
                  'measured_at':'2026-10-16T14:00:00Z'}
    def test_empty_ledger(self):self.assertEqual(len(validate_ledger({'schema_version':'1.4','records':[]})['records']),0)
    def test_reject_unreviewed_pass(self):
        d=copy.deepcopy(self.one);d['review_status']='SELF_REPORTED'
        with self.assertRaises(ValueError):validate_ledger({'schema_version':'1.4','records':[d]})
    def test_reject_pass_without_evidence(self):
        d=copy.deepcopy(self.one);d['evidence_sha256']=None
        with self.assertRaises(ValueError):validate_ledger({'schema_version':'1.4','records':[d]})
    def test_reject_fail_without_evidence(self):
        d=copy.deepcopy(self.one);d['result']='FAIL';d['evidence_sha256']=None
        with self.assertRaises(ValueError):validate_ledger({'schema_version':'1.4','records':[d]})
    def test_reject_unknown_status(self):
        d=copy.deepcopy(self.one);d['result']='PERFECT'
        with self.assertRaises(ValueError):validate_ledger({'schema_version':'1.4','records':[d]})
    def test_reject_nan_actual_cost(self):
        d=copy.deepcopy(self.one);d['actual_cost_usd']=float('nan')
        with self.assertRaises(ValueError):validate_ledger({'schema_version':'1.4','records':[d]})
    def test_insufficient_sample_does_not_recalibrate(self):
        doc={'schema_version':'1.4','records':[self.one]}
        self.assertFalse(observed_stats(validate_ledger(doc),'fixture.max','vision','high',5)['calibrated'])
    def test_calibrated_bad_model_filtered(self):
        records=[]
        for i in range(6):
            a=copy.deepcopy(self.one);a['task_id']='a'+str(i);a['result']='FAIL' if i<5 else 'PASS'
            records.append(a)
        doc={'schema_version':'1.4','records':records}
        self.assertTrue(observed_stats(validate_ledger(doc),'fixture.max','vision','high',5)['calibrated'])
        result=route_task(self.task,self.registry,doc)
        self.assertNotEqual(result['assignment']['effort'],'high')
        self.assertFalse(result['assignment']['benchmark']['calibrated'])
    def test_record_with_actual_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fp=root/'evidence.txt';fp.write_text('real evidence text')
            one=copy.deepcopy(self.one);one.pop('evidence_sha256')
            doc=record_benchmark({'schema_version':'1.4','records':[]},one,fp,root)
            self.assertEqual(doc['records'][0]['evidence_sha256'],hashlib.sha256(fp.read_bytes()).hexdigest())
    def test_missing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            one=copy.deepcopy(self.one)
            with self.assertRaises(ValueError):record_benchmark(None,one,None,tmp)
    def test_evidence_outside_project(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            evidence=Path(b)/'outside.txt';evidence.write_text('nope')
            with self.assertRaises(ValueError):record_benchmark(None,self.one,evidence,a)
    def test_evidence_empty(self):
        with tempfile.TemporaryDirectory() as root:
            evidence=Path(root)/'empty.txt';evidence.write_text('')
            with self.assertRaises(ValueError):record_benchmark(None,self.one,evidence,root)


class EscalationTests(unittest.TestCase):
    def setUp(self):
        self.registry=fixture('registry_simulation.json')
        self.task=fixture('task_plan_chair.json')['tasks'][2]
        self.old=route_task(self.task,self.registry)
    def test_tool_failure_no_model_escalation(self):
        self.assertEqual(escalation(self.task,self.old,'TOOL_FAILURE',1,self.registry)['status'],'REPAIR_TOOL_ENVIRONMENT')
    def test_reference_missing_no_model_escalation(self):
        self.assertEqual(escalation(self.task,self.old,'REFERENCE_GAP',1,self.registry)['status'],'NEEDS_REFERENCE_EVIDENCE')
    def test_quality_escalates_not_downgrades(self):
        res=escalation(self.task,self.old,'QUALITY_FAIL',1,self.registry)
        self.assertIn(res['status'],('ESCALATED_CLASS','ESCALATED_EFFORT','ROUTED_TO_PEER_AFTER_FAILURE','NEEDS_MANUAL_REVIEW'))
        if 'new_route' in res:
            self.assertGreaterEqual(CLASSES.index(res['new_route']['assignment']['domain_class']),
                                    CLASSES.index(self.old['assignment']['domain_class']))
    def test_budget_doesnt_escalate(self):
        self.assertEqual(escalation(self.task,self.old,'BUDGET_FAILURE',1,self.registry)['status'],'STOP_BUDGET')
    def test_scope_rollback(self):
        self.assertEqual(escalation(self.task,self.old,'SCOPE_VIOLATION',1,self.registry)['status'],'ROLLBACK_SCENE')
    def test_max_attempts_enforced(self):
        self.assertEqual(escalation(self.task,self.old,'QUALITY_FAIL',2,self.registry)['status'],'STOP_MAX_ATTEMPTS')
    def test_no_assignment(self):
        self.assertEqual(escalation(self.task,{'assignment':None},'QUALITY_FAIL',1,self.registry)['status'],'NEEDS_MANUAL_ROUTING')
    def test_bad_failure_cause(self):
        with self.assertRaises(ValueError):escalation(self.task,self.old,'MAGIC',1,self.registry)


class LeaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_lock_acquire_release(self):
        r=acquire_lease(self.root,'modeler')
        self.assertEqual(require_lease(self.root,'modeler',r['token'])['status'],'LEASE_VERIFIED')
        self.assertEqual(release_lease(self.root,'modeler',r['token'])['status'],'LEASE_RELEASED')
    def test_second_lease_denied(self):
        acquire_lease(self.root,'agent1')
        with self.assertRaisesRegex(ValueError,'already'):acquire_lease(self.root,'agent2')
    def test_wrong_owner(self):
        a=acquire_lease(self.root,'agent1')
        with self.assertRaisesRegex(ValueError,'holder'):require_lease(self.root,'agent2',a['token'])
    def test_wrong_token(self):
        acquire_lease(self.root,'agent1')
        with self.assertRaisesRegex(ValueError,'token'):release_lease(self.root,'agent1','forged')
    def test_invalid_holder(self):
        with self.assertRaises(ValueError):acquire_lease(self.root,'../../bad')
    def test_absent_lease(self):
        with self.assertRaises(ValueError):require_lease(self.root,'x','abc')
    def test_symlinked_forge_rejected(self):
        if os.name=='nt':self.skipTest('symlink creation may be disabled on Windows')
        other=self.root/'other';other.mkdir()
        (self.root/'.forge').symlink_to(other,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):acquire_lease(self.root,'agent1')


class CLITests(unittest.TestCase):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,str(ROOT/'scripts'/'air.py'),*map(str,args)],capture_output=True,text=True,timeout=15)
    def test_cli_validate_registry(self):
        p=self.run_cli('validate-registry',ROOT/'examples'/'air'/'registry_simulation.json')
        self.assertEqual(p.returncode,0,p.stdout)
    def test_cli_route_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as t:
            dest=Path(t)/'plan.json'
            p=self.run_cli('route',ROOT/'examples'/'air'/'task_plan_chair.json','--registry',
                           ROOT/'examples'/'air'/'registry_simulation.json','--out',dest)
            self.assertEqual(p.returncode,0,p.stdout)
            self.assertEqual(json.loads(dest.read_text())['status'],'PLANNED_NOT_EXECUTED')
    def test_cli_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            dest=Path(t)/'plan.json';dest.write_text('x')
            p=self.run_cli('route',ROOT/'examples'/'air'/'task_plan_chair.json','--registry',
                           ROOT/'examples'/'air'/'registry_simulation.json','--out',dest)
            self.assertEqual(p.returncode,3)
            self.assertEqual(dest.read_text(),'x')
    def test_bridge_managed_requires_lease(self):
        with tempfile.TemporaryDirectory() as t:
            p=subprocess.run([sys.executable,str(ROOT/'scripts'/'blender_bridge.py'),'run',
                '--blender',sys.executable,'--task','diagnostic-sample',
                '--out',str(Path(t)/'output')],capture_output=True,text=True,timeout=10,
                env={**os.environ,'FORGE_AIR_MANAGED':'1'})
            self.assertEqual(p.returncode,3,p.stdout)
            self.assertIn('requires project-root/holder/token lease',p.stdout)
    def test_bridge_managed_refuses_invalid_lease(self):
        with tempfile.TemporaryDirectory() as t:
            p=subprocess.run([sys.executable,str(ROOT/'scripts'/'blender_bridge.py'),'run',
                '--blender',sys.executable,'--task','diagnostic-sample',
                '--out',str(Path(t)/'output'),'--air-project-root',str(t),
                '--air-holder','x','--air-token','wrong'],capture_output=True,text=True,timeout=10)
            self.assertEqual(p.returncode,3,p.stdout)
    def test_plugin_skills_eight_not_nine(self):
        self.assertEqual(len(list((ROOT/'skills').glob('*/SKILL.md'))),8)
    def test_docs_all_skills_air(self):
        for skill in (ROOT/'skills').glob('*/SKILL.md'):
            self.assertIn('Adaptive Intelligence Router',skill.read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()

# Supplemental regression tests stay here so core v1.3 tests are unchanged.
class ExtraRoutingBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.catalog=fixture('registry_simulation.json')
        self.tasks=fixture('task_plan_chair.json')
    def test_project_cost_cannot_silently_degrade(self):
        self.catalog['policy']['max_project_estimated_cost_usd']=0.01
        p=make_plan(self.tasks,self.catalog)
        self.assertEqual(p['status'],'BLOCKED_PROJECT_BUDGET')
        self.assertEqual(p['routes'][5]['assignment']['effort'],'extra_high')
    def test_project_time_budget(self):
        self.catalog['policy']['max_project_estimated_seconds']=1.0
        p=make_plan(self.tasks,self.catalog)
        self.assertEqual(p['status'],'BLOCKED_PROJECT_BUDGET')
        self.assertTrue(p['estimated_project']['excludes_blender_and_deterministic_execution'])
    def test_production_budget_field_validation(self):
        self.catalog['policy']['max_project_estimated_cost_usd']=float('nan')
        with self.assertRaises(ValueError):validate_registry(self.catalog)
    def test_routing_has_no_qa_certificate(self):
        p=make_plan(self.tasks,self.catalog)
        self.assertIsNone(p['qa_approval'])
        self.assertIsNone(p['scene_edit_proof'])
    def test_alias_must_be_declared(self):
        self.catalog['models'][-1]['effort_wire_values']={'extra_high':'xhigh'}
        a=route_task(self.tasks['tasks'][5],self.catalog)['assignment']
        self.assertEqual(a['provider_effort_value'],'xhigh')
    def test_alias_cannot_claim_unsupported_effort(self):
        self.catalog['models'][0]['effort_wire_values']={'extra_high':'xhigh'}
        with self.assertRaises(ValueError):validate_registry(self.catalog)
    def test_provider_qualified_model_id(self):
        self.catalog['models'][0]['id']='local/mini-code'
        self.assertEqual(validate_registry(self.catalog)['models'],4)
    def test_parent_path_in_model_id_refused(self):
        self.catalog['models'][0]['id']='local/../bad'
        with self.assertRaises(ValueError):validate_registry(self.catalog)
    def test_preference_never_bypasses_qa(self):
        t=copy.deepcopy(self.tasks['tasks'][1]);t['preferred_model_id']='fixture.tiny'
        a=route_task(t,self.catalog)['assignment']
        self.assertEqual(a['model_id'],'fixture.max')
        self.assertFalse(a['model_preference_applied'])
    def test_plan_is_not_dispatch(self):
        for r in make_plan(self.tasks,self.catalog)['routes']:
            self.assertNotEqual(r['status'],'DISPATCHED')
    def test_evidence_ledger_does_not_count_tool_failure_as_quality_fail(self):
        r={'task_id':'t','model_id':'fixture.max','domain':'vision','effort':'high',
           'result':'TOOL_FAILURE','elapsed_s':1,'actual_cost_usd':.1,
           'evidence_sha256':None,'reviewer':'','review_status':'NONE',
           'measured_at':'2026-10-16T15:00:00Z'}
        led=validate_ledger({'schema_version':'1.4','records':[r]})
        self.assertFalse(observed_stats(led,'fixture.max','vision','high',3)['calibrated'])
    def test_doctor_has_no_fabricated_runtime_probe(self):
        cp=subprocess.run([sys.executable,str(ROOT/'scripts'/'air.py'),'doctor'],capture_output=True,text=True)
        self.assertEqual(cp.returncode,0)
        data=json.loads(cp.stdout)
        self.assertFalse(data['subagent_spawn_capability_observed'])
        self.assertFalse(data['provider_model_inventory_observed'])
    def test_lease_does_not_store_plain_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=acquire_lease(tmp,'scene-operator')
            self.assertNotIn(r['token'],Path(r['lease_path']).read_text())
            release_lease(tmp,'scene-operator',r['token'])
    def test_bridge_lease_does_not_allow_outside_project(self):
        with tempfile.TemporaryDirectory() as base:
            project=Path(base)/'proj';project.mkdir()
            foreign=Path(base)/'foreign';foreign.mkdir()
            r=acquire_lease(project,'writer')
            proc=subprocess.run([sys.executable,str(ROOT/'scripts'/'blender_bridge.py'),'run',
                '--blender',sys.executable,'--task','diagnostic-sample',
                '--out',str(foreign),'--air-project-root',str(project),
                '--air-holder','writer','--air-token',r['token']],capture_output=True,text=True,timeout=10,
                env={**os.environ,'FORGE_AIR_MANAGED':'1'})
            self.assertEqual(proc.returncode,3,proc.stdout)
            self.assertIn('inside project root',proc.stdout)
            release_lease(project,'writer',r['token'])

class TierCoverageTests(unittest.TestCase):
    def setUp(self):
        self.registry=fixture('registry_simulation.json')
        seed=copy.deepcopy(self.registry['models'][0])
        self.registry['models']=[]
        for i,tier in enumerate(CLASSES):
            m=copy.deepcopy(seed)
            m['id']='fixture.test_'+tier
            m['domain_classes']={'general':tier}
            m['efforts']=['low','medium','high','extra_high']
            m['usd_per_1m_input']=(i+1)*.5
            m['usd_per_1m_output']=(i+1)*1.5
            self.registry['models'].append(m)
        self.task=fixture('task_plan_chair.json')['tasks'][2]
        self.task.update(domain='general',quality='standard',requires_modalities=['text'],requires_tools=['none'])
    def test_five_classes_selectable_per_task(self):
        for complexity,tier in [(1,'extra_basic'),(2,'basic'),(3,'medium'),(4,'advanced'),(5,'extra_advanced')]:
            with self.subTest(complexity=complexity):
                for metric in ('complexity','uncertainty','impact','failure_cost'):
                    self.task[metric]=complexity
                assignment=route_task(self.task,self.registry)['assignment']
                self.assertEqual(assignment['domain_class'],tier)
    def test_four_efforts_selectable_per_task(self):
        for complexity,effort in [(1,'low'),(2,'medium'),(3,'high'),(5,'extra_high')]:
            with self.subTest(complexity=complexity):
                for metric in ('complexity','uncertainty','impact','failure_cost'):
                    self.task[metric]=complexity
                assignment=route_task(self.task,self.registry)['assignment']
                self.assertEqual(assignment['effort'],effort)
