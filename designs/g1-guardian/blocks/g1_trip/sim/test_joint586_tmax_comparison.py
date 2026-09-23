"""Supplemental negative controls against the unchanged hash-bound comparison helper."""
import copy
import unittest
import numpy as np
from compare_joint586_tmax_probe import compare


class Tests(unittest.TestCase):
    def setup_case(self):
        wave=np.zeros((4,18));wave[:,0]=[0,1e-7,3e-7,1.02e-6];wave[:,13]=1
        analysis=dict(actual_clock_rising_crossings_s={k:[2e-7] for k in ['soft','hard']},comparators={k:dict(measured_edge_decision=True,legacy_phase_decision=True,sampling_policies_agree=True) for k in ['soft','hard']})
        bounds=dict(clock_output_event_shift_s=2e-10,event_bracket_width_s=2e-10,quiet_decision_analog_abs_V=1e-4,wholewave_analog_abs_V=1e-3,wholewave_other_abs_V=.05)
        return wave,analysis,bounds
    def test_identical_control(self):
        wave,a,b=self.setup_case();self.assertTrue(all(compare(wave,wave.copy(),list(map(str,range(18))),a,copy.deepcopy(a),b)['checks'].values()))
    def test_decision_flip_rejected(self):
        wave,a,b=self.setup_case();other=copy.deepcopy(a);other['comparators']['hard']['measured_edge_decision']=False
        self.assertFalse(compare(wave,wave.copy(),list(map(str,range(18))),a,other,b)['checks']['same_original_actual_and_legacy_decisions'])
    def test_analog_shift_rejected(self):
        wave,a,b=self.setup_case();other=wave.copy();other[:,13]+=.0002
        self.assertFalse(compare(wave,other,list(map(str,range(18))),a,a,b)['checks']['quiet_decision_analog_consistency'])
    def test_extra_crossing_rejected(self):
        wave,a,b=self.setup_case();other=wave.copy();other[1:,1]=1.2
        self.assertFalse(compare(wave,other,list(map(str,range(18))),a,a,b)['checks']['event_counts_times_resolution'])
    def test_wholewave_internal_excursion_rejected(self):
        wave,a,b=self.setup_case();other=wave.copy();other[1,9]=.06
        self.assertFalse(compare(wave,other,list(map(str,range(18))),a,a,b)['checks']['wholewave_consistency'])
    def test_nonfinite_rejected(self):
        wave,a,b=self.setup_case();other=wave.copy();other[1,9]=float('nan')
        with self.assertRaises(AssertionError):compare(wave,other,list(map(str,range(18))),a,a,b)


if __name__=='__main__':unittest.main()
