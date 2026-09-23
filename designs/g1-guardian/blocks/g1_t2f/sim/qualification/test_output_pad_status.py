"""Status-only controls; synthetic metadata is not an analog simulation."""
import unittest
from run_output_pad import combined_status

class OutputPadStatus(unittest.TestCase):
    def good(self):
        return dict(solver_exit=0,timed_out=False,numerical_status='passed',
                    output_function_status='passed')

    def test_complete_numerical_and_functional(self):
        self.assertEqual(combined_status(self.good()),'passed')

    def test_functional_failure_is_not_numerical_pass(self):
        r=self.good();r['output_function_status']='failed'
        self.assertEqual(combined_status(r),'failed')

    def test_missing_functional_check(self):
        r=self.good();del r['output_function_status']
        self.assertEqual(combined_status(r),'failed')

    def test_analysis_error_after_numerical_completion(self):
        r=self.good();r['analysis_error']=''
        self.assertEqual(combined_status(r),'failed')

    def test_nonzero_solver_exit(self):
        r=self.good();r['solver_exit']=1
        self.assertEqual(combined_status(r),'failed')

    def test_numerical_failure(self):
        r=self.good();r['numerical_status']='failed'
        self.assertEqual(combined_status(r),'failed')

    def test_timeout_is_not_run_to_completion(self):
        r=self.good();r.update(timed_out=True,solver_exit=None)
        self.assertEqual(combined_status(r),'not run')

    def test_empty_record_is_not_pass(self):
        self.assertEqual(combined_status({}),'failed')

if __name__=='__main__':
    unittest.main()
