import unittest
from prepare_586_source_controls import inventory, transform, strip_queries
from run_586_source_control import requirements
from analyze_586_source_controls import calibrated


class SourceControlsTests(unittest.TestCase):
    def deck(self):
        return '.include bgr.spice\n.temp 12.5\nCout fout 0 50f\n.control\nset num_threads=1\ntran 5n 32u\nwrdata ptat_T12.5.dat v(fout)\n.endc\n'

    def test_exact_host_replay(self):
        self.assertEqual(transform(self.deck(), 12.5, {}, True), self.deck())

    def test_instrumentation_explicit_op_and_query_only(self):
        changed = transform(self.deck(), 12.5, {'BGR': ['@x[p]'], 'T2F': ['@y[q]']})
        self.assertEqual(strip_queries(changed), self.deck().replace('tran 5n 32u\n', 'op\ntran 5n 32u\n'))

    def test_source_only_pair_body(self):
        old = transform(self.deck(), 12.5, {'BGR': ['@old[p]'], 'T2F': ['@t[q]']})
        new = transform(self.deck(), 12.5, {'BGR': ['@new[p]', '@extra[p]'], 'T2F': ['@t[q]']})
        self.assertEqual(strip_queries(old), strip_queries(new))

    def test_nominal_primitive_inventory(self):
        q, rows = inventory('XM1 d g s b sg13_hv_nmos w=1u l=1u\nXR2 a b c rppd w=1u l=1u\nXQ3 c b e s npn13G2\nXC4 a b cap_cmim\nCext1 a b 1f\n', 'xt2f')
        self.assertEqual(len(q), 9)
        self.assertEqual(len(rows), 4)
        self.assertIn('@c.xt2f.xc4.c1[scale]', q)

    def test_wrong_original_timing_rejected(self):
        with self.assertRaises(AssertionError):
            transform(self.deck().replace('32u', '40u'), 25, {})

    def test_source_substitution_cannot_bypass_old_exact_gate(self):
        self.assertIn(('old-inventory', 'exact_historical_wave_status', 'passed'), requirements('new-paired'))
        self.assertEqual(requirements('new-t25'), [('new-paired', 'control_status', 'passed')])

    def test_original_linear_criterion_preserved(self):
        good = {-40: 600, 25: 1250, 100: 2000, 125: 2250}
        self.assertEqual(calibrated(good)['status'], 'passed')
        good[-40] += 30
        self.assertEqual(calibrated(good)['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
