import json,tempfile,unittest
from pathlib import Path
from freeze_core_v1_workflow_gate import freeze, WORKFLOWS

class FreezeCoreWorkflowGateTest(unittest.TestCase):
    def recipe(self,workflow):
        if workflow=='content-quality-gate':
            return {'questions':{'quality':{'type':'score','instructions':'Rate.','criteria':['bad','ok']}},'declarative_policy':{'type':'score','questionId':'quality','thresholds':[{'atLeast':1,'branch':'publish'}],'belowBranch':'reject'}}
        if workflow=='sales-lead-fit':
            return {'questions':{'qualified':{'type':'binary','instructions':'Fit?'}},'declarative_policy':{'type':'binary','questionId':'qualified','trueBranch':'yes','falseBranch':'no','uncertainBranch':'review'}}
        return {'questions':{'q':{'type':'choice','instructions':'Choose.','criteria':{'a':'A','b':'B'}}},'declarative_policy':{'type':'choice','questionId':'q','branches':{'a':'a','b':'b'},'uncertainBranch':'review'}}
    def test_freezes_five_workflows_before_cases(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); contract=root/'contract.md'; contract.write_text('v1')
            for w in WORKFLOWS:
                p=root/'examples'/'use-cases'/w/'custom-reflex.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(self.recipe(w)))
            d=freeze(root,'abc',contract)
            self.assertEqual(d['status'],'frozen-before-case-pack-and-engine-inference')
            self.assertEqual(len(d['selected_workflows']),5)
            self.assertEqual(d['case_pack_rules']['minimum_total_cases'],150)
            self.assertEqual(d['case_pack_rules']['languages'],['en','es'])
            self.assertEqual(d['case_pack_rules']['minimum_cases_per_language_per_workflow'],15)
            self.assertEqual(d['evaluation']['extra_model_calls_for_core'],0)
            self.assertTrue(d['predeclared_gate']['core_exact_branch_delta_must_be_positive'])
    def test_branch_sets_are_frozen_from_policy(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); contract=root/'contract.md'; contract.write_text('v1')
            for w in WORKFLOWS:
                p=root/'examples'/'use-cases'/w/'custom-reflex.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(self.recipe(w)))
            d=freeze(root,'abc',contract); by={x['id']:x for x in d['selected_workflows']}
            self.assertEqual(by['sales-lead-fit']['operational_branches'],['no','review','yes'])
            self.assertEqual(by['content-quality-gate']['operational_branches'],['publish','reject'])

if __name__=='__main__': unittest.main()


class FreezeReplicationGateTest(unittest.TestCase):
    def test_can_freeze_different_workflows_with_transport_policy(self):
        from freeze_core_v1_workflow_gate import freeze
        workflows=('one','two','three','four','five')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); contract=root/'contract.md'; contract.write_text('v1')
            for w in workflows:
                p=root/'examples'/'use-cases'/w/'custom-reflex.json'; p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(json.dumps({'questions':{'q':{'type':'choice','instructions':'Choose.','criteria':{'a':'A','b':'B'}}},'declarative_policy':{'type':'choice','questionId':'q','branches':{'a':'a','b':'b'},'uncertainBranch':'review'}}))
            d=freeze(root,'abc',contract,workflows=workflows,transport_retries=2,transport_retry_backoff_ms=2000.0,gate_identity='core-v1-workflow-gate-v2')
            self.assertEqual([x['id'] for x in d['selected_workflows']],list(workflows))
            self.assertEqual(d['gate_identity'],'core-v1-workflow-gate-v2')
            retry=d['evaluation']['transport_retry_policy']
            self.assertEqual(retry['max_retries'],2)
            self.assertEqual(retry['backoff_ms'],2000.0)
            self.assertFalse(retry['semantic_client_4xx_retried'])
            self.assertTrue(retry['preserve_retry_ledger'])
