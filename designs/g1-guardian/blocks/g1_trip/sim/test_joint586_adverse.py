import unittest
from prepare_joint586_adverse import transform_fixture, SIM, REFERENCE


class Transform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.deck=(SIM/'qualification'/REFERENCE/'population_transient.cir').read_text()
    def test_typ_legacy_is_literal_identity(self):
        changed,diff=transform_fixture(self.deck,'typ',3.3,1.2,None)
        self.assertEqual(changed,self.deck)
        self.assertEqual(diff,[])
    def test_rails_scale_only_high_bits_and_clock(self):
        changed,diff=transform_fixture(self.deck,'slow',3.,1.08,None)
        self.assertIn('pulse(0 1.08 20n 0.2n 0.2n 100n 200n)',changed)
        self.assertNotIn(' dc 1.2\n',changed)
        self.assertEqual(changed.split('.control\n')[1],self.deck.split('.control\n')[1])
        self.assertEqual(changed.count('_mismatch\n'),5)
    def test_true_common_mode_holds_differential(self):
        import re
        for cm in [-.1,0.,.3]:
            changed,diff=transform_fixture(self.deck,'fast',3.6,1.32,cm)
            p=float(re.search(r'^Vsh shp 0 dc (.+)$',changed,re.M).group(1))
            n=float(re.search(r'^Vshn shn 0 dc (.+)$',changed,re.M).group(1))
            self.assertAlmostEqual(p-n,.025,places=15)
            self.assertAlmostEqual((p+n)/2,cm,places=15)
            self.assertIn('XS shp shn ',changed)


if __name__=='__main__':unittest.main()
