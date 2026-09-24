import copy, importlib.util, json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("validate_submission",ROOT/"tools/validate_submission.py")
mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)

class SubmissionEnvelopeTest(unittest.TestCase):
    def setUp(self): self.valid=json.loads((ROOT/"templates/result-submission-v1.json").read_text())
    def test_template_is_valid(self): self.assertEqual(mod.validate(self.valid),[])
    def test_rejects_bad_sha(self):
        d=copy.deepcopy(self.valid); d["corpus"]["sha256"]="abc"; self.assertTrue(any("sha256" in x for x in mod.validate(d)))
    def test_rejects_out_of_range_accuracy(self):
        d=copy.deepcopy(self.valid); d["metrics"]["semantic_accuracy"]=1.1; self.assertTrue(any("semantic_accuracy" in x for x in mod.validate(d)))
    def test_rejects_missing_receipts(self):
        d=copy.deepcopy(self.valid); d["evidence"]["receipt_paths"]=[]; self.assertTrue(any("receipt_paths" in x for x in mod.validate(d)))
    def test_requires_development_disclosure(self):
        d=copy.deepcopy(self.valid); del d["evidence"]["benchmark_used_for_development"]; self.assertTrue(any("benchmark_used" in x for x in mod.validate(d)))

if __name__ == '__main__': unittest.main()
