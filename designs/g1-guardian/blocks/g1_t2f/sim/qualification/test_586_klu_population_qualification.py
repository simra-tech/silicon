import json
import unittest
from prepare_586_klu_population_qualification import HERE,transform,exact_reuse
from prepare_586_klu_nominal_references import transform as nominal_transform
from audit_586_klu_population_qualification import numerical_gate

class QualificationGate(unittest.TestCase):
    def test_all18_original_input_transforms(self):
        packet=json.loads((HERE/'t2f586-klu-own6-preparation-20260923-a.json').read_text())
        self.assertEqual(len(packet['cases']),18)
        for case in packet['cases']:
            old=HERE/'runs'/case['original_run'];new=HERE/'runs'/case['run_id']
            exact_reuse(old,new)
            self.assertEqual((new/'probe.cir').read_text().replace('.options klu\n',''),(old/'probe.cir').read_text())
    def test_nominal_three_inverse(self):
        packet=json.loads((HERE/'t2f586-klu-nominal-references-20260923-b.json').read_text())
        self.assertEqual(len(packet['cases']),3)
        for case in packet['cases']:
            new=HERE/'runs'/case['run_id'];prep=json.loads((new/'preparation.json').read_text());old=HERE/'runs'/prep['original_run']
            self.assertEqual((new/'probe.cir').read_text(),nominal_transform((old/'probe.cir').read_text()))
            self.assertEqual(sum(map(len,prep['expected_full3180'].values())),3180)
    def test_zeroexit_error_rejected(self):
        r=dict(status='completed',returncode=0)
        with self.assertRaises(AssertionError):numerical_gate(r,dict(runtime=r,errors=[]),'Using KLU as Direct Linear Solver\nError: transient failed')
    def test_timeout_rejected(self):
        r=dict(status='timeout',returncode=0)
        with self.assertRaises(AssertionError):numerical_gate(r,dict(runtime=r,errors=[]),'Using KLU as Direct Linear Solver')
    def test_summary_runtime_mismatch_rejected(self):
        with self.assertRaises(AssertionError):numerical_gate(dict(status='completed',returncode=0),dict(runtime=dict(status='running'),errors=[]),'Using KLU as Direct Linear Solver')
    def test_analysis_error_rejected(self):
        r=dict(status='completed',returncode=0)
        with self.assertRaises(AssertionError):numerical_gate(r,dict(runtime=r,errors=[],analysis_error='late failure'),'Using KLU as Direct Linear Solver')

if __name__=='__main__':unittest.main()
