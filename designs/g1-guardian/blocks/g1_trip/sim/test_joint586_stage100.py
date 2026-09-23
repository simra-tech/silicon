import unittest
from audit_joint586_stage100 import terminal,classify_numerical_failure


class Stage100(unittest.TestCase):
    def test_failed_sample_is_terminal_not_dropped(self):
        self.assertTrue(terminal('failed calibration'))
        self.assertFalse(terminal('running'))
        self.assertFalse(terminal('paused before next leaf'))
    def test_only_original_bound_and_no_errors_classify_isolated(self):
        self.assertEqual(classify_numerical_failure({'status':'timeout','timeout_s':1200},{'errors':[]}),'isolated original1200s watchdog')
        self.assertTrue(classify_numerical_failure({'status':'timeout','timeout_s':2400},{'errors':[]}).startswith('blocked'))
        self.assertTrue(classify_numerical_failure({'status':'timeout','timeout_s':1200},{'errors':['no such vector']}).startswith('blocked'))


if __name__=='__main__':unittest.main()
