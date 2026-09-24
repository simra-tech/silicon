import unittest
from dac586_dc_metrics import actual_bits,transfer_bounds,interval_divide


class MetricsTests(unittest.TestCase):
    def test_all_code_actual_bits(self):
        for code in range(256):self.assertTrue(actual_bits([1.2*((c>>i)&1) for c in [code,255-code] for i in range(8)],code,255-code))

    def test_nonexact_bit_does_not_pass(self):
        bits=[0.]*16;bits[0]=1e-18;self.assertFalse(actual_bits(bits,0,0))

    def test_nominal_and_near_zero_step(self):
        values=[i*.002 for i in range(256)];self.assertTrue(transfer_bounds(values)['status'].startswith('passed'))
        values[128]=values[127]+1e-7;result=transfer_bounds(values)
        self.assertEqual(result['steps'][127]['status'],'requires original-static refinement')
        self.assertLessEqual(result['steps'][127]['DNL_LSB'][0],-1)

    def test_negative_numerator_interval(self):
        self.assertEqual(interval_divide([-2,-1],[1,2]),[-2,-.5])

    def test_invalid_missing_or_nan_refused(self):
        with self.assertRaises(AssertionError):transfer_bounds([0.]*255)
        with self.assertRaises(AssertionError):transfer_bounds([float('nan')]*256)
        with self.assertRaises(AssertionError):interval_divide([0,1],[0,1])


if __name__=='__main__':unittest.main()
