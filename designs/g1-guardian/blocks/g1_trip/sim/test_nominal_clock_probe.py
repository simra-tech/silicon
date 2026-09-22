"""Synthetic sampling-contract tests; no simulator or model edits."""
from pathlib import Path
import unittest
from run_nominal_clock_probe import analyze_wave, validate_saved_nodes

SIM = Path(__file__).resolve().parent


class NominalClockContract(unittest.TestCase):
    def setUp(self):
        self.sampling = {
            'delay_after_measured_edge_s': 20e-9,
            'legacy_phase_soft_samples_s': [440e-9, 640e-9, 840e-9],
            'legacy_phase_hard_samples_s': [540.2e-9, 740.2e-9, 940.2e-9],
        }
        self.rows = []
        for i in range(10201):
            t = i * .1e-9
            phase_ns = (i * .1 - 20) % 200
            clk = 1.2 * min(1., phase_ns / .2) if 0 <= phase_ns < 100 else 0.
            hard = 1.2 if 100.2 <= phase_ns else 0.
            self.rows.append([t, clk, .7, .75, .75, 0., 0., .7, hard, .1, .2, .3, .4])

    def test_five_cycles_and_two_sampling_policies(self):
        result = analyze_wave(self.rows, self.sampling)
        self.assertEqual(result['rising_crossing_counts'], {'soft': 5, 'hard': 5})
        self.assertEqual(result['sampling_status'], 'passed')
        self.assertEqual(len(result['hard_early_evaluation']), 5)
        self.assertIs(result['comparators']['hard']['measured_edge_decision'], False)

    def test_mixed_decisions_fail_closed(self):
        for row in self.rows:
            if 735e-9 < row[0] < 745e-9:
                row[6] = 1.2
        self.assertTrue(analyze_wave(self.rows, self.sampling)['sampling_status'].startswith('failed'))

    def test_missing_saved_vector_fails_closed(self):
        self.rows[1].pop()
        with self.assertRaises(AssertionError):
            analyze_wave(self.rows, self.sampling)

    def test_clock_count_fails_closed(self):
        for row in self.rows:
            row[8] = 0.
        self.assertEqual(analyze_wave(self.rows, self.sampling)['sampling_status'], 'failed clock crossing count')

    def test_short_endpoint_fails_closed(self):
        with self.assertRaises(AssertionError):
            analyze_wave(self.rows[:-1], self.sampling)

    def test_real_source_hierarchy_and_missing_saved_node(self):
        # Depend on tracked source, not a machine-local qualification directory.
        trip = (SIM / 'netlist' / 'g1_trip.spice').read_text()
        vectors = ' '.join('v(' + node + ')' for node in
                           ['xt.cmp_clk_n', 'xt.xch.xp', 'xt.xch.xq', 'xt.xch.xn', 'xt.xch.yn'])
        deck = 'XT test_nodes g1_trip\n.save v(clk) ' + vectors + '\nwrdata test.dat v(clk) ' + vectors + '\n'
        self.assertTrue(validate_saved_nodes(deck, trip)['status'].startswith('passed'))
        with self.assertRaises(AssertionError):
            validate_saved_nodes(deck.replace('v(xt.xch.xp)', 'v(xt.xch.missing)'), trip)


if __name__ == '__main__':
    unittest.main()
