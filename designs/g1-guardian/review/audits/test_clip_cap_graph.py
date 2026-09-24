import unittest
from clip_cap_graph import parse_capacitors


class CapacitorParserTests(unittest.TestCase):
    def test_wrapped_capacitor(self):
        caps, aliases = parse_capacitors('C1 P N\n+ 3.5f\nC2 P VSUBS 2a')
        self.assertAlmostEqual(caps[0][2], 3.5e-15)
        self.assertEqual(len(caps), 2)

    def test_inconsistent_target_net_names_rejected(self):
        with self.assertRaises(ValueError):
            parse_capacitors('C1 CTX_L50_1|P N 1f\nC2 P|CTX_L50_1 VSUBS 2f')

    def test_target_alias(self):
        caps, aliases = parse_capacitors('C1 CTX_L50_1|P N 1f\nC2 CTX_L50_1|P VSUBS 2f')
        self.assertEqual(caps[0][:2], ('P', 'N'))

    def test_ground_connected_fill(self):
        caps, aliases = parse_capacitors('C1 P N 1f\nC2 P FILL_L50_0|CTX_L50_2 2f')
        self.assertEqual(caps[1][1], 'CTX_L50_2')

    def test_invalid(self):
        for text in ['+ 1f', 'C1 P N -1f', 'C1 P N 1f\nC1 P N 2f',
                     'C1 P|N VSUBS 1f', 'C1 P|VSUBS N 1f',
                     'C1 P STRANGE 1f', 'C1 P VSUBS 1f', 'C1 P N']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_capacitors(text)


if __name__ == '__main__':
    unittest.main()
