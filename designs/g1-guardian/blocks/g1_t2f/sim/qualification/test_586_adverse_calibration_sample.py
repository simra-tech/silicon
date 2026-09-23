import unittest
from run_586_adverse_calibration_sample import reference_run, sample_deck, SEED_START, CONTROL_SEED
from prepare_586_adverse_controls import CONDITIONS
from analyze_586_adverse_controls import calibrate


class AdverseSampleTests(unittest.TestCase):
    def test_all_six_declared_transforms_restore_exact_reference(self):
        for corner in SEED_START:
            original = (reference_run(corner)/'probe.cir').read_text()
            for label, temperature, vdda, vdd, role in CONDITIONS:
                seed = SEED_START[corner]
                deck = sample_deck(original, corner, seed, label)
                for old, new in [('.temp %d\n' % temperature, '.temp 25\n'),
                    ('setseed %d\n' % seed, 'setseed %d\n' % CONTROL_SEED[corner]),
                    ('set temp=%d\n' % temperature, 'set temp=25\n'),
                    ('Vdd vdd 0 dc '+str(vdda)+'\n', 'Vdd vdd 0 dc 3.3\n'),
                    ('Vdd12 vdd12 0 dc '+str(vdd)+'\n', 'Vdd12 vdd12 0 dc 1.2\n'),
                    ('Ven en 0 pwl(0 0 1u 0 1.01u '+str(vdda)+')\n', 'Ven en 0 pwl(0 0 1u 0 1.01u 3.3)\n')]:
                    self.assertEqual(deck.count(old), 1)
                    deck = deck.replace(old, new)
                self.assertEqual(deck, original)

    def test_populations_and_conditions_are_not_interchangeable(self):
        original = (reference_run('slow')/'probe.cir').read_text()
        for seed in [74101, 75100, 75131, 75201]:
            with self.assertRaises(AssertionError):
                sample_deck(original, 'slow', seed, 'cal25')
        with self.assertRaises(ValueError):
            sample_deck(original, 'slow', 75101, 'extra')

    def test_frozen_linear_failure_not_refitted(self):
        values = {label: 1000000+1000*temperature for label, temperature, a, d, role in CONDITIONS}
        values['highcold'] -= 2100
        result = calibrate(values)
        self.assertEqual(result['status'], 'failed')
        self.assertAlmostEqual(result['maximum_independent_abs_residual_C'], 2.1)
        self.assertEqual(result['slope_Hz_per_C'], 1000)


if __name__ == '__main__':
    unittest.main()
