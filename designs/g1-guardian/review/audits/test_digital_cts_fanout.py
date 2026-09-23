import unittest
from pathlib import Path
from run_digital_cts_fanout import environment_text, corner_environment


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.original = 'set ::env(CURRENT_ODB) /held/input.odb\n' + ''.join(
            'set ::env(SAVE_' + kind + ') /old/' + kind + '\n'
            for kind in ('ODB', 'DEF', 'SDC', 'NL', 'PNL'))

    def test_baseline_changes_only_outputs(self):
        result = environment_text(self.original, Path('/fresh'), 0)
        self.assertIn('set ::env(CURRENT_ODB) /held/input.odb', result)
        self.assertNotIn('CTS_SINK_CLUSTERING_SIZE', result)
        self.assertEqual(result.count('/fresh/'), 5)

    def test_candidate_only_adds_cluster(self):
        baseline = environment_text(self.original, Path('/fresh'), 0)
        candidate = environment_text(self.original, Path('/fresh'), 8)
        self.assertEqual(candidate, baseline + 'set ::env(CTS_SINK_CLUSTERING_SIZE) 8\n')

    def test_missing_output_rejected(self):
        with self.assertRaises(AssertionError):
            environment_text(self.original.replace('SAVE_NL', 'BROKEN_NL'), Path('/fresh'), 8)

    def test_preexisting_cluster_rejected(self):
        with self.assertRaises(AssertionError):
            environment_text(self.original + '# CTS_SINK_CLUSTERING_SIZE\n', Path('/fresh'), 8)

    def test_unsupported_cluster_rejected(self):
        with self.assertRaises(AssertionError):
            environment_text(self.original, Path('/fresh'), 16)

    def test_derived_corner_and_rc_coverage(self):
        import json
        config = json.loads((Path(__file__).parents[2] / 'blocks/g1_ctrl/flow/runs/run7/35-openroad-cts/config.json').read_text())
        result = corner_environment(config, lambda x: x, ['exclude1'])
        self.assertEqual(sum(k.startswith('_LIB_CORNER_') for k in result), 3)
        self.assertEqual(sum(k.startswith('_LAYER_RC_') for k in result), 15)
        self.assertEqual(sum(k.startswith('_VIA_R_') for k in result), 21)
        self.assertEqual(result['_PNR_EXCLUDED_CELLS'], ['exclude1'])
        self.assertEqual(result['_LAYER_RC_0'][2:], [0.00854576, 1e-10])


if __name__ == '__main__':
    unittest.main()
