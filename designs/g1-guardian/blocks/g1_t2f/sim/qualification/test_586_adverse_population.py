import unittest
from prepare_586_adverse_population import BASE, CORNERS, SEEDS, make_deck
from prepare_586_population import make_deck as typ_deck


class AdversePopulationTests(unittest.TestCase):
    def setUp(self):
        self.original = (BASE/'ptat_T12.5.cir').read_text()
        self.groups = {'BGR': ['@q.xbgr.xq1.qnpn13g2[area]'], 'T2F': ['@c.xt2f.xc1.c1[scale]']}

    def test_only_five_sections_and_seed(self):
        for corner, seeds in SEEDS.items():
            for index, seed in enumerate(seeds):
                for temperatures in [[25], [25, 125, -40, 25]]:
                    deck = make_deck(self.original, corner, seed, temperatures, self.groups)
                    restored = deck.replace('setseed %d\n' % seed, 'setseed %d\n' % (74001+index))
                    for stem, old, new in zip(['hbt', 'mos', 'res', 'cap'], ['typ', 'tt', 'typ', 'typ'], CORNERS[corner]):
                        restored = restored.replace(' '+stem+'_'+new+'_mismatch\n', ' '+stem+'_'+old+'_mismatch\n')
                    self.assertEqual(restored, typ_deck(self.original, 74001+index, temperatures, self.groups))
                    self.assertEqual(deck.count('\nreset\n'), 1)
                    self.assertEqual(deck.count('tran 5n 32u\n'), len(temperatures))

    def test_unknown_population_rejected(self):
        for corner, seed in [('slow', 74101), ('fast', 75001), ('typical', 74001)]:
            with self.assertRaises(AssertionError):
                make_deck(self.original, corner, seed, [25], self.groups)


if __name__ == '__main__':
    unittest.main()
