import unittest
import numpy as np
from prepare_joint586_tmax_probe import ORIGINAL,transform,OLD,NEW
from run_joint586_tmax_probe import runtime_gate
from compare_joint586_tmax_probe import crossings


class Tests(unittest.TestCase):
    def test_exact_inverse(self):
        text=(ORIGINAL/'probe.cir').read_text();trial=transform(text,'tmax-unit')
        trial=trial.replace(NEW,OLD).replace('qualification/tmax-unit/phase0.dat','qualification/'+ORIGINAL.parent.name+'/p00/phase0.dat')
        self.assertEqual(text,trial)
    def test_duplicate_or_wrong_step_rejected(self):
        text=(ORIGINAL/'probe.cir').read_text()
        for changed in [text+OLD,text.replace(OLD,'tran 0.2n 1.02u 0 0.5n\n')]:
            with self.assertRaises(AssertionError):transform(changed,'tmax-unit')
    def test_solver_or_seed_mutation_rejected(self):
        text=(ORIGINAL/'probe.cir').read_text()
        for changed in [text+'.options klu\n',text.replace('setseed 73001','setseed 73002')]:
            with self.assertRaises(AssertionError):transform(changed,'tmax-unit')
    def test_zero_exit_abort_rejected(self):
        log='Using SPARSE 1.3 as Direct Linear Solver\nJOINT_POPULATION_TRAN_END\nanalysis aborted\n'
        with self.assertRaises(AssertionError):runtime_gate(dict(status='completed',returncode=0),log)
    def test_timeout_label_rejected(self):
        with self.assertRaises(AssertionError):runtime_gate(dict(status='timeout',returncode=0),'Using SPARSE 1.3 as Direct Linear Solver\nJOINT_POPULATION_TRAN_END')
    def test_crossing_bracket_and_direction(self):
        data=np.array([[0,0],[1,1.2],[2,0]],dtype=float)
        self.assertEqual(crossings(data,1,True),[dict(time_s=.5,bracket_s=[0.,1.])])
        self.assertEqual(crossings(data,1,False),[dict(time_s=1.5,bracket_s=[1.,2.])])


if __name__=='__main__':unittest.main()
