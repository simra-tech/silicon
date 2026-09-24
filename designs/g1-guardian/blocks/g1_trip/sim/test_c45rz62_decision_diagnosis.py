import copy
import unittest
from analyze_c45rz62_knownfailure_decisions import extract, DELAYS


class Controls(unittest.TestCase):
    def fixture(self):
        return dict(sampling_status='passed', hard_early_evaluation=[dict(samples=[dict(
            delay_after_measured_edge_ns=d, actual_hard_clock_V=0., hard_differential_V=.001*j,
            hard_output_V=float(j), hard_frontend_xp_xq_xn_yn_V=[j]*4) for d in DELAYS]) for j in range(5)],
            comparators=dict(hard=dict(sampling_policies_agree=True),soft={}), actual_clock_rising_crossings_s={})

    def test_last_three_not_first_three(self):
        d=extract(self.fixture()); self.assertEqual(d['early_last_three'][0]['hard_output_V']['cycles'],[2.,3.,4.])

    def test_missing_edge_rejected(self):
        d=self.fixture();d['hard_early_evaluation'].pop()
        with self.assertRaises(AssertionError):extract(d)

    def test_changed_sampling_rejected(self):
        d=self.fixture();d['comparators']['hard']['sampling_policies_agree']=False
        with self.assertRaises(AssertionError):extract(d)

    def test_wrong_delay_rejected(self):
        d=self.fixture();d['hard_early_evaluation'][0]['samples'][0]['delay_after_measured_edge_ns']=99
        with self.assertRaises(AssertionError):extract(d)


if __name__=='__main__':unittest.main()
