import unittest
from prepare_586_supply_decomposition import make_deck
from prepare_586_adverse_controls import make_deck as adverse_deck


class SupplyDecompositionTests(unittest.TestCase):
    def test_only_three_source_amplitudes_change(self):
        groups = {'BGR': ['@q.xbgr.xq1.qnpn13g2[area]'], 'T2F': ['@c.xt2f.xc1.c1[scale]']}
        for corner in ['slow', 'fast']:
            for temperature in [-40, 125]:
                deck = make_deck(corner, temperature, 3.3, 1.2, groups)
                restored = deck.replace('Vdd vdd 0 dc 3.3\n', 'Vdd vdd 0 dc 3.0\n')
                restored = restored.replace('Vdd12 vdd12 0 dc 1.2\n', 'Vdd12 vdd12 0 dc 1.08\n')
                restored = restored.replace('Ven en 0 pwl(0 0 1u 0 1.01u 3.3)\n', 'Ven en 0 pwl(0 0 1u 0 1.01u 3.0)\n')
                self.assertEqual(restored, adverse_deck(corner, temperature, 3.0, 1.08, groups))

    def test_undeclared_temperature_rejected(self):
        with self.assertRaises(AssertionError):
            make_deck('slow', 25, 3.3, 1.2, {})


if __name__ == '__main__':
    unittest.main()
