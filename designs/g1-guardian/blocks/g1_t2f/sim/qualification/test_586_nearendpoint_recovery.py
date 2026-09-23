import unittest
import numpy as np
from run_586_nearendpoint_recovery import numerical_gate,validate_wave

class RecoveryGate(unittest.TestCase):
    def fixture(self):
        a=np.zeros((2,13));a[1,0]=32e-6
        h=['time']+['v%d'%i for i in range(12)]
        return (' '.join(h)+'\n').encode(),a,h
    def test_finite_endpoint(self):
        self.assertEqual(validate_wave(*self.fixture()),0)
    def test_header_order(self):
        b,a,h=self.fixture();h[1],h[2]=h[2],h[1]
        with self.assertRaises(AssertionError):validate_wave(b,a,h)
    def test_short_endpoint(self):
        b,a,h=self.fixture();a[1,0]=31e-6
        with self.assertRaises(AssertionError):validate_wave(b,a,h)
    def test_nonfinite(self):
        b,a,h=self.fixture();a[1,1]=float('nan')
        with self.assertRaises(AssertionError):validate_wave(b,a,h)
    def test_vce_violation(self):
        b,a,h=self.fixture();a[1,7]=1.7
        with self.assertRaises(AssertionError):validate_wave(b,a,h)
    def test_error_exit_zero(self):
        with self.assertRaises(AssertionError):numerical_gate(dict(status='completed',returncode=0),['Error'],'Using SPARSE 1.3 as Direct Linear Solver')
    def test_klu_not_allowed(self):
        with self.assertRaises(AssertionError):numerical_gate(dict(status='completed',returncode=0),[],'Using KLU as Direct Linear Solver')

if __name__=='__main__':unittest.main()
