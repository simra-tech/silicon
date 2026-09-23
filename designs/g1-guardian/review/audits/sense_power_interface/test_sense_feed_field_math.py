#!/usr/bin/env python3
import copy
import unittest
from sense_feed_field_math import parse_caps, reduce_caps, ac_check, context_check


def provenance():
    rows=[dict(label=n,group=g,source_net=s) for n,g,s in
          [('P','P','vdd'),('PSEG','P','vdd'),('N','N','pc1'),('CTX','context','other')]]
    return dict(fill_count=0,MIM_Vmim_count=0,labels=rows,
        components=[dict(labels=[r['label']],source_net=r['source_net']) for r in rows])


class Tests(unittest.TestCase):
    def caps(self):
        return parse_caps('C1 P N 1f\nC2 P VSUBS 2f\nC3 N VSUBS 3f\nC4 PSEG VSUBS 4f\nC5 PSEG N 2f\nC6 CTX VSUBS 1f')
    def test_known_group_matrix(self):
        r=reduce_caps(self.caps(),provenance())
        self.assertAlmostEqual(r['P_ground_F']/1e-15,6.)
        self.assertAlmostEqual(r['N_ground_F']/1e-15,3.)
        self.assertAlmostEqual(r['mutual_F']/1e-15,3.)
        self.assertEqual(r['floating_charge_residual_F'],0.)
    def test_parallel_capacitors(self):
        r=reduce_caps(self.caps()+[('P','N',1e-15)],provenance())
        self.assertAlmostEqual(r['mutual_F']/1e-15,4.)
    def test_intrinsic_target_group_edge_cancels(self):
        a=reduce_caps(self.caps(),provenance());b=reduce_caps(self.caps()+[('P','PSEG',7e-15)],provenance())
        self.assertEqual(a['matrix_F'],b['matrix_F'])
    def test_retained_six_three_point_five_control(self):
        # Existing independent two-target-piece/floating-fill analytic coupon.
        pg,pf,p2f,fg=1.,2.,3.,5.
        self.assertEqual(pg+pf+p2f,6.)
        self.assertEqual(pg+(pf+p2f)*fg/(pf+p2f+fg),3.5)
    def test_continuation(self): self.assertAlmostEqual(parse_caps('C1 P N\n+ 3.5f')[0][2],3.5e-15)
    def test_bad_caps(self):
        for text in ('+ 1f','C1 P N -1f','C1 P P 1f','C1 P N 1e999','C1 P N 1f\nC1 P N 2f','R1 P N 1'):
            with self.subTest(text=text),self.assertRaises(ValueError):parse_caps(text)
    def test_missing_component(self):
        with self.assertRaises(AssertionError):reduce_caps(self.caps()[:-1],provenance())
    def test_unknown_component(self):
        with self.assertRaises(AssertionError):reduce_caps(self.caps()+[('OTHER','P',1e-15)],provenance())
    def test_foreign_alias(self):
        with self.assertRaises(AssertionError):reduce_caps([('P|N','VSUBS',1e-15)],provenance())
    def test_actual_fill_rejected(self):
        p=provenance();p['fill_count']=1
        with self.assertRaises(AssertionError):reduce_caps(self.caps(),p)
    def test_ac_finite_exact(self):self.assertEqual(ac_check('cp = 1e-15\ncn = -2e-15\nSENSE_FEED_AC_END\n',0,[1e-15,-2e-15])['status'],'passed')
    def test_ac_swapped_values(self):self.assertEqual(ac_check('cp = -2e-15\ncn = 1e-15\nSENSE_FEED_AC_END\n',0,[1e-15,-2e-15])['status'],'failed')
    def test_ac_fatal_exit_zero(self):self.assertEqual(ac_check('cp = 1e-15\ncn = -2e-15\nSENSE_FEED_AC_END\nError: failed\n',0,[1e-15,-2e-15])['status'],'failed')
    def test_ac_duplicate(self):self.assertEqual(ac_check('cp = 1e-15\ncp = 1e-15\ncn = -2e-15\nSENSE_FEED_AC_END\n',0,[1e-15,-2e-15])['status'],'failed')
    def test_ac_infinite(self):self.assertEqual(ac_check('cp = 1e999\ncn = -2e-15\nSENSE_FEED_AC_END\n',0,[1e-15,-2e-15])['status'],'failed')
    def test_context_equal(self):
        r=reduce_caps(self.caps(),provenance());self.assertEqual(context_check(r,r)['status'],'passed')
    def test_zero_denominator_not_waived(self):
        r=reduce_caps(self.caps(),provenance());r['mutual_F']=0.
        self.assertEqual(context_check(r,r)['status'],'failed')
    def test_one_percent_hard(self):
        r=reduce_caps(self.caps(),provenance());s=copy.deepcopy(r);s['P_ground_F']*=1.02
        self.assertEqual(context_check(s,r)['status'],'failed')


if __name__=='__main__':unittest.main()
