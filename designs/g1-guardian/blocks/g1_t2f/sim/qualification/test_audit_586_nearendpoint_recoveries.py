import unittest
from audit_586_nearendpoint_recoveries import checked_phase


class IndependentReceiptGate(unittest.TestCase):
    def setUp(self):
        self.state=dict(status='completed',returncode=0,timeout_s=900)
        self.log='Using SPARSE 1.3 as Direct Linear Solver\nPHASE0_BEGIN\nfinite phase\nPHASE0_END\n'

    def test_completed_exact_receipt(self):
        self.assertEqual(checked_phase(self.state,dict(self.state),self.log),'finite phase\n')

    def test_zero_exit_errors_rejected(self):
        for error in ['Error: no transient','Timestep too small','analysis aborted','doAnalyses: TRAN failed','no such vector']:
            with self.subTest(error=error),self.assertRaises(AssertionError):
                checked_phase(self.state,dict(self.state),self.log+error+'\n')

    def test_summary_pass_cannot_hide_timeout(self):
        state=dict(self.state,status='timeout')
        with self.assertRaises(AssertionError):checked_phase(state,state,self.log)

    def test_receipt_disagreement_rejected(self):
        with self.assertRaises(AssertionError):
            checked_phase(self.state,dict(self.state,returncode=1),self.log)

    def test_missing_or_duplicate_phase_rejected(self):
        for log in [self.log.replace('PHASE0_END','missing'),self.log+self.log]:
            with self.subTest(log=log),self.assertRaises(AssertionError):
                checked_phase(self.state,self.state,log)

    def test_solver_change_rejected(self):
        with self.assertRaises(AssertionError):
            checked_phase(self.state,self.state,self.log.replace('SPARSE 1.3','KLU'))


if __name__=='__main__':unittest.main()
