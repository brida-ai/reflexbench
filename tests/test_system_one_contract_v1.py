import unittest

from system_one_contract_v1 import compile_request, normalize_question, validate_recipe


class SystemOneContractV1Test(unittest.TestCase):
    def test_binary_is_only_wire_normalized_to_noul(self):
        source={
            'type':'binary',
            'instructions':'Does the supplied evidence support the claim?',
            'criteria':{'true':'Evidence supports it.','false':'Evidence does not support it.'},
        }
        got=normalize_question(source)
        self.assertEqual(got,{
            'type':'noul',
            'instructions':source['instructions'],
            'criteria':source['criteria'],
        })
        self.assertEqual(source['type'],'binary')

    def test_choice_preserves_label_order_and_exact_text(self):
        q={'type':'choice','instructions':'Choose one.','criteria':{'z':'Zulu','a':'Alpha'}}
        got=normalize_question(q)
        self.assertEqual(list(got['criteria']),['z','a'])
        self.assertEqual(got['criteria'],q['criteria'])

    def test_score_preserves_ordinal_criteria(self):
        q={'type':'score','instructions':'Rate quality.','criteria':['bad','okay','good']}
        self.assertEqual(normalize_question(q),q)

    def test_engine_specific_prompting_is_rejected(self):
        for key in ('prompt','systemPrompt','temperature','adapter','engine','model'):
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError,'unsupported question keys'):
                    normalize_question({'type':'binary','instructions':'Question?',key:'x'})

    def test_choice_requires_semantic_criteria(self):
        with self.assertRaisesRegex(ValueError,'criteria'):
            normalize_question({'type':'choice','instructions':'Choose.'})
        with self.assertRaisesRegex(ValueError,'at least two'):
            normalize_question({'type':'choice','instructions':'Choose.','criteria':{'only':'one'}})

    def test_score_requires_ordered_criteria(self):
        with self.assertRaisesRegex(ValueError,'list'):
            normalize_question({'type':'score','instructions':'Rate.','criteria':{'1':'bad','2':'good'}})

    def test_compile_request_does_not_rewrite_state(self):
        state={'b':2,'a':{'x':1}}
        questions={'q':{'type':'binary','instructions':'Question?'}}
        got=compile_request(state,questions)
        self.assertIs(got['state'],state)
        self.assertEqual(got['questions']['q']['type'],'noul')
        self.assertEqual(set(got),{'state','questions'})

    def test_recipe_policy_question_must_exist_and_match_type(self):
        recipe={
            'questions':{'qualified':{'type':'binary','instructions':'Qualified?'}},
            'declarative_policy':{
                'type':'binary','questionId':'qualified','trueBranch':'yes','falseBranch':'no',
                'uncertainBranch':'review','trueWhenProbabilityAtLeast':.8,'falseWhenProbabilityAtMost':.2,
            },
        }
        validate_recipe(recipe)
        broken={**recipe,'declarative_policy':{**recipe['declarative_policy'],'questionId':'missing'}}
        with self.assertRaisesRegex(ValueError,'questionId'):
            validate_recipe(broken)
        mismatch={**recipe,'declarative_policy':{**recipe['declarative_policy'],'type':'choice'}}
        with self.assertRaisesRegex(ValueError,'type'):
            validate_recipe(mismatch)

    def test_recipe_cannot_embed_engine_specific_configuration(self):
        recipe={
            'questions':{'q':{'type':'binary','instructions':'Q?'}},
            'declarative_policy':{'type':'binary','questionId':'q'},
            'model':'jev-latest',
        }
        with self.assertRaisesRegex(ValueError,'engine-specific'):
            validate_recipe(recipe)


if __name__=='__main__':
    unittest.main()
