import unittest
from prepare_joint586_klu_replay import ORIGINAL,transform
class Replay(unittest.TestCase):
    def test_only_selector_output(self):
        original=(ORIGINAL/'probe.cir').read_text();new=transform(original,'test-klu')
        self.assertEqual(new.replace('qualification/test-klu/phase0.dat','qualification/'+ORIGINAL.parent.name+'/p00/phase0.dat').replace('.options klu\n',''),original)
        self.assertEqual([s for s in new.splitlines() if s.startswith('.include ')],[s for s in original.splitlines() if s.startswith('.include ')])
    def test_reject_seed_change(self):
        with self.assertRaises(AssertionError):transform((ORIGINAL/'probe.cir').read_text().replace('setseed 73001','setseed 73002'),'test-klu')
if __name__=='__main__':unittest.main()
