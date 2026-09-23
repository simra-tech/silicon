import unittest
from prepare_joint586_adverse_fixture_controls import fixture, SIM, REFERENCE, CONDITIONS, LABELS


class Fixture(unittest.TestCase):
    def test_twelve_declared_body_output_transforms(self):
        original=(SIM/'qualification'/REFERENCE/'population_transient.cir').read_text()
        for corner,seed in [('slow',77001),('fast',78001)]:
            for condition in CONDITIONS:
                if condition[0] not in LABELS:continue
                deck=fixture(original,'prospective-fixture',corner,seed,condition)
                self.assertEqual(deck.count('\nreset\n'),1)
                self.assertEqual(deck.count('tran 0.2n 1.02u 0 0.2n\n'),1)
                self.assertEqual(deck.count('setseed %d\n'%seed),1)
                self.assertIn('.temp '+str(float(condition[1]))+'\n',deck)
                self.assertIn('Vclk clk 0 pulse(0 %.12g 20n 0.2n 0.2n 100n 200n)'%condition[3],deck)
                self.assertIn('Vshn shn 0 dc '+format(condition[4]-.025/2,'.17g')+'\n',deck)
                self.assertIn('Vsh shp 0 dc '+format(condition[4]+.025/2,'.17g')+'\n',deck)
                self.assertEqual(deck.count('echo NON_BGR_BEFORE_BEGIN\n'),1)
                self.assertEqual(deck.count('echo BGR_AFTER_BEGIN\n'),1)
                # No original query/measurement/control statement changes other
                # than seed and output path; SHN observation is append-only.
                old=original.split('.control\n')[1].replace(REFERENCE,'prospective-fixture').replace('setseed 73001\n','setseed %d\n'%seed)
                new=deck.split('.control\n')[1]
                new=new.replace('echo SHN_OBSERVATION_OP\nprint v(shn)\necho SHN_OBSERVATION_OP_END\n','').replace(' v(shn)\n','\n')
                self.assertEqual(old,new)


if __name__=='__main__':unittest.main()
