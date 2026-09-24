import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class MachineSurfacesTest(unittest.TestCase):
    def test_discovery_targets_exist(self):
        d=json.loads((ROOT/'benchmark.json').read_text())
        self.assertEqual(d['id'],'brida/reflexbench')
        self.assertEqual(d['version'],'1.0.0')
        for key in ['primary_leaderboard','submission_guide','submission_schema','lab_integration_guide','citation','badge']:
            self.assertTrue((ROOT/d[key]).exists(), key)

    def test_primary_leaderboard_matches_locked_claims(self):
        d=json.loads((ROOT/'leaderboards/v1.json').read_text())
        rows=d['primary_lane']['results']
        self.assertEqual(d['primary_lane']['rows'],111)
        self.assertEqual([round(x['semantic_accuracy'],3) for x in rows],[.730,.414,.396,.378,.369,.351,.324])
        self.assertEqual(rows[0]['display_name'],'TypeSafe Jev')
        self.assertIn('jeff / GLiFormer', rows[3]['display_name'])
        for x in rows:
            self.assertTrue((ROOT/x['receipt']).exists(), x['receipt'])

    def test_harness_lane_is_explicitly_separate(self):
        d=json.loads((ROOT/'leaderboards/v1.json').read_text())
        h=d['supplemental_lanes']['public110_reflex_harness_ablation']
        self.assertAlmostEqual(h['simple_mean_delta_pp'],2.9090909091,places=8)
        self.assertAlmostEqual(h['max_delta_pp'],8.1818181818,places=8)
        j=d['supplemental_lanes']['typesafe_jev_same_response_policy']
        self.assertAlmostEqual(j['raw_semantic_accuracy'],106/110)
        self.assertEqual(j['reflex_operational_accuracy'],1.0)
        self.assertEqual(j['extra_model_calls'],0)
        self.assertIn('not 100% raw semantic accuracy',j['note'])

if __name__=='__main__': unittest.main()
