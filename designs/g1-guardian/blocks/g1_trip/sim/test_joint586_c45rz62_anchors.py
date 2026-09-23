import unittest
from prepare_joint586_c45rz62_anchors import candidate_source,deck_transform,OLD,NEW

class Tests(unittest.TestCase):
    def test_main_only_exact_source_inverse(self):
        rz='XRZ out1 cz vss rppd w=1u l=6.2u m=1 b=0 mm_ok=1\n'
        old='.subckt buffer a b\n'+rz+'.ends\n.subckt g1_ota_main_candidate a b\n'+rz+'XCC cz out cap_cmim w=69u l=23u m=1 mm_ok=1\n.ends\n'
        new=candidate_source(old);self.assertEqual(new.count('l=62u'),1);self.assertEqual(new.count('l=6.2u'),1);self.assertIn('w=45u',new)
    def test_only_source_path_output_and_step(self):
        old='.include qualification/parent/sense.spice\nsetseed 73001\n'+OLD+'wrdata qualification/parent/p08/phase0.dat v(a)\n'
        for step in ['0.2n','1n']:
            result=deck_transform(old,'parent','p08','new',step)
            inverse=result.replace('qualification/new/sense.spice','qualification/parent/sense.spice').replace('qualification/new/phase0.dat','qualification/parent/p08/phase0.dat')
            if step=='1n':inverse=inverse.replace(NEW,OLD)
            self.assertEqual(inverse,old)
    def test_wrong_seed_or_step_rejected(self):
        with self.assertRaises(AssertionError):deck_transform('setseed 73002\n'+OLD,'a','b','c','1n')
        with self.assertRaises(AssertionError):deck_transform('','a','b','c','2n')
    def test_wrong_candidate_source_rejected(self):
        with self.assertRaises(AssertionError):candidate_source('.subckt g1_ota_main_candidate a b\n.ends\n')

if __name__=='__main__':unittest.main()
