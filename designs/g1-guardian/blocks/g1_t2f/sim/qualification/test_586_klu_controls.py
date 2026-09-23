import unittest
from prepare_586_klu_controls import HERE,REFERENCES,make_full
class MatchedControls(unittest.TestCase):
    def test_all_corners_exact_inverse(self):
        for n in REFERENCES.values():
            original=(HERE/'runs'/n/'probe.cir').read_text();trial=make_full(original)
            self.assertEqual(trial.replace('.options klu\n',''),original)
            self.assertEqual(trial.count('meas tran'),original.count('meas tran'))
            self.assertEqual(trial,make_full(original))
    def test_reject_existing_selector(self):
        original=(HERE/'runs'/REFERENCES['typical']/'probe.cir').read_text()
        with self.assertRaises(AssertionError):make_full(make_full(original))
if __name__=='__main__':unittest.main()
