import unittest

from systemone_helpers import average_choice_answers, normalize_questions, reverse_choice_question


class SystemOneHelpersTest(unittest.TestCase):
    def test_binary_maps_to_noul_without_mutating_input(self):
        src = {"q": {"type": "binary", "instructions": "x"}}
        got = normalize_questions(src)
        self.assertEqual(got["q"]["type"], "noul")
        self.assertEqual(src["q"]["type"], "binary")

    def test_reverse_choice_preserves_label_meaning(self):
        q = {"type": "choice", "criteria": {"a": "A", "b": "B", "c": "C"}}
        got = reverse_choice_question(q)
        self.assertEqual(list(got["criteria"]), ["c", "b", "a"])
        self.assertEqual(got["criteria"]["b"], "B")

    def test_average_choice_aligns_by_label_not_position(self):
        a = {"probabilities": {"a": 0.8, "b": 0.2}}
        b = {"probabilities": {"b": 0.6, "a": 0.4}}
        got = average_choice_answers(a, b)
        self.assertAlmostEqual(got["probabilities"]["a"], 0.6)
        self.assertAlmostEqual(got["probabilities"]["b"], 0.4)
        self.assertEqual(got["choice"], "a")


if __name__ == "__main__":
    unittest.main()
