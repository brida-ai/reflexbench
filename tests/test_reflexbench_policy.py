import unittest

from reflexbench_policy import apply_declarative_policy


class PolicyTest(unittest.TestCase):
    def test_choice_separates_semantic_from_threshold(self):
        policy = {
            "type": "choice",
            "branches": {"progressing": "continue", "stalled": "inspect"},
            "minimumSelectedProbability": 0.78,
            "uncertainBranch": "review",
        }
        answer = {
            "type": "choice",
            "choice": "progressing",
            "probabilities": {"progressing": 0.606, "stalled": 0.394},
        }
        got = apply_declarative_policy(policy, answer)
        self.assertEqual(got.semantic_branch, "continue")
        self.assertEqual(got.operational_branch, "review")
        self.assertAlmostEqual(got.selected_probability, 0.606)

    def test_binary_thresholds(self):
        policy = {
            "type": "binary",
            "trueBranch": "include",
            "falseBranch": "discard",
            "trueWhenProbabilityAtLeast": 0.82,
            "falseWhenProbabilityAtMost": 0.18,
            "uncertainBranch": "review",
        }
        high = apply_declarative_policy(policy, {"type": "noul", "noul": 0.91})
        mid = apply_declarative_policy(policy, {"type": "noul", "noul": 0.63})
        low = apply_declarative_policy(policy, {"type": "noul", "noul": 0.08})
        self.assertEqual((high.semantic_branch, high.operational_branch), ("include", "include"))
        self.assertEqual((mid.semantic_branch, mid.operational_branch), ("include", "review"))
        self.assertEqual((low.semantic_branch, low.operational_branch), ("discard", "discard"))

    def test_score_uses_declared_thresholds(self):
        policy = {
            "type": "score",
            "thresholds": [
                {"atLeast": 3.5, "branch": "publish"},
                {"atLeast": 1.5, "branch": "revise"},
            ],
            "belowBranch": "reject",
        }
        self.assertEqual(apply_declarative_policy(policy, {"type": "score", "score": 3.8}).operational_branch, "publish")
        self.assertEqual(apply_declarative_policy(policy, {"type": "score", "score": 2.2}).operational_branch, "revise")
        self.assertEqual(apply_declarative_policy(policy, {"type": "score", "score": 0.8}).operational_branch, "reject")


if __name__ == "__main__":
    unittest.main()
