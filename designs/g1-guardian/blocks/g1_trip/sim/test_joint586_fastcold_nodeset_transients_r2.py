import unittest
from run_joint586_fastcold_nodeset_transients_r2 import error_lines
from run_joint586_fastcold_nodeset_transients import numerical_gate


class AbortGate(unittest.TestCase):
    def test_zero_exit_abort_even_with_end_marker(self):
        log = 'Using KLU as Direct Linear Solver\nSimulation: analysis aborted\nJOINT_POPULATION_TRAN_END'
        self.assertEqual(error_lines(log), ['Simulation: analysis aborted'])
        with self.assertRaises(AssertionError):
            numerical_gate(dict(status='completed', returncode=0), error_lines(log), log, 'klu')

    def test_no_duplicate_abort_error(self):
        self.assertEqual(error_lines('Error: analysis aborted'), ['Error: analysis aborted'])


if __name__ == '__main__':
    unittest.main()
