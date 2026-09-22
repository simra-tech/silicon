import unittest
from prepare_bgr_calibration_probe import transform, normalized_stimulus


class CalibrationStimulusTests(unittest.TestCase):
    def deck(self):
        return ('.temp 125.0\nVsh shp 0 dc 0.0245\n'+
                ''.join('V%s%d %s%d 0 dc 0\n' % (ch,i,ch,i) for ch in ['s','h'] for i in range(8))+
                'Vclk clk 0 pulse(0 1.2 20n 0.2n 0.2n 100n 200n)\nsetseed 71002\ntran 0.2n 1.02u 0 0.2n\ninclude old/sense.spice\n')

    def test_only_declared_inputs_change(self):
        original=self.deck();new=transform(original,'old','fresh',153,204,.025,-40)
        self.assertEqual(normalized_stimulus(original),normalized_stimulus(new.replace('fresh','old')))
        self.assertIn('Vs0 s0 0 dc 1.2',new)
        self.assertIn('Vh0 h0 0 dc 0',new)
        self.assertIn('Vh2 h2 0 dc 1.2',new)

    def test_invalid_inputs_rejected(self):
        for soft,hard,shunt,temp in [(-1,0,.025,25),(0,256,.025,25),(0,0,.051,25),(0,0,.025,26)]:
            with self.assertRaises(AssertionError):transform(self.deck(),'old','fresh',soft,hard,shunt,temp)


if __name__=='__main__':unittest.main()
