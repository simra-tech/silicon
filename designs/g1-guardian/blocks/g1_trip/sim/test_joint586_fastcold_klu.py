import unittest
from prepare_joint586_fastcold_klu import ORIGINAL,transform
class Fastcold(unittest.TestCase):
    def test_inverse_and_source_unchanged(self):
        original=(ORIGINAL/'population_transient.cir').read_text();trial=transform(original,'test-klu')
        restored=trial.replace('qualification/test-klu/phase0.dat','qualification/'+ORIGINAL.name+'/phase0.dat').replace('.options klu\n','')
        self.assertEqual(restored,original)
        self.assertEqual([s for s in trial.splitlines() if s.startswith('.include ')],[s for s in original.splitlines() if s.startswith('.include ')])
    def test_no_seed_change(self):
        with self.assertRaises(AssertionError):transform((ORIGINAL/'population_transient.cir').read_text().replace('setseed 78001','setseed 78002'),'test-klu')
if __name__=='__main__':unittest.main()
