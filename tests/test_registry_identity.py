import json
import tempfile
import unittest
from pathlib import Path
from registry_identity import custom_reflex_manifest_hash


class RegistryIdentityTest(unittest.TestCase):
    def test_hash_is_order_independent_and_content_sensitive(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name,value in [('a',1),('b',2)]:
                p=root/'examples'/'use-cases'/name/'custom-reflex.json'; p.parent.mkdir(parents=True); p.write_text(json.dumps({'v':value}))
            one=custom_reflex_manifest_hash(root,['a','b'])
            two=custom_reflex_manifest_hash(root,['b','a'])
            self.assertEqual(one,two)
            p=root/'examples'/'use-cases'/'b'/'custom-reflex.json'; p.write_text(json.dumps({'v':3}))
            self.assertNotEqual(one,custom_reflex_manifest_hash(root,['a','b']))


if __name__ == '__main__': unittest.main()
