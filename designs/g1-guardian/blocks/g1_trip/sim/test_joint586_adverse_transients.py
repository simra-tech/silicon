import unittest
from prepare_joint586_adverse_transients import append_shn,phases,SIM,REFERENCE,transform_fixture


class OutputAndPhases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.old=(SIM/'qualification'/REFERENCE/'population_transient.cir').read_text()
    def test_appended_vector_is_output_only_and_original_order_retained(self):
        old,_=transform_fixture(self.old,'slow',3.3,1.2,0.)
        new=append_shn(old)
        self.assertEqual(new.count(' v(shn)\n'),3)
        for before,after in zip([l for l in old.splitlines() if l.startswith(('.save ','wrdata '))],
                                [l for l in new.splitlines() if l.startswith(('.save ','wrdata '))]):
            self.assertEqual(after,before+' v(shn)')
    def test_single_reset_and_seed_all_four_phases(self):
        new=phases(self.old,REFERENCE,'test-four',77001,[25,125,-40,25])
        self.assertEqual(new.count('\nreset\n'),1)
        self.assertEqual(new.count('setseed 77001\n'),1)
        self.assertEqual(new.count('tran 0.2n 1.02u 0 0.2n\n'),4)
        self.assertIn('phase3.dat',new)
    def test_ground_reference_cannot_fake_shn_observation(self):
        with self.assertRaises(AssertionError):append_shn(self.old)
    def test_exact_original18_byte_projection(self):
        from run_joint586_adverse_transient import compare18
        old=[(' '.join('n%d'%i for i in range(18))+'\n').encode(),(' '.join(str(i) for i in range(18))+'\n').encode()]
        new=[old[0][:-1]+b' shn\n',old[1][:-1]+b' 18\n']
        self.assertTrue(compare18(old,new)['status'].startswith('passed'))
        new[1]=new[1].replace(b'0 1 ',b'0 2 ',1)
        with self.assertRaises(AssertionError):compare18(old,new)


if __name__=='__main__':unittest.main()
