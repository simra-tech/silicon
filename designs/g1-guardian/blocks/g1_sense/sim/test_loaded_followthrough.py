#!/usr/bin/env python3
"""Fail-closed preparation controls for adverse AC and loaded steps."""
import json
from pathlib import Path
import tempfile
import unittest
from run_loaded_followthrough import (get_reference,adverse_deck,step_deck,TRAN,errors)
from run_loaded_noise_audit import table

class Controls(unittest.TestCase):
    def test_both_adverse_anchors_and_bases(self):
        for case in ['slow','fast']:
            run,ref,prep,expected,op=get_reference('adverse',case)
            self.assertEqual(len(expected),11512);self.assertEqual(len(op),9)
            original=(ref/'population_transient.cir').read_text()
            for mode in ['differential','tian_voltage','tian_current']:
                d=adverse_deck(original,Path('/tmp/qualified-output'),mode,run,prep['groups'])
                self.assertEqual(d.count('\nop\n'),1);self.assertNotIn(TRAN,d)
                self.assertEqual(d.count('ac dec 100 1 1g'),1)
                if mode=='differential':
                    self.assertIn('Vsh shp 0 dc 0.012500000000000001 ac .5',d)
                    self.assertIn('Vshn shn 0 dc -0.012500000000000001 ac -.5',d)
                else:self.assertIn('.param pv=%d pi=%d'%(mode=='tian_voltage',mode=='tian_current'),d)
    def test_nominal_step_and_dc(self):
        run,ref,prep,expected,op=get_reference('settling','rise')
        original=(ref/'population_transient.cir').read_text()
        for target in [0.,.05]:
            step=step_deck(original,Path('/tmp/qualified-output'),'step',target,prep['groups'])
            dc=step_deck(original,Path('/tmp/qualified-output'),'dc',target,prep['groups'])
            self.assertEqual(step.count(TRAN),1);self.assertNotIn(TRAN,dc)
            self.assertEqual(step.split('.control')[0].count('PWL('),1)
            self.assertIn('Vsh shp 0 dc 0.025000000000000001 PWL(0 .025 200n .025 201n ',step)
            self.assertEqual(step.count('echo LEGACY27_AFTER_BEGIN'),1)
            self.assertEqual(dc.count('echo LEGACY27_AFTER_BEGIN'),1)
            # All original numerical option and canonical source lines remain.
            for line in original.splitlines():
                if line.startswith(('.option','.include','.lib','.temp','Vclk')):
                    self.assertIn(line,step);self.assertIn(line,dc)
    def test_missing_input_rejected(self):
        run,ref,prep,expected,op=get_reference('settling','rise')
        original=(ref/'population_transient.cir').read_text().replace('Vsh shp 0 dc 0.025000000000000001','* wrong input')
        with self.assertRaises(AssertionError):step_deck(original,Path('/tmp/out'),'step',.05,prep['groups'])
    def test_fatal_log_rejected_independent_exit(self):
        for line in ['Fatal: rejected','Error: bad','Warning from checkvalid: vector x not available','doAnalyses: failed']:
            self.assertTrue(errors(line))
        self.assertFalse(errors('WARNING: V(i2,c) voltage is greater than specified by vmax'))
    def test_header_nonfinite_and_order_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'data'
            p.write_text('time a b\n0 1 2\n1 3 4\n');table(p,['time','a','b'])
            with self.assertRaises(AssertionError):table(p,['time','b','a'])
            p.write_text('time a b\n0 1 2\n1 nan 4\n')
            with self.assertRaises(AssertionError):table(p,['time','a','b'])
            p.write_text('time a b\n1 1 2\n0 3 4\n')
            with self.assertRaises(AssertionError):table(p,['time','a','b'])

if __name__=='__main__':unittest.main()
