import unittest
from prepare_586_klu_temperature_coverage import HERE,REFERENCES,transform
class TemperatureContracts(unittest.TestCase):
    def test_original_one_reset_fullphase_inverse(self):
        paths=[HERE/'runs'/'t2f586-calibration-s74101-20260922-a'/('p%02d'%i)/'probe.cir' for i in [1,2,3]]
        paths += [HERE/'runs'/n.replace('-enabled','-return')/'probe.cir' for n in REFERENCES.values()]
        for path in paths:
            original=path.read_text();trial=transform(original)
            self.assertEqual(trial.replace('.options klu\n',''),original)
            self.assertEqual(trial.count('meas tran'),original.count('meas tran'))
            self.assertEqual(trial.count('reset\n'),1)
if __name__=='__main__':unittest.main()
