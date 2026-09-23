import unittest
from prepare_586_rail_factorial import HERE, make_deck


class RailFactorialTests(unittest.TestCase):
    def test_all_four_exact_inverse_transforms(self):
        for corner in ['slow', 'fast']:
            original = (HERE/'runs'/('t2f586-supply-decomposition-20260923-a-'+corner+'-nomcold')/'probe.cir').read_text()
            for label in ['analoghigh', 'digitalhigh']:
                deck = make_deck(original, label)
                self.assertEqual(deck.split('.control\n')[1], original.split('.control\n')[1])
                changed = [(a, b) for a, b in zip(original.splitlines(), deck.splitlines()) if a != b]
                self.assertEqual(len(changed), 2 if label == 'analoghigh' else 1)
                restored = deck.replace('Vdd vdd 0 dc 3.6\n', 'Vdd vdd 0 dc 3.3\n')
                restored = restored.replace('Vdd12 vdd12 0 dc 1.32\n', 'Vdd12 vdd12 0 dc 1.2\n')
                restored = restored.replace('Ven en 0 pwl(0 0 1u 0 1.01u 3.6)\n', 'Ven en 0 pwl(0 0 1u 0 1.01u 3.3)\n')
                self.assertEqual(restored, original)

    def test_undeclared_temperature_seed_or_condition_rejected(self):
        original = (HERE/'runs/t2f586-supply-decomposition-20260923-a-slow-nomcold/probe.cir').read_text()
        for bad in [original.replace('.temp -40', '.temp 125'), original+'\nsetseed 1\n', original+'\n* _mismatch\n']:
            with self.assertRaises(AssertionError):
                make_deck(bad, 'analoghigh')
        with self.assertRaises(AssertionError):
            make_deck(original, 'allhigh')


if __name__ == '__main__':
    unittest.main()
