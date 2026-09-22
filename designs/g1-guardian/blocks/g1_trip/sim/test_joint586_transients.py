import unittest
from prepare_joint586_transients import transform
from audit_joint586_transients import compare_wave


TEMPLATE = '.temp 25.0\n.include old/sense.spice\n.control\nset num_threads=1\nsetseed 71002\nreset\nop\ntran 0.2n 1.02u 0 0.2n\nwrdata old/hard_+0mV.dat v(clk)\necho QUALIFICATION_END\nquit 0\n.endc\n.end\n'


class TransientControlTests(unittest.TestCase):
    def test_byte_equality_not_replaced_by_numeric_equality(self):
        result = compare_wave(b't v\n0 1\n', b't v\n0.0 1.0\n')
        self.assertFalse(result['decoded_bytes_exact'])
        self.assertTrue(result['numeric_rows_exact'])

    def test_different_grid_has_no_invented_delta(self):
        result = compare_wave(b't v\n0 1\n', b't v\n1 1\n')
        self.assertFalse(result['time_grid_exact'])
        self.assertIsNone(result['maximum_abs_node_delta_V_on_exact_grid'])

    def test_single_phase_seed_temperature_only(self):
        result = transform(TEMPLATE, 'old', 'new', 73001, [125])
        expected = TEMPLATE.replace('.temp 25.0', '.temp 125.0').replace('old', 'new').replace('71002', '73001').replace('hard_+0mV.dat', 'phase0.dat')
        result = result.replace('echo PHASE0_BEGIN\n', '').replace('echo PHASE0_END\n', '').replace('echo JOINT_POPULATION_TRAN_END\n', '')
        self.assertEqual(result, expected)

    def test_return_preserves_four_full_phases_no_redraw(self):
        result = transform(TEMPLATE, 'old', 'new', 73001, [25, 125, -40, 25])
        self.assertEqual(result.count('\nreset\n'), 1)
        self.assertEqual(result.count('\nsetseed '), 1)
        self.assertEqual(result.count('tran 0.2n 1.02u 0 0.2n\n'), 4)
        self.assertEqual(result.count('\nop\n'), 4)
        self.assertEqual(result.count('set temp='), 4)
        self.assertIn('wrdata new/phase3.dat', result)

    def test_different_transient_setting_rejected(self):
        with self.assertRaises(AssertionError):
            transform(TEMPLATE.replace('1.02u', '1.01u'), 'old', 'new', 73001, [25])


if __name__ == '__main__':
    unittest.main()
