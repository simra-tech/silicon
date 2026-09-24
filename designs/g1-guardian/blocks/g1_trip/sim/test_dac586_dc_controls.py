import math
import unittest
from prepare_dac586_dc_controls import map_bits


class MapTests(unittest.TestCase):
    def test_all256_exact_integer_bits(self):
        for code in range(256):
            for bit in range(8):
                mapped=1.2*(math.floor((code+.1)/2**bit)-2*math.floor((code+.1)/2**(bit+1)))
                self.assertEqual(mapped,1.2*((code>>bit)&1))

    def test_mapping_does_not_edit_other_circuit(self):
        source='untouched\n'+''.join('V%s%d %s%d 0 dc %s\n'%(prefix,bit,prefix,bit,1.2*((code>>bit)&1)) for prefix,code in [('s',135),('h',151)] for bit in range(8))+'Xkeep a b model\n.control\nop\n.endc\n'
        result=map_bits(source,135,151)
        self.assertIn('Xkeep a b model\n',result)
        self.assertEqual(result.count(' V=1.2*'),16)
        self.assertIn('Vcode code 0 dc 0\n',result)

    def test_changed_original_bit_rejected(self):
        with self.assertRaises(AssertionError):map_bits('Vs0 s0 0 dc 0\n.control\n',135,151)


if __name__=='__main__':unittest.main()
