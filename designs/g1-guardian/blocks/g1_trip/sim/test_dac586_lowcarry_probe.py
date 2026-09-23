import unittest
from prepare_dac586_lowcarry_probe import chunk_deck

def fixture():
    return '\n'.join(['V'+p+str(i)+' '+p+str(i)+' 0 dc 0' for p in ['s','h'] for i in range(8)])+'\n.save v(out)\n.control\nop\nwrdata qualification/old/op0.dat v(out)\necho POPULATION_OP_END\nquit 0\n.endc\n.end\n'

class Tests(unittest.TestCase):
    def test_exact_code_range_and_two_sweeps(self):
        result=chunk_deck(fixture(),'old','new',{'FULL':['@x[p]']})
        self.assertEqual(result.count('dc Vcode '),2)
        self.assertIn('dc Vcode 0 7 1\n',result);self.assertIn('dc Vcode 7 0 -1\n',result)
        self.assertIn('echo DC_FULL_AFTER_BEGIN\nprint @x[p]\n',result)
        self.assertEqual(result.count('floor('),32)
    def test_nonzero_original_rejected(self):
        with self.assertRaises(AssertionError):chunk_deck(fixture().replace('Vs0 s0 0 dc 0','Vs0 s0 0 dc 1.2'),'old','new',{})
    def test_missing_end_rejected(self):
        with self.assertRaises(AssertionError):chunk_deck(fixture().replace('quit 0','quit 1'),'old','new',{})
    def test_multiple_output_rejected(self):
        with self.assertRaises(ValueError):chunk_deck(fixture().replace('op\n','op\nwrdata qualification/old/extra.dat v(out)\n'),'old','new',{})

if __name__=='__main__':unittest.main()
