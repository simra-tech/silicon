import unittest
from analyze_bgr_substitution_outcomes import warning_inventory


class WarningInventoryTests(unittest.TestCase):
    def test_instance_nan_is_not_nonfinite_warning(self):
        result = warning_inventory('@n.xt.xcs.xmnan1.nsg13_lv_nmos[w] = 1.49e-6\n')
        self.assertEqual(result['count'], 0)
        self.assertEqual(result['retained_runner_nan_substring_false_positives'], 1)

    def test_real_nan_retained(self):
        result = warning_inventory('The temperature limiting function received NaN.\n')
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['hierarchy_counts'], {'unclassified': 1})

    def test_warning_hierarchy_and_progress(self):
        result = warning_inventory('Reference value : 2e-8\nOSDI(debug) n.xbgr.xr21.nr1: WARNING: V(i2,c) voltage is greater than specified by vmax\n')
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['hierarchy_counts'], {'xbgr': 1})
        self.assertEqual(list(result['first_preceding_progress_time_s'].values()), [2e-8])


if __name__ == '__main__':
    unittest.main()
