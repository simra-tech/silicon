import json
import unittest
from prepare_dac586_chunk_controls import SIM,alter_code,transform


class ChunkTests(unittest.TestCase):
    def test_all16_bit_values(self):
        for code in range(256):
            lines=alter_code(code).splitlines()
            self.assertEqual(len(lines),16)
            for offset,prefix in [(0,'s'),(8,'h')]:
                observed=sum((line.endswith('=1.2'))<<bit for bit,line in enumerate(lines[offset:offset+8]))
                self.assertEqual(observed,code)

    def test_transform_inverse_and_single_seed(self):
        for label in ['room','hot']:
            ref=SIM/'qualification'/('dac586-static-controls-20260923-a-c127-'+label)
            original=(ref/'dac_static.cir').read_text();prep=json.loads((ref/'preparation.json').read_text())
            new=transform(original,ref.name,'chunk',prep['groups'])
            self.assertEqual(new.split('.control\n')[0].replace('chunk',ref.name),original.split('.control\n')[0])
            prefix,tail=new.split('echo DAC_CHUNK_WARM_BEGIN\n')
            tail=tail.split('echo DAC_CHUNK_WARM_END\n')[1]
            self.assertEqual((prefix+tail).replace('chunk',ref.name),original)
            self.assertEqual(new.count('\nreset\n'),1)
            self.assertEqual(new.count('\nsetseed '),1)
            self.assertEqual(new.count('\nop\n'),4)
            self.assertEqual(new.count('\nprint '),3*(11512+27))

    def test_bad_code_rejected(self):
        for code in [-1,256,None,1.5]:
            with self.assertRaises(AssertionError):alter_code(code)


if __name__=='__main__':unittest.main()
