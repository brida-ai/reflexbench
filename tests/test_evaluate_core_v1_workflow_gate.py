import unittest

from evaluate_core_v1_workflow_gate import slice_summary


class CoreWorkflowGateEvaluatorTest(unittest.TestCase):
    def test_same_response_rescues_harms_and_review_coverage(self):
        rows=[
            {'use_case':'a','semantic_correct':False,'operational_correct':True,'semantic_branch':'yes','operational_branch':'review'},
            {'use_case':'a','semantic_correct':True,'operational_correct':False,'semantic_branch':'yes','operational_branch':'review'},
            {'use_case':'a','semantic_correct':True,'operational_correct':True,'semantic_branch':'yes','operational_branch':'yes'},
            {'use_case':'b','semantic_correct':True,'operational_correct':True,'semantic_branch':'publish','operational_branch':'publish'},
        ]
        got=slice_summary(rows,{'a':'review','b':None})
        self.assertEqual(got['rescues'],1)
        self.assertEqual(got['harms'],1)
        self.assertEqual(got['interventions'],2)
        self.assertEqual(got['review_count'],2)
        self.assertAlmostEqual(got['automation_coverage'],.5)
        self.assertEqual(got['direct_action_accuracy'],1.0)
        self.assertEqual(got['paired_delta'],0.0)

    def test_slice_summary_allows_completed_subset_for_transport_failure_diagnostics(self):
        rows=[
            {'use_case':'a','semantic_correct':True,'operational_correct':True,'semantic_branch':'yes','operational_branch':'yes'},
        ]
        got=slice_summary(rows,{'a':'review'})
        self.assertEqual(got['n'],1)
        self.assertEqual(got['core_exact_branch_accuracy'],1.0)


if __name__=='__main__': unittest.main()


class SameResponseInvariantTest(unittest.TestCase):
    def test_v1_requires_one_http_request_per_completed_row(self):
        from evaluate_core_v1_workflow_gate import same_response_invariant
        procedure={'evaluation':{}}
        result={'ablation':{'choice_ensemble':'none','native_permutations':None},'run':{'http_requests':3}}
        got=same_response_invariant(procedure,result,3)
        self.assertTrue(got['holds'])
        self.assertEqual(got['mode'],'legacy-no-retry')

    def test_v1_rejects_extra_http_request_without_predeclared_retry(self):
        from evaluate_core_v1_workflow_gate import same_response_invariant
        procedure={'evaluation':{}}
        result={'ablation':{'choice_ensemble':'none','native_permutations':None},'run':{'http_requests':4}}
        self.assertFalse(same_response_invariant(procedure,result,3)['holds'])

    def test_v2_accepts_predeclared_transport_retry_without_semantic_extra_pass(self):
        from evaluate_core_v1_workflow_gate import same_response_invariant
        procedure={'evaluation':{'transport_retry_policy':{'max_retries':2,'backoff_ms':2000.0}}}
        result={
            'ablation':{'choice_ensemble':'none','native_permutations':None,'transport_retries':2,'transport_retry_backoff_ms':2000.0},
            'run':{'http_requests':4,'transport_retry_requests':1,'successful_decisions':3},
        }
        got=same_response_invariant(procedure,result,3)
        self.assertTrue(got['holds'])
        self.assertEqual(got['mode'],'predeclared-transport-retry')
        self.assertEqual(got['transport_retry_requests'],1)

    def test_v2_rejects_retry_config_drift(self):
        from evaluate_core_v1_workflow_gate import same_response_invariant
        procedure={'evaluation':{'transport_retry_policy':{'max_retries':2,'backoff_ms':2000.0}}}
        result={
            'ablation':{'choice_ensemble':'none','native_permutations':None,'transport_retries':1,'transport_retry_backoff_ms':2000.0},
            'run':{'http_requests':4,'transport_retry_requests':1,'successful_decisions':3},
        }
        self.assertFalse(same_response_invariant(procedure,result,3)['holds'])
