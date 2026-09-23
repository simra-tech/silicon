#!/usr/bin/env python3
"""Source transformation and stimulus-basis controls; no analog execution."""
import unittest
from fractions import Fraction
from pathlib import Path
from run_loaded_ac_audit import MODES, TRIP, REFERENCE, make_deck, source_probe
import json

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ref=TRIP/'qualification'/REFERENCE
        cls.source=(ref/'sense.spice').read_text()
        cls.deck=(ref/'population_transient.cir').read_text()
        cls.groups=json.loads((ref/'preparation.json').read_text())['groups']
    def test_exact_probe_inverse(self):
        changed=source_probe(self.source)
        old='XOTA vp vn iptat isense vdd vss g1_ota_main_candidate'
        new=old.replace('vp vn','vp main_loop_e')
        added='Vmain_probe main_loop_e vn dc 0 ac {pv}\nImain_probe vss main_loop_e dc 0 ac {pi}\n'
        self.assertEqual(changed.replace(added,'').replace(new,old),self.source)
    def test_wrong_source_rejected(self):
        with self.assertRaises(AssertionError):source_probe(self.source.replace('XOTA vp vn','XOTA vp wrong'))
    def test_every_mode_preserves_OP_parameter_queries(self):
        old=self.deck.split('.control\n',1)[1].split('tran 0.2n 1.02u 0 0.2n\n')[0]
        for mode in MODES:
            d=make_deck(self.deck,Path('/tmp/unique-ac-control'),mode,self.groups)
            controls=d.split('.control\n',1)[1]
            from run_loaded_ac_audit import OBS
            saved='save '+' '.join(OBS)+(' v(xs.main_loop_e) i(v.xs.vmain_probe)' if mode.startswith('tian_') else '')+'\n'
            self.assertEqual(controls.replace(saved,'',1)[:len(old)],old)
            self.assertEqual(d.count('\nop\n'),1)
            self.assertEqual(d.count('ac dec 100 1 1g'),1)
            self.assertNotIn('\ntran ',d)
    def test_DC_zero_common_fixture(self):
        for mode in ['differential','common']:
            d=make_deck(self.deck,Path('/tmp/unique-ac-control'),mode,self.groups)
            self.assertIn('Vcm_measure noise_cm 0 dc 0 ac ',d)
            self.assertIn('XS shp noise_cm vref iptat isense vped vref_buf vdda 0 g1_sense',d)
    def test_exact_stimulus_basis(self):
        d=(Fraction(1,2),Fraction(-1,2));c=(Fraction(1),Fraction(1))
        self.assertEqual(d[0]-d[1],1);self.assertEqual(sum(d),0)
        self.assertEqual(c[0]-c[1],0);self.assertEqual(sum(c)/2,1)
        self.assertEqual(tuple(d[i]+c[i]/2 for i in [0,1]),(1,0))
    def test_other_sources_have_no_ac_drive(self):
        for mode,target in [('psrr_vdda','Vdda vdda 0 dc {VDDA} ac 1'),('psrr_vdd','Vdd vdd 0 dc {VDD} ac 1')]:
            d=make_deck(self.deck,Path('/tmp/unique-ac-control'),mode,self.groups).split('.control')[0]
            self.assertEqual([line for line in d.splitlines() if ' ac ' in line],[target])

if __name__=='__main__':unittest.main()
