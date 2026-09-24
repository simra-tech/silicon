import unittest
from run_hardclock4_diagnostic import trip_transform, deck_transform, rounding_relation, SIM, PARENT


class Controls(unittest.TestCase):
    def test_exact_local_source(self):
        old=(SIM/'qualification'/PARENT/'trip.spice').read_text();new=trip_transform(old)
        self.assertEqual(new.count('.subckt g1_inv_hardclock4 '),1)
        self.assertEqual(new.count('XCLKI cmp_clk cmp_clk_n vdd vss g1_inv_hardclock4\n'),1)
        self.assertTrue(new.startswith(old.replace('XCLKI cmp_clk cmp_clk_n vdd vss g1_inv\n','XCLKI cmp_clk cmp_clk_n vdd vss g1_inv_hardclock4\n')))
        with self.assertRaises(AssertionError):trip_transform(new)

    def test_wrong_original_width_rejected(self):
        old=(SIM/'qualification'/PARENT/'trip.spice').read_text()
        with self.assertRaises(AssertionError):trip_transform(old.replace('XMP y a vdd vdd sg13_lv_pmos w=1u l=0.13u','XMP y a vdd vdd sg13_lv_pmos w=2u l=0.13u'))

    def test_deck_original_time_held(self):
        old=(SIM/'qualification'/PARENT/'p57/probe.cir').read_text()
        new=deck_transform(old,'p57','example');self.assertIn('tran 0.2n 1.02u 0 0.2n\n',new)
        with self.assertRaises(AssertionError):deck_transform(old.replace('0 0.2n\n','0 1n\n'),'p57','example')

    def test_native_width_delta(self):
        rounding_relation('9.969208106195320e-7','3.996920810619532e-6','w',1e-6)
        with self.assertRaises(AssertionError):rounding_relation('9.969208106195320e-7','4.000000000000000e-6','w',1e-6)

    def test_native_sigma_half(self):
        rounding_relation('2.812302582634026e-3','1.406151291317013e-3','delvto',1e-6)
        rounding_relation('9.956766444669786e-1','9.978383222334893e-1','factuo',1e-6)
        with self.assertRaises(AssertionError):rounding_relation('2.812302582634026e-3','2.812302582634026e-3','delvto',1e-6)


if __name__=='__main__':unittest.main()
