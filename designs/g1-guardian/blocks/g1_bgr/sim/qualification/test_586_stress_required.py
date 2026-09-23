import json
import unittest
import numpy as np
from run_586_stress_required import HERE,instrument,validate


class StressControls(unittest.TestCase):
    def test_original_three_inverses(self):
        q=json.loads((HERE/'runs/bgr_one_draw_20260922_r1/manifest.json').read_text())
        for name in ('dip','r4','load'):
            text=(HERE/'runs/bgr_stress3_20260921_01'/(name+'.cir')).read_text()
            changed=instrument(text,q['parameters'],['vdd'])
            self.assertEqual(changed.count('\nprint @'),2842)
            self.assertEqual(changed.split('tran ')[1].splitlines()[0],'2n 40u')
            self.assertNotIn('\nop\n',changed)
    def test_missing_transient_rejected(self):
        with self.assertRaises(AssertionError):instrument('quit\n',['p'+str(i)for i in range(2842)],[])
    def test_duplicate_parameter_rejected(self):
        with self.assertRaises(AssertionError):instrument('tran 2n 40u\nquit\n',['p']*2842,[])
    def test_valid_wave(self):
        validate(np.array([[0.,1.],[40e-6,1.]]),['time','v(x)'],['time','v(x)'])
    def test_wrong_or_nonfinite_wave(self):
        for data,header in [(np.array([[0.,1.],[40e-6,1.]]),['time','v(wrong)']),
                            (np.array([[0.,1.],[0.,1.]]),['time','v(x)']),
                            (np.array([[0.,1.],[39e-6,1.]]),['time','v(x)']),
                            (np.array([[0.,1.],[40e-6,np.nan]]),['time','v(x)'])]:
            with self.assertRaises(AssertionError):validate(data,header,['time','v(x)'])


if __name__=='__main__':unittest.main()
