import json
import unittest
from prepare_joint586_fast_nodeset_rescue import SIM,ORIGINAL,LABELS,FIXTURES,REUSE,guesses,transform
from run_joint586_fast_nodeset_rescue import numerical_gate


class RescueContract(unittest.TestCase):
    def test_all_fourteen_exact_inverse_and_bounds(self):
        values=guesses((ORIGINAL/'run.log').read_text())
        paths=[SIM/'qualification'/('joint586-fast-transqual-shn-20260923-b-'+label) for label in LABELS]
        paths += [SIM/'qualification'/('joint586-fast-fixture-controls-20260923-b-'+label) for label in FIXTURES]
        self.assertEqual(len(paths),14)
        added=set()
        for old in paths:
            prep=json.loads((old/'preparation.json').read_text());body=(old/'population_transient.cir').read_text()
            deck,audit=transform(body,old.name,'test-new-run',values);added.add(audit['fixed_nodeset'])
            self.assertTrue(audit['exact_inverse'])
            self.assertEqual([l for l in deck.splitlines() if l.startswith(('.include','tran ','meas tran ','setseed '))],
                [l for l in body.splitlines() if l.startswith(('.include','tran ','meas tran ','setseed '))])
            self.assertIn(prep['watchdog_s'],[1200,4800])
        self.assertEqual(len(added),1)

    def test_completed_lowcold_reuse_exact(self):
        body=(ORIGINAL/'population_transient.cir').read_text()
        deck,_=transform(body,ORIGINAL.name,REUSE,guesses((ORIGINAL/'run.log').read_text()))
        self.assertEqual(deck,(SIM/'qualification'/REUSE/'population_transient.cir').read_text())

    def test_double_nodeset_rejected(self):
        with self.assertRaises(AssertionError):
            transform('.nodeset v(x)=1\n.control\n','old','new',guesses((ORIGINAL/'run.log').read_text()))

    def test_exit_zero_abort_rejected(self):
        with self.assertRaises(AssertionError):
            numerical_gate(dict(status='completed',returncode=0),'Using SPARSE 1.3 as Direct Linear Solver\nanalysis aborted\nJOINT_POPULATION_TRAN_END')

    def test_timeout_rejected(self):
        with self.assertRaises(AssertionError):
            numerical_gate(dict(status='timeout',returncode=0),'Using SPARSE 1.3 as Direct Linear Solver\nJOINT_POPULATION_TRAN_END')

    def test_wrong_solver_rejected(self):
        with self.assertRaises(AssertionError):
            numerical_gate(dict(status='completed',returncode=0),'Using KLU as Direct Linear Solver\nJOINT_POPULATION_TRAN_END')


if __name__=='__main__':unittest.main()
