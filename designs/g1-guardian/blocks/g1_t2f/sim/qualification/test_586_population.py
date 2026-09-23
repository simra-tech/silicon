import unittest
from prepare_586_population import BASE, make_deck, mismatch_source
from run_586_population_control import phase_text
from analyze_586_population import changed_primitives


class PopulationTests(unittest.TestCase):
    def setUp(self):
        self.original = (BASE/'ptat_T12.5.cir').read_text()
        self.groups = {'BGR': ['@q.xbgr.xq1.qnpn13g2[area]'], 'T2F': ['@c.xt2f.xc1.c1[scale]']}

    def test_source_only_original_call_flags(self):
        text = '* unchanged\nXM1 d g s b sg13_hv_nmos w=1u l=1u\nCext1 a b 1f\n.end\n'
        for enabled in [True, False]:
            changed = mismatch_source(text, enabled)
            self.assertEqual(changed.replace(' mm_ok='+str(int(enabled)), ''), text)
            self.assertEqual(changed.count('mm_ok='), 1)

    def test_double_instrumentation_rejected(self):
        with self.assertRaises(AssertionError):
            mismatch_source('XM1 d g s b model mm_ok=1\n', True)

    def test_return_has_one_seed_reset_and_four_unchanged_transients(self):
        deck = make_deck(self.original, 74001, [25, 125, -40, 25], self.groups)
        self.assertEqual(deck.count('\nreset\n'), 1)
        self.assertEqual(deck.count('\nsetseed '), 1)
        self.assertEqual(deck.count('tran 5n 32u\n'), 4)
        self.assertEqual(deck.count('rise=24'), 4)
        self.assertEqual(deck.count('rise=8'), 8)
        self.assertIn('wrdata phase3.dat ', deck)
        self.assertEqual(deck.count('_mismatch\n'), 5)

    def test_body_only_declared_libraries_temperature_changed(self):
        changed = make_deck(self.original, 74002, [25], self.groups).split('.control\n')[0]
        restored = changed.replace('_mismatch\n', '\n').replace('.temp 25\n', '.temp 12.5\n')
        self.assertEqual(restored, self.original.split('.control\n')[0])

    def test_unknown_seed_or_temperature_sequence_rejected(self):
        for seed, temps in [(51001, [25]), (74001, [125]), (74001, [25, 25])]:
            with self.assertRaises(AssertionError):
                make_deck(self.original, seed, temps, self.groups)

    def test_phase_requires_completed_unique_markers(self):
        self.assertEqual(phase_text('PHASE0_BEGIN\nvalue\nPHASE0_END\n', 0), 'value\n')
        with self.assertRaises(AssertionError):
            phase_text('PHASE0_BEGIN\nvalue\n', 0)
        with self.assertRaises(AssertionError):
            phase_text('PHASE0_BEGIN\na\nPHASE0_END\nPHASE0_BEGIN\nb\nPHASE0_END\n', 0)

    def test_every_primitive_must_vary_in_changed_seed(self):
        inventory = {'primitives': [{'instance': 'xbgr.x1', 'group': 'BGR', 'kind': 'MOS', 'queries': ['w', 'delvto']},
                                     {'instance': 'xt2f.c1', 'group': 'T2F', 'kind': 'CMIM', 'queries': ['scale']}]}
        old = {'BGR': [['w', '1'], ['delvto', '.1']], 'T2F': [['scale', '1']]}
        new = {'BGR': [['w', '1'], ['delvto', '.2']], 'T2F': [['scale', '1']]}
        rows = changed_primitives(inventory, old, new)
        self.assertEqual([r['status'] for r in rows], ['passed', 'failed'])
        new['T2F'] = [['scale', '1.0000']]
        self.assertEqual(changed_primitives(inventory, old, new)[1]['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
