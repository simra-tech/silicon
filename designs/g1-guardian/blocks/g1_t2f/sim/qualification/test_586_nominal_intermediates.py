import unittest
from prepare_586_nominal_intermediates import deck_for, REFERENCE
from run_586_nominal_intermediate import frozen_residual
import json


class IntermediateTests(unittest.TestCase):
    def test_temperature_only_deck_difference(self):
        groups = json.loads((REFERENCE/'preparation.json').read_text())['query_groups']
        reference = (REFERENCE/'probe.cir').read_text()
        for t in [-20, 0, 50, 75]:
            self.assertEqual(deck_for(t, groups).replace('.temp '+str(float(t))+'\n', '.temp 25.0\n'), reference)

    def test_out_of_scope_temperature_rejected(self):
        with self.assertRaises(AssertionError):
            deck_for(125, {})

    def test_frozen_calibration_no_refit(self):
        analysis = {'status': 'passed', 'points': [{'temperature_C': 25, 'frequency_Hz': 1000}, {'temperature_C': 100, 'frequency_Hz': 1750}]}
        self.assertEqual(frozen_residual(50, 1250, analysis)['status'], 'passed')
        result = frozen_residual(50, 1271, analysis)
        self.assertEqual(result['status'], 'failed')
        self.assertAlmostEqual(result['residual_C'], 2.1)


if __name__ == '__main__':
    unittest.main()
