import unittest
import numpy as np
from analyze_regenpair4_timing import persistent_crossing


class Controls(unittest.TestCase):
    def test_linear_crossing(self):
        d=persistent_crossing(np.array([0.,1.,2.]),np.array([0.,1.,1.]),0.,2.,.9)
        self.assertAlmostEqual(d['time_s'],.9)

    def test_glitch_not_accepted(self):
        d=persistent_crossing(np.array([0.,1.,2.,3.,4.]),np.array([0.,1.,0.,1.,1.]),0.,4.,.9)
        self.assertAlmostEqual(d['time_s'],2.9)

    def test_final_unresolved(self):
        d=persistent_crossing(np.array([0.,1.,2.]),np.array([0.,1.,.1]),0.,2.,.9)
        self.assertIn('not reached',d['status'])


if __name__=='__main__':unittest.main()
