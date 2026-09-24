import unittest
import re
from prepare_dac586_twoop_chunk import transform


class TwoOpTests(unittest.TestCase):
    def test_only_two_additional_solves(self):
        source='title\n.control\nsetseed 73001\nreset\nop\necho P0\nop\nprint x\nwrdata old/op0.dat v(x)\necho POPULATION_OP_END\nquit 0\n.endc\n.end\n'
        result=transform(source,'old','new',{'BGR':['@x[y]']})
        self.assertEqual(len(re.findall(r'^op$',result,re.M)),6)
        self.assertEqual(result.count('op\nop\nwrdata '),2)
        self.assertEqual(result.count('\nreset\n'),1)

    def test_unknown_original_rejected(self):
        with self.assertRaises(AssertionError):transform('unknown','old','new',{})


if __name__=='__main__':unittest.main()
