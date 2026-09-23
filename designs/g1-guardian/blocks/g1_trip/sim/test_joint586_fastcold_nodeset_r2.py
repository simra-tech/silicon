import unittest
from run_joint586_fastcold_nodeset_r2 import NODES,output_values,numerical_gate,baseline_comparison

class OutputGate(unittest.TestCase):
    def blob(self):return ('v-sweep '+' '.join('v('+n+')' for n in NODES)+'\n0 '+' '.join(['1']*8)+'\n').encode()
    def test_header_order_rejected(self):
        blob=self.blob().replace(b'v(vref) v(iptat)',b'v(iptat) v(vref)')
        with self.assertRaises(AssertionError):output_values(blob)
    def test_nonfinite_rejected(self):
        with self.assertRaises(AssertionError):output_values(self.blob().replace(b'0 1 ',b'0 nan '))
    def test_exit_zero_solver_error_rejected(self):
        with self.assertRaises(AssertionError):numerical_gate(dict(status='completed',returncode=0),['Error: OP failed'],'JOINT_NODESET_OP_END\nUsing KLU as Direct Linear Solver','klu')
    def test_timeout_rejected(self):
        with self.assertRaises(AssertionError):numerical_gate(dict(status='timeout',returncode=0),[],'JOINT_NODESET_OP_END\nUsing KLU as Direct Linear Solver','klu')
    def test_failed_baseline_rejected(self):
        with self.assertRaises(AssertionError):baseline_comparison(dict(status='failed'),self.blob(),output_values(self.blob()),self.blob())
    def test_pass_label_with_error_rejected(self):
        with self.assertRaises(AssertionError):baseline_comparison(dict(status='passed finite fullparameter OP diagnostic; exact comparisons separate',errors=[],analysis_error='late assertion'),self.blob(),output_values(self.blob()),self.blob())
    def test_exact_control(self):
        values=output_values(self.blob());base=dict(status='passed finite fullparameter OP diagnostic; exact comparisons separate',errors=[],op_nodes_V=values)
        self.assertTrue(baseline_comparison(base,self.blob(),values,self.blob())['baseline_data_bytes_exact'])

if __name__=='__main__':unittest.main()
