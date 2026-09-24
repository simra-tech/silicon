import unittest
from run_clock_coupling import changed_deck
from check_clock_coupling import gain_check, sample


class DeckTest(unittest.TestCase):
    def setUp(self):
        self.deck = '* fixture\nVsh shp 0 dc .036\nCL isense 0 300f\n.include qualification/old/sense.spice\n.control\nquit\n.endc\n.end\n'

    def test_only_capacitor_changes(self):
        new = changed_deck(self.deck, 'old', 'new', 'coupling')
        self.assertEqual(new.replace('Cinterface isense clk 5.23387214f\n', '').replace('new', 'old'), self.deck)

    def test_gain_probes(self):
        import re
        for mode, delta in [('gain5', 5e-6), ('gain10', 1e-5)]:
            new = changed_deck(self.deck, 'old', 'new', mode)
            self.assertAlmostEqual(float(re.search(r'^Vsh shp 0 dc (\S+)', new, re.M)[1]), .036 + delta)
            self.assertNotIn('Cinterface', new)

    def test_frozen_via_cap_only(self):
        new = changed_deck(self.deck, 'old', 'new', 'coupling', 5.286345256)
        self.assertEqual(new.replace('Cinterface isense clk 5.286345256f\n', '').replace('new', 'old'), self.deck)
        for value in (0, -1, float('nan'), 6):
            with self.assertRaises(AssertionError):
                changed_deck(self.deck, 'old', 'new', 'coupling', value)

    def test_rejects_missing_load(self):
        with self.assertRaises(AssertionError):
            changed_deck(self.deck.replace('300f', '400f'), 'old', 'new', 'coupling')

    def test_rejects_reused_run(self):
        with self.assertRaises(AssertionError):
            changed_deck(self.deck, 'old', 'old', 'coupling')

    def test_rejects_duplicate_input(self):
        with self.assertRaises(AssertionError):
            changed_deck('Vsh shp 0 dc .036\n' + self.deck, 'old', 'new', 'gain5')

    def test_gain_gate(self):
        self.assertTrue(gain_check(10, 10.01)[0])
        for left, right in [(10, 11), (0, 0), (10, -10), (float('nan'), 10)]:
            self.assertFalse(gain_check(left, right)[0])

    def test_interpolation_no_extrapolation(self):
        wave = {'times': [0, 1], 'rows': [[0, 2], [1, 4]]}
        self.assertEqual(sample(wave, .5, 1), 3)
        self.assertEqual(sample(wave, 0, 1), 2)
        self.assertEqual(sample(wave, 1, 1), 4)
        with self.assertRaises(AssertionError):
            sample(wave, 1.1, 1)


if __name__ == '__main__':
    unittest.main()
