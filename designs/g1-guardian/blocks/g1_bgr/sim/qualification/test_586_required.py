import unittest
from run_586_required_ac import probe_source
from run_586_pvt import transform


class Required586Tests(unittest.TestCase):
    def test_gate_probe_preserves_original_device(self):
        source = '.subckt x vdd vss\nXM1 d pbias s b model w=1u l=1u\n.ends\n'
        modified, changed = probe_source(source, 'pbias')
        self.assertEqual(len(changed), 1)
        self.assertIn('XM1 d gate_probe s b model w=1u l=1u', modified)

    def test_missing_probe_rejected(self):
        with self.assertRaises(AssertionError):
            probe_source('.subckt x vdd vss\n.ends\n', 'pbias')

    def test_pvt_changes_only_declared_lines(self):
        deck = '/cornerHBT.lib hbt_typ\n/cornerMOShv.lib mos_tt\n/cornerRES.lib res_typ\nVdd vdd 0 3.3\ntran frozen\n'
        result = transform(deck, 'wcs', 'ss', 'bcs', 3.0)
        self.assertIn('tran frozen\n', result)
        self.assertIn('/cornerHBT.lib hbt_wcs\n', result)
        self.assertIn('Vdd vdd 0 3.0\n', result)

    def test_missing_supply_rejected(self):
        with self.assertRaises(AssertionError):
            transform('', 'wcs', 'ss', 'wcs', 3.0)


if __name__ == '__main__':
    unittest.main()
