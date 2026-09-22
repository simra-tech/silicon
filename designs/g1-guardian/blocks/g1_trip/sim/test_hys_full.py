#!/usr/bin/env python3
"""Small crossing/projection guards for the prospective HYS trace checker."""
import unittest
import numpy as np
from check_hys_full import crossings, project_numeric_row

class TraceTests(unittest.TestCase):
    def test_rising_interpolation(self):
        self.assertEqual(crossings(np.array([0.,2.]),np.array([0.,1.2])),[1.])
    def test_falling_interpolation(self):
        self.assertEqual(crossings(np.array([0.,2.]),np.array([1.2,0.]),False),[1.])
    def test_exact_threshold_counted_once(self):
        self.assertEqual(crossings(np.array([0.,1.,2.]),np.array([0.,.6,1.2])),[1.])
    def test_constant_no_false_edge(self):
        self.assertEqual(crossings(np.array([0.,1.]),np.array([.6,.6])),[])
    def test_projection_does_not_hide_original_value_change(self):
        a=np.arange(12,dtype=float).reshape(3,4)
        full=np.column_stack((a,np.array([100.,101.,102.])))
        self.assertTrue(np.array_equal(a,full[:,:-1]))
        full[1,2]=np.nextafter(full[1,2],np.inf)
        self.assertFalse(np.array_equal(a,full[:,:-1]))
    def test_projection_does_not_hide_time_change(self):
        a=np.arange(12,dtype=float).reshape(3,4)
        full=np.column_stack((a,np.array([100.,101.,102.])))
        full[1,0]=np.nextafter(full[1,0],np.inf)
        self.assertFalse(np.array_equal(a[:,0],full[:,0]))
    def test_exact_byte_projection(self):
        original=b' 0.000e+00  1.000e+00 \n'
        full=b' 0.000e+00  1.000e+00  2.000e+00 \n'
        self.assertEqual(project_numeric_row(full,2),original)
    def test_format_only_numeric_equivalent_change_rejected(self):
        original=b' 0.000e+00  1.000e+00 \n'
        full=b' 0.0000e+00  1.000e+00  2.000e+00 \n'
        projected=project_numeric_row(full,2)
        self.assertEqual(list(map(float,projected.split())),list(map(float,original.split())))
        self.assertNotEqual(projected,original)
    def test_line_ending_difference_not_normalized(self):
        original=b' 0.000e+00  1.000e+00 \n'
        full=b' 0.000e+00  1.000e+00  2.000e+00 \r\n'
        self.assertNotEqual(project_numeric_row(full,2),original)

if __name__=='__main__':unittest.main()
