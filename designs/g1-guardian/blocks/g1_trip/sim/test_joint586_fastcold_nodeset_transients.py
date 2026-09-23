import unittest
from prepare_joint586_fastcold_nodeset_transients import ORIGINAL, guesses, transform
from run_joint586_fastcold_nodeset_transients import numerical_gate, validate_header, error_lines


class ContractTests(unittest.TestCase):
    def test_exact_inverse_both_arms(self):
        original = (ORIGINAL/'population_transient.cir').read_text()
        values = guesses((ORIGINAL/'run.log').read_text())
        for solver in ['sparse', 'klu']:
            deck, audit = transform(original, 'test-'+solver, solver, values)
            self.assertTrue(audit['exact_inverse_restores_original'])
            self.assertEqual([l for l in deck.splitlines() if l.startswith(('tran ', 'meas tran '))],
                [l for l in original.splitlines() if l.startswith(('tran ', 'meas tran '))])
            self.assertEqual(deck.count('.nodeset '), 1)
            self.assertEqual(deck.count('.options klu'), int(solver == 'klu'))

    def test_original_mismatch_rejected(self):
        original = (ORIGINAL/'population_transient.cir').read_text()
        with self.assertRaises(AssertionError):
            transform(original.replace('setseed 78001', 'setseed 78002'), 'test', 'sparse', guesses((ORIGINAL/'run.log').read_text()))

    def test_zero_exit_solver_error(self):
        log = 'Using KLU as Direct Linear Solver\nError: timestep too small\nJOINT_POPULATION_TRAN_END'
        with self.assertRaises(AssertionError):
            numerical_gate(dict(status='completed', returncode=0), error_lines(log), log, 'klu')

    def test_timeout_and_wrong_solver(self):
        log = 'Using KLU as Direct Linear Solver\nJOINT_POPULATION_TRAN_END'
        for state, solver in [(dict(status='timeout', returncode=0), 'klu'), (dict(status='completed', returncode=0), 'sparse')]:
            with self.assertRaises(AssertionError):
                numerical_gate(state, [], log, solver)

    def test_header_order_and_scale(self):
        deck = (ORIGINAL/'population_transient.cir').read_text()
        line, = [l for l in deck.splitlines() if l.startswith('wrdata ')]
        header = 'time '+' '.join(line.split()[2:])+'\n'
        validate_header(header.encode(), deck)
        for wrong in [header.replace('time', 'v-sweep'), header.replace('v(clk) v(xt.icmp)', 'v(xt.icmp) v(clk)')]:
            with self.assertRaises(AssertionError):
                validate_header(wrong.encode(), deck)


if __name__ == '__main__':
    unittest.main()
