import unittest
from prepare_bgr_prefix_probe import transform, FULL_TRAN, PREFIX_TRAN, require_measurements_inside_prefix
from run_bgr_prefix_probe import analyze_prefix
from analyze_bgr_prefix_trajectories import initial_warning_phases
from audit_failed_bgr_prefix import audit_measurement_errors, EXPECTED


class PrefixTransformTests(unittest.TestCase):
    def test_exact_reversible_single_endpoint_change(self):
        old = 'include qualification/old/bgr.spice\n' + FULL_TRAN + 'wrdata qualification/old/wave.dat v(x)\n'
        new = transform(old, 'old', 'fresh')
        self.assertEqual(new.replace('fresh', 'old').replace(PREFIX_TRAN, FULL_TRAN), old)

    def test_missing_or_repeated_transient_rejected(self):
        for deck in ['', FULL_TRAN + FULL_TRAN]:
            with self.assertRaises(AssertionError):
                transform(deck, 'old', 'fresh')

    def test_future_measurement_preflight_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'Future-window'):
            require_measurements_inside_prefix('meas tran ds_sample find ds at=8.4e-07\n')
        self.assertEqual(require_measurements_inside_prefix('meas tran first find ds at=4e-08\n'), [('first', '4e-08')])


class PrefixWaveTests(unittest.TestCase):
    def wave(self):
        rows = []
        for i in range(2191):
            t = i*.1e-9
            row = [0.0]*18
            row[0] = t
            row[1] = 1.2 if 20e-9 <= t < 120.2e-9 else 0.0
            row[8] = 1.2 if t >= 120.5e-9 else 0.0
            rows.append(row)
        return rows

    def test_first_pair_only(self):
        result = analyze_prefix(self.wave())
        self.assertTrue(result['status'].startswith('passed'))
        for row in result['channels'].values():
            self.assertEqual(row['actual_decision'], 'LOW')
            self.assertTrue(row['sampling_policies_agree'])
            self.assertEqual(len(row['early_evolution']), 6)

    def test_incomplete_and_missing_columns_rejected(self):
        for rows in [self.wave()[:-1], [row[:13] for row in self.wave()]]:
            with self.assertRaises(AssertionError):
                analyze_prefix(rows)

    def test_extra_clock_rise_rejected(self):
        rows = self.wave()
        for row in rows:
            if 150e-9 < row[0] < 151e-9:
                row[1] = 1.2
        with self.assertRaises(AssertionError):
            analyze_prefix(rows)


class InitializationWarningTests(unittest.TestCase):
    def test_phase_boundaries_and_instance_nan(self):
        log = ('WARNING: first\nNON_BGR_BEFORE_BEGIN\n'
               '@n.xt.xmnan1[w] = 1e-6\nBGR_BEFORE_END\n'
               'WARNING: initialization\nInitial Transient Solution\n'
               'WARNING: positive time\n')
        self.assertEqual(initial_warning_phases(log), {'before_inventory': 1, 'inventory': 0,
                         'transient_initialization': 1, 'after_initial_transient_solution': 1})


class FailedFixtureAuditTests(unittest.TestCase):
    def fixtures(self):
        names = sorted(EXPECTED)
        return (['Error: measure  %s  find(AT) : out of interval' % name for name in names],
                ''.join('meas tran %s find ds at=8.4e-07\n' % name for name in names))

    def test_exact_eight_errors(self):
        errors, deck = self.fixtures()
        self.assertEqual(len(audit_measurement_errors(errors, deck)), 8)

    def test_other_or_missing_error_rejected(self):
        errors, deck = self.fixtures()
        for invalid in [errors[:-1], errors+['Error: no such vector'], errors[:-1]+['Error: timestep too small']]:
            with self.assertRaises(AssertionError):
                audit_measurement_errors(invalid, deck)


if __name__ == '__main__':
    unittest.main()
