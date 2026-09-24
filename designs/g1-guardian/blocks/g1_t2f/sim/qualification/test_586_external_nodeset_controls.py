import unittest
from prepare_586_external_nodeset_controls import transform,NODES,ARMS


class TransformTests(unittest.TestCase):
    def setUp(self):
        self.source='.options klu\n.control\nreset\nop\necho P0_BGR_BEFORE_BEGIN\nprint @x[p]\necho P0_BGR_BEFORE_END\ntran 5n 32u\necho P0_BGR_AFTER_BEGIN\nprint @x[p]\necho P0_BGR_AFTER_END\nmeas tran t_a when v(fout)=.6 rise=8\nwrdata phase0.dat v(fout)\necho PHASE0_END\nquit\n.endc\n.end\n'
        self.guesses={node:'1.234' for node in NODES}

    def test_three_declared_arms(self):
        for arm in ARMS:
            result=transform('\n'+self.source,arm,self.guesses)
            self.assertNotIn('meas tran',result);self.assertNotIn('tran 5n',result)
            self.assertEqual(result.count('\nop\n'),2)
            self.assertEqual('.options klu' in result,arm=='klu-nodeset')
            self.assertEqual('.nodeset' in result,arm!='sparse-original')

    def test_no_silent_different_timing(self):
        with self.assertRaises(AssertionError):transform('\n'+self.source.replace('32u','31u'),ARMS[0],self.guesses)

    def test_reject_unknown_node_or_arm(self):
        with self.assertRaises(AssertionError):transform('\n'+self.source,'other',self.guesses)
        with self.assertRaises(AssertionError):transform('\n'+self.source,ARMS[0],dict(self.guesses,unknown='0'))


if __name__=='__main__':unittest.main()
