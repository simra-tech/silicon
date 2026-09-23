import json
import unittest
import numpy as np
from run_586_startup_required import HERE,terminal_map,instrument,validate_wave


class StartupControls(unittest.TestCase):
    def test_native_terminals(self):
        source=(HERE/'runs/bgr_one_draw_20260922_r1/disabled/pex_nominal.spice').read_text()
        devices,nodes=terminal_map(source)
        self.assertEqual(sum(d['instance'].startswith('XQ')for d in devices),301)
        self.assertEqual(sum(d['instance'].startswith('XM')for d in devices),336)
        self.assertEqual(len(nodes),23)

    def test_readonly_instrument_all_six(self):
        q=json.loads((HERE/'runs/bgr_one_draw_20260922_r1/manifest.json').read_text())
        old=HERE/'runs/bgr_startup6_20260921_01'
        cases=json.loads((old/'manifest.json').read_text())['cases']
        for case in cases:
            deck=(old/(case['name']+'.cir')).read_text()
            changed=instrument(deck,q['parameters'],['vdd'])
            self.assertEqual(changed.split('tran ')[1].splitlines()[0],deck.split('tran ')[1].splitlines()[0])
            self.assertNotIn('\nop\n',changed)
            self.assertEqual(changed.count('\nprint @'),2842)

    def test_missing_uic_rejected(self):
        with self.assertRaises(AssertionError):instrument('tran 1n 1u\nquit\n',['p'+str(i)for i in range(2842)],[])

    def test_duplicate_inventory_rejected(self):
        with self.assertRaises(AssertionError):instrument('tran 1n 1u uic\nquit\n',['p']*2842,[])

    def test_wave_positive(self):
        validate_wave(np.array([[.1,1.],[.3,1.]]),['time','v(x)'],['time','v(x)'],.3)

    def test_wave_rejections(self):
        for data,header in [(np.array([[.1,1.],[.3,1.]]),['time','v(wrong)']),
                            (np.array([[.1,1.],[.1,1.]]),['time','v(x)']),
                            (np.array([[.1,1.],[.2,1.]]),['time','v(x)']),
                            (np.array([[.1,1.],[.3,np.nan]]),['time','v(x)'])]:
            with self.assertRaises(AssertionError):validate_wave(data,header,['time','v(x)'],.3)


if __name__=='__main__':unittest.main()
