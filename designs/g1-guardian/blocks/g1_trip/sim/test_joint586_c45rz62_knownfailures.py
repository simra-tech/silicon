import copy
import json
import re
import unittest
import numpy as np
from run_joint586_c45rz62_knownfailures import SIM,CAP,vector_gate,input_observation,read_group,phase_parameters
from prepare_joint586_c45rz62_known_failures import transform
from prepare_joint586_tmax_probe import OLD


class Tests(unittest.TestCase):
    def setUp(self):
        self.out=SIM/'qualification/joint586-c45rz62-s73001-p00-original-step-20260923-a'
        self.prep=json.loads((self.out/'preparation.json').read_text());self.before=self.prep['expected_candidate_parameters'];self.old=self.prep['expected_old_parameters'];self.legacy=self.prep['expected_legacy27']
    def test_vector_gate_actual_candidate_and_wrong_changes(self):
        vector_gate(self.before,self.before,self.old,self.legacy,self.legacy)
        bad=copy.deepcopy(self.before);next(r for r in bad if r[0]!=CAP)[1]='999'
        with self.assertRaises(AssertionError):vector_gate(bad,bad,self.old,self.legacy,self.legacy)
        with self.assertRaises(AssertionError):vector_gate(self.before,bad,self.old,self.legacy,self.legacy)
        bad=copy.deepcopy(self.before);next(r for r in bad if r[0]==CAP)[1]='1.123456'
        with self.assertRaises(AssertionError):vector_gate(bad,bad,self.old,self.legacy,self.legacy)
    def test_exact_original_method_inverse_and_wrong_step(self):
        original='.include qualification/parent/sense.spice\n.nodeset v(a)=.7\nsetseed 78101\n'+OLD+'wrdata qualification/parent/p57/phase0.dat v(a)\n'
        changed=transform(original,'parent','p57','new',78101)
        self.assertEqual(changed.replace('qualification/new/sense.spice','qualification/parent/sense.spice').replace('qualification/new/phase0.dat','qualification/parent/p57/phase0.dat'),original)
        with self.assertRaises(AssertionError):transform(original.replace(OLD,OLD.replace('0.2n\n','1n\n')),'parent','p57','new',78101)
        with self.assertRaises(AssertionError):transform(original,'parent','p57','new',78001)
    def test_actual_shn_and_mean_required(self):
        data=np.zeros((2,19));data[:,17]=.01275;data[:,18]=-.01275
        prep=dict(wave_header=list(range(19)),condition=['low_cold_cm0',-40,3.,1.08,0.],shunt_V=.0255)
        input_observation(data,prep);data[:,18]=0
        with self.assertRaises(AssertionError):input_observation(data,prep)
        with self.assertRaises(AssertionError):input_observation(data[:,:18],prep)
    def test_original_trans_legacy_parser_actual_log(self):
        log=(self.out/'run.log').read_text();section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
        groups=self.prep['groups'];before=read_group(section,'NON_BGR_BEFORE',groups['NON_BGR'])+read_group(section,'BGR_BEFORE',groups['BGR'])
        parsed=phase_parameters(section,groups,before);self.assertEqual(parsed['legacy27'],self.legacy)
        vector_gate(before,parsed['parameters_after'],self.old,parsed['legacy27'],self.legacy)


if __name__=='__main__':unittest.main()
