import unittest
from lef_port_stub import port_stub


def fixture(rows):
    return 'MACRO demo\n' + ''.join('  PIN {}\n    DIRECTION {} ;\n  END {}\n'.format(n, d, n) for n, d in rows) + 'END demo\n'


class PortStubTests(unittest.TestCase):
    def test_names_vectors_and_directions(self):
        result, pins = port_stub(fixture([('a[0]', 'INPUT'), ('a[1]', 'INPUT'), ('z', 'OUTPUT'), ('VSS', 'INOUT')]), 'demo')
        self.assertIn('input [1:0] a;', result)
        self.assertEqual(pins, {'a[0]': 'input', 'a[1]': 'input', 'z': 'output', 'VSS': 'inout'})

    def test_missing_bit_rejected(self):
        with self.assertRaises(AssertionError):
            port_stub(fixture([('a[0]', 'INPUT'), ('a[2]', 'INPUT')]), 'demo')

    def test_mixed_direction_rejected(self):
        with self.assertRaises(AssertionError):
            port_stub(fixture([('a[0]', 'INPUT'), ('a[1]', 'OUTPUT')]), 'demo')

    def test_duplicate_rejected(self):
        with self.assertRaises(AssertionError):
            port_stub(fixture([('a', 'INPUT'), ('a', 'INPUT')]), 'demo')

    def test_scalar_bus_collision_rejected(self):
        with self.assertRaises(AssertionError):
            port_stub(fixture([('a', 'INPUT'), ('a[0]', 'INPUT')]), 'demo')

    def test_wrong_macro_rejected(self):
        with self.assertRaises(AssertionError):
            port_stub(fixture([('a', 'INPUT')]), 'other')

    def test_missing_direction_rejected(self):
        with self.assertRaises(AssertionError):
            port_stub(fixture([('a', 'INPUT')]).replace('DIRECTION INPUT ;', ''), 'demo')


if __name__ == '__main__':
    unittest.main()
