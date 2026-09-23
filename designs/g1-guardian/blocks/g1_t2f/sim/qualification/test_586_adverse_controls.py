import json
import unittest
from prepare_586_adverse_controls import REFERENCE, CORNERS, CONDITIONS, make_deck
from analyze_586_adverse_controls import calibrate, analyze_corner


class AdverseTests(unittest.TestCase):
    def test_exact_declared_corner_rail_temperature_only(self):
        groups = json.loads((REFERENCE/'preparation.json').read_text())['query_groups']
        reference = (REFERENCE/'probe.cir').read_text()
        for corner, (h, m, r, c) in CORNERS.items():
            for label, t, va, vd, role in CONDITIONS:
                deck = make_deck(corner, t, va, vd, groups)
                for old, new in [('hbt_'+h, 'hbt_typ'), ('mos_'+m, 'mos_tt'), ('res_'+r, 'res_typ'), ('cap_'+c, 'cap_typ')]:
                    deck = deck.replace(' '+old+'\n', ' '+new+'\n')
                deck = deck.replace('.temp '+str(float(t))+'\n', '.temp 25.0\n')
                deck = deck.replace('Vdd vdd 0 dc '+str(va)+'\n', 'Vdd vdd 0 dc 3.3\n')
                deck = deck.replace('Vdd12 vdd12 0 dc '+str(vd)+'\n', 'Vdd12 vdd12 0 dc 1.2\n')
                deck = deck.replace('1.01u '+str(va)+')\n', '1.01u 3.3)\n')
                self.assertEqual(deck, reference)

    def test_invalid_protocol_condition_rejected(self):
        with self.assertRaises(AssertionError):
            make_deck('slow', 25, 3.0, 1.08, {})

    def test_calibration_is_nominal_rail_only(self):
        rows = {'cal25': 1000, 'cal100': 1750, 'lowcold': 350, 'lowhot': 2000, 'highcold': 350, 'highhot': 2000}
        self.assertEqual(calibrate(rows)['status'], 'passed')
        rows['highhot'] += 21
        result = calibrate(rows)
        self.assertEqual(result['status'], 'failed')
        self.assertAlmostEqual(result['maximum_independent_abs_residual_C'], 2.1)
        self.assertEqual(result['slope_Hz_per_C'], 10)

    def test_missing_receipts_explicit_not_run(self):
        report = analyze_corner({})
        self.assertEqual(report['status'], 'not run')
        self.assertEqual(len(report['missing_receipts']), 6)
        self.assertEqual(set(report['control_statuses'].values()), {'not run'})

    def test_failed_completed_control_retained_with_missing(self):
        report = analyze_corner({'cal25': {'control_status': 'failed'}})
        self.assertEqual(report['known_failed_controls'], ['cal25'])
        self.assertTrue(report['status'].startswith('failed'))
        self.assertEqual(len(report['missing_receipts']), 5)

    def test_complete_corner_survives_other_missing_corner(self):
        entries = {label: dict(control_status='passed', full3180_status='passed', parameters_before={'a': 1},
            parameters_after={'a': 1}, measurements={'freq': 750+temperature*10})
            for label, temperature, va, vd, role in CONDITIONS}
        corners = {'slow': analyze_corner(entries), 'fast': analyze_corner({})}
        self.assertEqual(corners['slow']['status'], 'passed')
        self.assertEqual(corners['fast']['status'], 'not run')

    def test_invalid_receipt_fails_without_aborting(self):
        report = analyze_corner({}, errors={'cal25': 'hash mismatch'})
        self.assertTrue(report['status'].startswith('failed'))
        self.assertEqual(report['receipt_errors']['cal25'], 'hash mismatch')


if __name__ == '__main__':
    unittest.main()
