import re
import unittest
from run_joint586_adverse_calibration import adverse_deck, SIM, REFERENCE, CONDITIONS


class AdverseCalibration(unittest.TestCase):
    def test_condition_matrix_and_binary_codes_preserved(self):
        source=(SIM/'qualification'/REFERENCE/'population_transient.cir').read_text()
        for corner,seed in [('slow',77101),('fast',78101)]:
            for condition in CONDITIONS:
                for codes in [[0,0],[255,255],[127,191],[153,204]]:
                    deck=adverse_deck(source,REFERENCE,'test-adverse',seed,codes,.0245,condition,corner)
                    self.assertEqual(deck.count('setseed %d\n'%seed),1)
                    self.assertEqual(deck.count('\nreset\n'),1)
                    self.assertEqual(deck.count('tran 0.2n 1.02u 0 0.2n\n'),1)
                    for letter,code in zip(['s','h'],codes):
                        actual=[float(re.search(r'^V%s%d %s%d 0 dc (.+)$'%(letter,b,letter,b),deck,re.M).group(1)) for b in range(8)]
                        self.assertEqual(actual,[condition[3] if code&(1<<b) else 0. for b in range(8)])
                    self.assertEqual('v(shn)' in deck,condition[4] is not None)
                    self.assertIn('.temp '+str(float(condition[1]))+'\n',deck)


if __name__=='__main__':unittest.main()
