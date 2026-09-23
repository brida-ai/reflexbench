import json
import tempfile
import unittest
from pathlib import Path

from build_public_fixture_corpus import build


class BuildPublicFixtureCorpusTest(unittest.TestCase):
    def test_deterministic_order_and_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, branch in (("z-case", "z"), ("a-case", "a")):
                p = root / "examples" / "use-cases" / name / "custom-reflex.json"
                p.parent.mkdir(parents=True)
                p.write_text(json.dumps({
                    "questions": {
                        "decision": {
                            "type": "choice",
                            "instructions": "Choose one.",
                            "criteria": {"a": "Option A", "z": "Option Z"},
                        }
                    },
                    "declarative_policy": {"type": "choice", "questionId": "decision"},
                    "fixtures": [{"id": "one", "state": {"x": name}, "expectedBranch": branch}],
                }))
            one, m1 = build(root, "abc")
            two, m2 = build(root, "abc")
            self.assertEqual(one, two)
            self.assertEqual(m1, m2)
            rows = [json.loads(x) for x in one.decode().splitlines()]
            self.assertEqual([r["useCase"] for r in rows], ["a-case", "z-case"])
            self.assertEqual(m1["rows"], 2)
            self.assertEqual(m1["policy_fixture_counts"], {"choice": 2})

    def test_engine_specific_recipe_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "examples" / "use-cases" / "bad" / "custom-reflex.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({
                "model": "jev-latest",
                "questions": {"q": {"type": "binary", "instructions": "Q?"}},
                "declarative_policy": {"type": "binary", "questionId": "q"},
                "fixtures": [{"state": {"x": 1}, "expectedBranch": "yes"}],
            }))
            with self.assertRaisesRegex(ValueError, "engine-specific"):
                build(root, "abc")


if __name__ == "__main__":
    unittest.main()
