import unittest
from run_top import CASES, shift_fault_phase


class FaultPhaseTests(unittest.TestCase):
    def test_zero_is_exact_existing_fixture(self):
        for name, case in CASES.items():
            self.assertEqual(shift_fault_phase(case, name, 0), case)

    def test_only_fault_times_move(self):
        for name in ['c_mid', 'hard_pulse', 'hard_pulse400']:
            old = CASES[name]
            new = shift_fault_phase(old, name, 125)
            self.assertEqual(new['frames'], old['frames'])
            self.assertEqual(new['load'][0], old['load'][0])
            self.assertEqual(new['event_us'], 30.125)
            self.assertEqual(new['tstop'], old['tstop'])
            for (t, v), (nt, nv) in zip(old['load'][1:], new['load'][1:]):
                self.assertAlmostEqual(nt - t, 125e-9, places=15)
                self.assertEqual(nv, v)
            self.assertNotIn('event_us', old)

    def test_bad_scope_and_numbers_rejected(self):
        for value in [-1, 501, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                shift_fault_phase(CASES['c_mid'], 'c_mid', value)
        for name, timeline in [('b_s', 'baseline'), ('c_mid', 'compact')]:
            with self.assertRaises(ValueError):
                shift_fault_phase(CASES[name], name, 125, timeline)

    def test_distinct_pulse_widths_preserve_original(self):
        from check_campaign import pulse_half_height_width
        self.assertAlmostEqual(pulse_half_height_width(CASES['hard_pulse']['load'],1),200e-9,places=15)
        self.assertAlmostEqual(pulse_half_height_width(CASES['hard_pulse400']['load'],1),400e-9,places=15)
        with self.assertRaises(ValueError):
            pulse_half_height_width(CASES['c_mid']['load'],1)


if __name__ == '__main__':
    unittest.main()
