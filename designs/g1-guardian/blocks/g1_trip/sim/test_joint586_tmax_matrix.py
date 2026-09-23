import unittest
from prepare_joint586_tmax_matrix import declared_pair,matched_transform,OLD,NEW

class Tests(unittest.TestCase):
    def test_preserves_nodeset_and_only_tmax_output(self):
        old='setseed 78101\n.nodeset v(a)=.7\n'+OLD+'wrdata qualification/old/p54/phase0.dat v(a)\n'
        new=matched_transform(old,'old/p54','new',78101)
        self.assertEqual(new.replace(NEW,OLD).replace('qualification/new/phase0.dat','qualification/old/p54/phase0.dat'),old)
    def test_wrong_seed_or_solver_rejected(self):
        text='setseed 73001\n'+OLD+'wrdata qualification/a/phase0.dat v(a)\n'
        with self.assertRaises(AssertionError):matched_transform(text,'a','b',78101)
        with self.assertRaises(AssertionError):matched_transform(text+'.options klu\n','a','b',73001)
    def test_definition_not_decision_selects(self):
        rows=[dict(kind='residual',temperature_C=-40,shunt_V=v,codes=[1,2],condition=['cold_legacy',-40,3.3,1.2,None],decisions={'soft':True}) for v in [.0245,.0255]]
        declared_pair(rows,77101)
        rows[0]['shunt_V']=.0249
        with self.assertRaises(AssertionError):declared_pair(rows,77101)
    def test_wrong_corner_temperature_or_codes_rejected(self):
        rows=[dict(kind='residual',temperature_C=125,shunt_V=v,codes=[1,2],condition=['hot_legacy',125,3.3,1.2,None]) for v in [.0245,.0255]]
        declared_pair(rows,78101)
        rows[1]['codes']=[1,3]
        with self.assertRaises(AssertionError):declared_pair(rows,78101)
    def test_wrong_pair_order_rejected(self):
        rows=[dict(kind='residual',temperature_C=25,shunt_V=v,codes=[1,2]) for v in [.0255,.0245]]
        with self.assertRaises(AssertionError):declared_pair(rows,73001)

if __name__=='__main__':unittest.main()
