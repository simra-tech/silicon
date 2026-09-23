import unittest
from prepare_joint586_fast_nodeset_rescue import SIM
from run_joint586_fast_nodeset_return_r2 import validate_each_phase,original_validator


class FourOutputs(unittest.TestCase):
    def setUp(self):
        out=SIM/'qualification/joint586-fast-nodeset-rescue-own-return-20260923-a'
        self.deck=(out/'population_transient.cir').read_text();self.trip=(out/'trip.spice').read_text()

    def test_original_rejects_four_output_return(self):
        with self.assertRaises(AssertionError):original_validator(self.deck,self.trip)

    def test_all_four_validated_without_deck_change(self):
        original=self.deck
        self.assertTrue(validate_each_phase(self.deck,self.trip)['status'].startswith('passed'))
        self.assertEqual(original,self.deck)

    def test_missing_saved_vector_in_fourth_phase_rejected(self):
        lines=self.deck.splitlines(True);indices=[i for i,l in enumerate(lines) if l.startswith('wrdata ')]
        lines[indices[-1]]=lines[indices[-1]].replace(' v(xt.xch.yn)','')
        with self.assertRaises(AssertionError):validate_each_phase(''.join(lines),self.trip)


if __name__=='__main__':unittest.main()
