import json,tempfile,unittest
from pathlib import Path
from validate_reflex_registry_v1 import validate_registry

class RegistryValidationTest(unittest.TestCase):
    def write(self,root,name,payload):
        p=root/'examples'/'use-cases'/name/'custom-reflex.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload)); return p
    def valid(self):
        return {'questions':{'q':{'type':'choice','instructions':'Choose.','criteria':{'a':'A','b':'B'}}},'declarative_policy':{'type':'choice','questionId':'q'}}
    def test_valid_registry(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self.write(root,'a',self.valid()); self.write(root,'b',self.valid()); d=validate_registry(root,'abc'); self.assertTrue(d['all_valid']); self.assertEqual(d['recipes_valid'],2); self.assertEqual(d['question_type_counts'],{'choice':2})
    def test_invalid_recipe_is_reported_not_dropped(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self.write(root,'ok',self.valid()); bad=self.valid(); bad['model']='jev-latest'; self.write(root,'bad',bad); d=validate_registry(root,'abc'); self.assertFalse(d['all_valid']); self.assertEqual(d['recipes_total'],2); self.assertEqual(d['recipes_failed'],1); self.assertEqual(d['failures'][0]['id'],'bad')

if __name__=='__main__': unittest.main()
