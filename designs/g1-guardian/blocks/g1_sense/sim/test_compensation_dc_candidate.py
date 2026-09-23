#!/usr/bin/env python3
"""Fail-closed controls for the separately declared cross-source DC gate."""
import unittest
from qualify_compensation_dc_candidate import bounded_dc,OBS


class Controls(unittest.TestCase):
    def setUp(self):
        self.quiet={'q'+str(i):0. for i in range(9)}
        self.obs={n:0. for n in OBS}

    def test_exact_and_both_signed_bounds(self):
        self.assertTrue(bounded_dc(self.quiet,self.obs,self.quiet,self.obs)['exact_quiet_equality'])
        for sign in [-1,1]:
            quiet=dict(self.quiet,q0=sign*1e-6)
            obs={n:sign*(1e-9 if n.startswith('i(') else 1e-6) for n in OBS}
            self.assertFalse(bounded_dc(quiet,obs,self.quiet,self.obs)['exact_quiet_equality'])

    def test_reject_voltage_current_nonfinite_and_wrong_names(self):
        for value in [1.000001e-6,-1.000001e-6,float('nan'),float('inf')]:
            with self.assertRaises(AssertionError):bounded_dc(dict(self.quiet,q0=value),self.obs,self.quiet,self.obs)
        for value in [1.000001e-9,-1.000001e-9,float('nan')]:
            with self.assertRaises(AssertionError):bounded_dc(self.quiet,dict(self.obs,**{'i(vdda)':value}),self.quiet,self.obs)
        bad=dict(self.quiet);bad['wrong']=bad.pop('q0')
        with self.assertRaises(AssertionError):bounded_dc(bad,self.obs,self.quiet,self.obs)


if __name__=='__main__':unittest.main()
