import copy
import unittest
from unittest.mock import patch
from audit_joint586_adverse_transients import cross_checks
from prepare_joint586_adverse_transients import CASES


class CrossControl(unittest.TestCase):
    def fixture(self):
        phase = dict(parameters_before=[['p', '1']], parameters_after=[['p', '1']], decisions={'hard': 'HIGH'})
        rows = {label: dict(phases=[copy.deepcopy(phase) for _ in temps]) for label, _, temps in CASES}
        rows['changed']['phases'][0]['parameters_before'] = [['p', '2']]
        old = (' '.join(['h']*18)+'\n'+' '.join(['1']*18)+'\n').encode()
        new = b''.join(line[:-1]+b' 0\n' for line in old.splitlines(keepends=True))
        waves = {label: [old for _ in temps] for label, _, temps in CASES}
        waves['cm0_shn19'] = [new]
        return rows, waves

    def check(self, rows, waves):
        with patch('audit_joint586_adverse_transients.variation', return_value={'test': dict(primitive_count=3500, primitives_with_changed_values=3500)}):
            return cross_checks(rows, waves)[0]

    def test_exact_controls(self):
        self.assertTrue(all(self.check(*self.fixture()).values()))

    def test_return_not_replaced_by_tolerance(self):
        rows, waves = self.fixture(); waves['return'][3] += b' '
        self.assertFalse(self.check(rows, waves)['return_wavebytes'])

    def test_appended_shn_cannot_change_original18(self):
        rows, waves = self.fixture(); waves['cm0_shn19'][0] = waves['cm0_shn19'][0].replace(b'1', b'2', 1)
        self.assertFalse(self.check(rows, waves)['cm0_original18_decoded_bytes_and_numeric_exact'])

    def test_disabled_seed_difference_is_failure(self):
        rows, waves = self.fixture(); rows['disabledchanged']['phases'][0]['parameters_before'] = [['p', '2']]
        self.assertFalse(self.check(rows, waves)['disabled11512'])

    def test_hot_vector_drift_is_failure(self):
        rows, waves = self.fixture(); rows['hot']['phases'][0]['parameters_after'] = [['p', '2']]
        self.assertFalse(self.check(rows, waves)['all_temperatures11512'])


if __name__ == '__main__':
    unittest.main()
