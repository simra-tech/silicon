import json
import unittest
from prepare_dac586_static_controls import SIM, REFERENCE, code_body, transform


class StaticControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ref = SIM/'qualification'/REFERENCE
        cls.original = (ref/'population_op.cir').read_text()
        cls.groups = json.loads((ref/'preparation.json').read_text())['prospective_groups']

    def test_identity_codes(self):
        body = self.original.split('.control\n')[0]
        self.assertEqual(code_body(body, 135, 151), body)

    def test_all_codes_inverse_and_only_bit_lines(self):
        body = self.original.split('.control\n')[0]
        for code in range(256):
            new = code_body(body, code, 255-code)
            for old_line, new_line in zip(body.splitlines(), new.splitlines()):
                if old_line != new_line:
                    self.assertRegex(old_line, r'^V[sh][0-7] ')

    def test_output_only_removable(self):
        new = transform(self.original, REFERENCE, 'probe', 135, 151, [25], self.groups)
        self.assertEqual(new.replace('probe', REFERENCE).replace(' i(vdda) i(vdd)', ''), self.original)

    def test_return_seed_once_and_full_queries(self):
        new = transform(self.original, REFERENCE, 'probe', 135, 151, [25, 125, -40, 25], self.groups)
        self.assertEqual(new.count('\nsetseed '), 1)
        self.assertEqual(new.count('\nreset\n'), 1)
        self.assertEqual(new.count('\nop\n'), 8)
        self.assertEqual(new.count('\nprint '), 8*(11512+27))

    def test_mutated_source_rejected(self):
        with self.assertRaises(AssertionError):
            transform(self.original.replace('Vs0 s0 0 dc 1.2', 'Vs0 s0 0 dc 1.1'),
                      REFERENCE, 'probe', 0, 0, [25], self.groups)

    def test_out_of_range_rejected(self):
        for code in [-1, 256, 1.5]:
            with self.assertRaises(AssertionError):
                code_body(self.original.split('.control\n')[0], code, 0)


if __name__ == '__main__':
    unittest.main()
