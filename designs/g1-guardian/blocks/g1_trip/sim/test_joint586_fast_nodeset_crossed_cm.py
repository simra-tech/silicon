import json
import unittest
from prepare_joint586_fast_nodeset_crossed_cm import SIM,REFERENCE,checks_for_corner,make_deck
from run_joint586_fast_nodeset_staged import adverse_deck
from run_joint586_fast_nodeset_rescue import numerical_gate


class CrossedChecks(unittest.TestCase):
    def setUp(self):
        self.scope=json.loads((SIM/'qualification/joint586-crossed-cm144-contract-20260923-a.json').read_text())
        self.tree=dict(bracket_status='passed selected probes',corrected_codes=dict(soft=150,hard=212),
            fixed_residual_codes=dict(soft=125,hard=136))

    def test_exact72_original_codes_and_crossings(self):
        rows=checks_for_corner(self.scope,'fast',self.tree)
        self.assertEqual(len(rows),72);self.assertEqual(sum(r['kind']=='guard' for r in rows),48)
        for row in rows:
            self.assertEqual(row['codes'],[150,212] if row['kind']=='guard' else [125,136])
        expected={(t,a,d,c) for t in [-40,125] for a,d in [(3.,1.08),(3.3,1.2),(3.6,1.32)] for c in [-.1,.3]}
        self.assertEqual({tuple(r['condition'][1:]) for r in rows},expected)

    def test_other_corner_cannot_inherit_fast_method(self):
        with self.assertRaises(AssertionError):checks_for_corner(self.scope,'slow',self.tree)

    def test_failed_calibration_cannot_select_favorable_codes(self):
        self.tree['bracket_status']='failed'
        with self.assertRaises(AssertionError):checks_for_corner(self.scope,'fast',self.tree)

    def test_input_identity_except_wave_destination(self):
        original=(SIM/'qualification'/REFERENCE/'population_transient.cir').read_text()
        for row in checks_for_corner(self.scope,'fast',self.tree):
            actual=make_deck(original,'crossed-unit-test',row)
            expected=adverse_deck(original,REFERENCE,'crossed-unit-test',78101,row['codes'],row['shunt_V'],row['condition'],'fast')
            restored=actual.replace('qualification/crossed-unit-test/p%02d/phase0.dat'%row['index'],'qualification/crossed-unit-test/phase0.dat')
            self.assertEqual(restored,expected)
            self.assertIn(' v(shn)\n',actual)

    def test_zero_exit_abort_rejected(self):
        log='Using SPARSE 1.3 as Direct Linear Solver\nJOINT_POPULATION_TRAN_END\nanalysis aborted\n'
        with self.assertRaises(AssertionError):numerical_gate(dict(status='completed',returncode=0),log)


if __name__=='__main__':unittest.main()

