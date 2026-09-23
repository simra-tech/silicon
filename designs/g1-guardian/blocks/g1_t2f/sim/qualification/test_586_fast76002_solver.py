import unittest
from prepare_586_fast76002_solver import make_prefix,GEAR,ORIGINAL


class SolverOnly(unittest.TestCase):
    def test_one_selector_inverse_restores_qualified_gear_bytes(self):
        new=make_prefix((ORIGINAL/'probe.cir').read_text())
        self.assertEqual(new.replace('.options klu\n',''),(GEAR/'probe.cir').read_text())
        self.assertEqual(new.count('.options klu\n'),1)
        self.assertEqual(new.count('method=gear'),1)
        self.assertEqual(new.count('tran 5n 2u\n'),1)
        self.assertIn('setseed 76002\n',new)
        self.assertIn('set temp=25\n',new)
        self.assertNotIn('method=trap',new)

    def test_existing_selector_rejected(self):
        original=(ORIGINAL/'probe.cir').read_text()
        with self.assertRaises(AssertionError):make_prefix(original.replace('.control\n','.options klu\n.control\n'))


if __name__=='__main__':unittest.main()
