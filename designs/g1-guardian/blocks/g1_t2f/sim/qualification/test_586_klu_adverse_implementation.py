import unittest
from run_586_klu_adverse_first_sample import numerical_gate, errors_in, header_for
from audit_586_klu_adverse_first_sample import receipt_gate
from prepare_586_klu_adverse_first_sample import HERE


class FailureGates(unittest.TestCase):
    def test_zero_exit_abort(self):
        log = 'Using KLU as Direct Linear Solver\nanalysis aborted\nPHASE0_END'
        with self.assertRaises(AssertionError):
            numerical_gate(dict(status='completed',returncode=0),log)

    def test_timeout_and_sparse_rejected(self):
        for state, log in [(dict(status='timeout',returncode=0),'Using KLU as Direct Linear Solver\nPHASE0_END'),
                (dict(status='completed',returncode=0),'Using SPARSE 1.3 as Direct Linear Solver\nPHASE0_END')]:
            with self.assertRaises(AssertionError):
                numerical_gate(state,log)

    def test_missing_endpoint_marker(self):
        with self.assertRaises(AssertionError):
            numerical_gate(dict(status='completed',returncode=0),'Using KLU as Direct Linear Solver')

    def test_pass_label_cannot_hide_timeout(self):
        state=dict(status='timeout',returncode=0)
        with self.assertRaises(AssertionError):
            receipt_gate(state,dict(runtime=state,status='passed',errors=[]),dict(status='passed'))

    def test_pass_label_cannot_hide_analysis_error(self):
        state=dict(status='completed',returncode=0)
        with self.assertRaises(AssertionError):
            receipt_gate(state,dict(runtime=state,status='passed',errors=[],analysis_error='late'),dict(status='passed'))

    def test_exact_named_header(self):
        header=header_for((HERE/'t2f586-klu-fast-firstsample-contract-20260923-a/cal25.cir').read_text())
        self.assertEqual(header[:5],['time','v(fout)','v(vref)','i(vdd)','i(vdd12)'])
        self.assertEqual(len(header),13)


if __name__=='__main__':
    unittest.main()
