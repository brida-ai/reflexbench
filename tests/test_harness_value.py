import unittest
from harness_value import bootstrap_policy_delta, paired_layer_value, policy_value


class HarnessValueTest(unittest.TestCase):
    def test_policy_rescues_and_harms_are_distinct(self):
        rows = [
            {"semantic_branch":"a","operational_branch":"a","semantic_correct":True,"operational_correct":True},
            {"semantic_branch":"a","operational_branch":"review","semantic_correct":False,"operational_correct":True},
            {"semantic_branch":"a","operational_branch":"review","semantic_correct":True,"operational_correct":False},
            {"semantic_branch":"a","operational_branch":"a","semantic_correct":False,"operational_correct":False},
        ]
        out = policy_value(rows)
        self.assertEqual(out["rescues"], 1)
        self.assertEqual(out["harms"], 1)
        self.assertEqual(out["net_rescues_minus_harms"], 0)
        self.assertEqual(out["interventions"], 2)
        self.assertEqual(out["net_accuracy_delta"], 0)

    def test_paired_layer_detects_hidden_branch_flips(self):
        a = [
            {"use_case":"u","case_id":"1","semantic_branch":"x","operational_branch":"x","semantic_correct":True,"operational_correct":True},
            {"use_case":"u","case_id":"2","semantic_branch":"y","operational_branch":"y","semantic_correct":False,"operational_correct":False},
        ]
        b = [
            {"use_case":"u","case_id":"1","semantic_branch":"z","operational_branch":"z","semantic_correct":False,"operational_correct":False},
            {"use_case":"u","case_id":"2","semantic_branch":"x","operational_branch":"x","semantic_correct":True,"operational_correct":True},
        ]
        out = paired_layer_value(a,b)
        self.assertEqual(out["semantic_accuracy_a"], out["semantic_accuracy_b"])
        self.assertEqual(out["semantic_branch_flips"], 2)
        self.assertEqual(out["b_semantic_rescues"], 1)
        self.assertEqual(out["b_semantic_harms"], 1)

    def test_bootstrap_policy_delta_preserves_pairing(self):
        rows = [
            {"semantic_correct":False,"operational_correct":True},
            {"semantic_correct":True,"operational_correct":True},
            {"semantic_correct":True,"operational_correct":True},
            {"semantic_correct":True,"operational_correct":True},
        ]
        out = bootstrap_policy_delta(rows, iterations=1000, seed=7)
        self.assertAlmostEqual(out["point_delta"], .25)
        self.assertGreaterEqual(out["ci95_low"], 0.0)
        self.assertLessEqual(out["ci95_high"], .75)

    def test_paired_layer_fails_on_mismatched_rows(self):
        a=[{"use_case":"u","case_id":"1","semantic_branch":"x","operational_branch":"x","semantic_correct":True,"operational_correct":True}]
        b=[{"use_case":"u","case_id":"2","semantic_branch":"x","operational_branch":"x","semantic_correct":True,"operational_correct":True}]
        with self.assertRaises(ValueError): paired_layer_value(a,b)


if __name__ == '__main__': unittest.main()
