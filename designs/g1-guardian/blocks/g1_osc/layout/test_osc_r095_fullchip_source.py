import unittest
import prepare_osc_r095_fullchip_source as candidate


class Controls(unittest.TestCase):
    def fixture(self):
        return '* before\n' + candidate.HEADER + ''.join(candidate.OLD) + 'XOTHER a b other\n.ends\n* after\n' + candidate.OLD[0]

    def test_only_two_lines_inside_target_change(self):
        source = self.fixture()
        expected = source.replace(candidate.HEADER + ''.join(candidate.OLD),
                                  candidate.HEADER + ''.join(candidate.NEW))
        self.assertEqual(candidate.rewrite_block(source), expected)

    def test_wrong_or_ambiguous_interface_rejected(self):
        for source in [self.fixture().replace('trim[0]', 'wrong'),
                       self.fixture() + candidate.HEADER]:
            with self.assertRaises(AssertionError):
                candidate.rewrite_block(source)

    def test_missing_or_duplicate_resistor_rejected(self):
        for source in [self.fixture().replace(candidate.OLD[1], ''),
                       self.fixture().replace(candidate.OLD[1], candidate.OLD[1] * 2)]:
            with self.assertRaises(AssertionError):
                candidate.rewrite_block(source)

    def test_unpinned_source_rejected(self):
        with self.assertRaises(AssertionError):
            candidate.convert(self.fixture().encode())


if __name__ == '__main__':
    unittest.main()
