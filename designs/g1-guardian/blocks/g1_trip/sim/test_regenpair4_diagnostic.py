import unittest
from run_regenpair4_diagnostic import trip_transform, deck_transform, rounding_relation, SIM, PARENT


class Controls(unittest.TestCase):
    def test_only_hard_pair(self):
        old=(SIM/'qualification'/PARENT/'trip.spice').read_text();new=trip_transform(old)
        self.assertEqual(new.count('.subckt g1_cmp_regenpair4 '),1)
        self.assertIn('XCLKI cmp_clk cmp_clk_n vdd vss g1_inv\n',new)
        self.assertIn('XCS icmp vth_soft cmp_clk cmp_soft cmp_soft_n vdd vss g1_cmp\n',new)
        self.assertEqual(new.count('XM3 xn yn xp vss sg13_lv_nmos w=6u l=0.26u ng=1 m=1 mm_ok=1\n'),1)
        with self.assertRaises(AssertionError):trip_transform(new)

    def test_wrong_pair_source_rejected(self):
        old=(SIM/'qualification'/PARENT/'trip.spice').read_text()
        with self.assertRaises(AssertionError):trip_transform(old.replace('XM3 xn yn xp vss sg13_lv_nmos w=3u l=0.13u','XM3 xn yn xp vss sg13_lv_nmos w=4u l=0.13u'))

    def test_time_and_clock_held(self):
        old=(SIM/'qualification'/PARENT/'p57/probe.cir').read_text();new=deck_transform(old,'p57','example')
        self.assertIn('tran 0.2n 1.02u 0 0.2n\n',new)
        with self.assertRaises(AssertionError):deck_transform(old.replace('0 0.2n\n','0 1n\n'),'p57','example')

    def test_absolute_geometry_noise(self):
        rounding_relation('2.998000000000000e-6','5.998000000000000e-6','w',3e-6)
        rounding_relation('1.280000000000000e-7','2.580000000000000e-7','l',.13e-6)
        with self.assertRaises(AssertionError):rounding_relation('2.998000000000000e-6','5.996000000000000e-6','w',3e-6)

    def test_native_sigma_half(self):
        rounding_relation('1.100000000000000e-2','5.500000000000000e-3','delvto',3e-6)
        rounding_relation('1.020000000000000e+0','1.010000000000000e+0','factuo',3e-6)
        with self.assertRaises(AssertionError):rounding_relation('1.100000000000000e-2','1.100000000000000e-2','delvto',3e-6)


if __name__=='__main__':unittest.main()
