#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[4]
SPEC=importlib.util.spec_from_file_location('pdn',ROOT/'flow/update_pdn_metrics.py');M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)
class PDNStatus(unittest.TestCase):
    def test_actual_log_overrides_prior_zero(self):
        log=(ROOT/'designs/g1-guardian/blocks/g1_padring/flow/runs/assembly-1350/22-openroad-generatepdn/analog_straps.log').read_text()
        state=M.update_metrics({'metrics':{'design__power_grid_violation__count__net:VDDA':0}},log)['metrics']
        self.assertEqual(state['design__power_grid_violation__count'],1)
        for net in ['VDD','VSS']:self.assertEqual(state['design__power_grid_violation__count__net:'+net],0)
        self.assertEqual(state['design__power_grid_violation__count__net:VDDA'],1)
    def test_missing_or_incomplete_cannot_pass(self):
        with self.assertRaises(ValueError):M.update_metrics({'metrics':{}},'')
        state=M.update_metrics({'metrics':{}},'check_power_grid -net VDDA')['metrics']
        self.assertEqual(state['design__power_grid_violation__count'],1)
    def test_raw_failure_overrides_pass(self):
        log='check_power_grid -net VDDA\nAll shapes on net VDDA are connected\nCheck connectivity failed on VDDA'
        self.assertEqual(M.update_metrics({'metrics':{}},log)['metrics']['design__power_grid_violation__count'],1)
if __name__=='__main__':unittest.main()
