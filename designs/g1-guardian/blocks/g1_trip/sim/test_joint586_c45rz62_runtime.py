import copy
import json
import unittest
from unittest.mock import patch
from run_joint586_c45rz62_anchors import SIM,CAP,candidate_parameter_gate,source_and_input_gate
from c45rz62_native_scale import scale_interval


class Tests(unittest.TestCase):
    def setUp(self):
        self.out=SIM/'qualification/joint586-c45rz62-s73001-p00-original-step-20260923-a'
        self.prep=json.loads((self.out/'preparation.json').read_text())
        self.parameters=dict(parameters_before=self.prep['expected_candidate_parameters'],parameters_after=self.prep['expected_candidate_parameters'],legacy27=self.prep['expected_legacy27'])
    def test_exact_bound_source(self):source_and_input_gate(self.out,self.prep)
    def test_wrong_source_hash_and_step_rejected(self):
        for key,value in [('tmax','1n'),('seed',73002)]:
            prep=copy.deepcopy(self.prep);prep[key]=value
            with self.assertRaises(AssertionError):source_and_input_gate(self.out,prep)
        prep=copy.deepcopy(self.prep);prep['source_hashes']['sense.spice']='0'*64
        with self.assertRaises(AssertionError):source_and_input_gate(self.out,prep)
    def test_native_area_law_and_unchanged11511(self):
        with patch('run_joint586_c45rz62_anchors.phase_parameters',return_value=self.parameters):candidate_parameter_gate('',self.prep)
        bad=copy.deepcopy(self.parameters);index=next(i for i,r in enumerate(bad['parameters_before']) if r[0]!=CAP);bad['parameters_before'][index][1]='999'
        with patch('run_joint586_c45rz62_anchors.phase_parameters',return_value=bad):
            with self.assertRaises(AssertionError):candidate_parameter_gate('',self.prep)
    def test_wrong_cap_scale_rejected(self):
        old=dict(self.prep['expected_old_parameters'])[CAP]
        self.assertEqual(scale_interval(old,'1.123456','45')['status'],'failed')
        bad=copy.deepcopy(self.parameters);next(r for r in bad['parameters_before'] if r[0]==CAP)[1]='1.123456'
        with patch('run_joint586_c45rz62_anchors.phase_parameters',return_value=bad):
            with self.assertRaises(AssertionError):candidate_parameter_gate('',self.prep)


if __name__=='__main__':unittest.main()
