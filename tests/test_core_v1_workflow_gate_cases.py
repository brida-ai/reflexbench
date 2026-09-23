import unittest
from collections import Counter

from build_core_v1_workflow_gate_cases import build


class CoreWorkflowCaseBuilderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = build()

    def test_exact_balanced_shape(self):
        self.assertEqual(len(self.rows), 150)
        self.assertEqual(len({row["id"] for row in self.rows}), 150)
        by_workflow = Counter(row["useCase"] for row in self.rows)
        self.assertEqual(len(by_workflow), 5)
        self.assertTrue(all(value == 30 for value in by_workflow.values()))
        by_language = Counter(
            (row["useCase"], row["language"]) for row in self.rows
        )
        self.assertTrue(all(value == 15 for value in by_language.values()))
        by_class = Counter(
            (row["useCase"], row["caseClass"]) for row in self.rows
        )
        self.assertTrue(all(value == 10 for value in by_class.values()))

    def test_blind_provenance_and_no_engine_fields(self):
        forbidden = {
            "questions",
            "question",
            "prompt",
            "systemPrompt",
            "model",
            "engine",
            "provider",
            "adapter",
            "temperature",
            "answer",
            "answers",
            "probabilities",
            "confidence",
        }
        for row in self.rows:
            self.assertFalse(set(row) & forbidden)
            self.assertFalse(
                row["provenance"]["modelOutputsObservedBeforeFreeze"]
            )

    def test_paired_translation_groups(self):
        groups = Counter(
            row["provenance"]["pairedTranslationGroup"] for row in self.rows
        )
        self.assertEqual(len(groups), 75)
        self.assertTrue(all(value == 2 for value in groups.values()))


if __name__ == "__main__":
    unittest.main()
