import copy
import json
import unittest
from run_regenpair4_diagnostic import SIM
from soft_regenpair4 import trip_transform,hard_transform,parameter_gate


class Controls(unittest.TestCase):
    def test_only_soft_regenerative_call_changes(self):
        text=(SIM/'qualification/joint586-calibration-s73133-20260922-a/trip.spice').read_text()
        old=hard_transform(text);new=trip_transform(text)
        self.assertEqual(new.replace('XCS icmp vth_soft cmp_clk cmp_soft cmp_soft_n vdd vss g1_cmp_regenpair4','XCS icmp vth_soft cmp_clk cmp_soft cmp_soft_n vdd vss g1_cmp'),old)
        self.assertIn('XM1 xp inp tail vss sg13_lv_nmos w=12u l=0.34u',new)
        with self.assertRaises(AssertionError):trip_transform(new)

    def test_seventeen_declared_laws_and_wrong_draw_rejected(self):
        old=json.loads((SIM/'qualification/joint586-calibration-s73133-20260922-a/p00/summary.json').read_text())['parameter_audit']
        hard=json.loads((SIM/'qualification/joint586-regenpair4-r100-roomcal-s73133-20260923-b/c00/summary.json').read_text())['parameter_audit']
        b=copy.deepcopy(hard['parameters_before'])
        for row in b:
            if any(row[0].startswith('@n.xt.xcs.'+x+'.') for x in ['xm3','xm4']):
                x=float(row[1])
                for kind in ['w','l','delvto','factuo']:
                    if row[0].endswith('['+kind+']'):
                        x=x+(3e-6 if kind=='w' else .13e-6) if kind in ['w','l'] else x/2 if kind=='delvto' else 1+(x-1)/2
                        row[1]=format(x,'.16e')
        _,laws=parameter_gate(b,b,old['parameters_before'],old['legacy27'],old['legacy27']);self.assertEqual(len(laws),17)
        for key in ['@n.xt.xcs.xm1.nsg13_lv_nmos[w]','@n.xt.xcs.xm3.nsg13_lv_nmos[delvto]']:
            changed=copy.deepcopy(b)
            for r in changed:
                if r[0]==key:r[1]=str(float(r[1])*1.01)
            with self.assertRaises(AssertionError):parameter_gate(changed,changed,old['parameters_before'],old['legacy27'],old['legacy27'])


if __name__=='__main__':unittest.main()
