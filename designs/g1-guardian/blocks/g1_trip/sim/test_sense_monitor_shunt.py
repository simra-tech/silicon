import unittest
import numpy as np
from sense_monitor_shunt_op import account, transform
from sense_accounted_current_tran import accounting


class ShuntTests(unittest.TestCase):
    def test_boundary_accounting(self):
        branches = np.array([.001, .0002, .0003])
        currents = np.array([[0, branches.sum()+3.3e-12]+branches.tolist()])
        result = account(currents, np.array([[0, 3.3, 3.3, 3.3, 3.3]]))
        self.assertEqual(result['raw_1pA_status'], 'failed')
        self.assertEqual(result['accounted_1pA_status'], 'passed')
        self.assertAlmostEqual(result['total_added_shunt_current_A'], 13.2e-12, places=20)

    def test_wrong_voltage_does_not_pass(self):
        currents = np.array([[0, .0015000000033, .001, .0002, .0003]])
        result = account(currents, np.array([[0, 0, 3.3, 3.3, 3.3]]))
        self.assertEqual(result['accounted_1pA_status'], 'failed')

    def test_output_only(self):
        old = '.option rshunt=1e12 gmin=1e-13\n.save v(a)\nop\nwrdata qualification/old/op0.dat v(a)\necho POPULATION_OP_END\n'
        new = transform(old, 'old', 'new')
        self.assertEqual(new.count('\nop\n'), 1)
        self.assertIn('wrdata qualification/new/op0.dat v(a)\n', new)
        self.assertIn('v(xs.vdd_ref_monitor)', new)

    def test_wrong_rshunt_fails(self):
        with self.assertRaises(AssertionError):
            transform('.option rshunt=1e13\n.save v(a)\necho POPULATION_OP_END\n', 'old', 'new')

    def test_transient_accounting_and_grid(self):
        currents = np.array([[0, .0015000000033, .001, .0002, .0003],
                             [1.02e-6, .0015000000033, .001, .0002, .0003]])
        volts = np.array([[0, 3.3, 3.3, 3.3, 3.3], [1.02e-6, 3.3, 3.3, 3.3, 3.3]])
        result = accounting(currents, volts)
        self.assertEqual(result['raw_1pA_status'], 'failed')
        self.assertEqual(result['accounted_1pA_status'], 'passed')
        volts[1, 0] = 1e-6
        with self.assertRaises(AssertionError):
            accounting(currents, volts)


if __name__ == '__main__':
    unittest.main()
