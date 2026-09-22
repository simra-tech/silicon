import unittest
from bgr_prefix_parity import select_prefix, compare_prefix_bytes
from prepare_bgr_prefix_probe import require_measurements_inside_prefix


def wave(times, value='1.0'):
    header = (' '.join('v%d' % i for i in range(18))+'\n').encode()
    rows = [(' '.join([str(t)]+[value]*17)+'\n').encode() for t in times]
    return header+b''.join(rows)


class StrictPrefixTests(unittest.TestCase):
    def test_exact_first200ns_different_later_endpoint(self):
        result = compare_prefix_bytes(wave([0, 1e-7, 2e-7, 2.19e-7]), wave([0, 1e-7, 2e-7, 3e-7, 1.02e-6]))
        self.assertTrue(result['status'].startswith('passed'))
        self.assertEqual(result['reference']['row_count'], 3)

    def test_numeric_equal_byte_difference_rejected(self):
        result = compare_prefix_bytes(wave([0, 2e-7, 2.19e-7]), wave([0, 2e-7, 1.02e-6], '1e0'))
        self.assertTrue(result['numeric_rows_exact'])
        self.assertFalse(result['decoded_bytes_exact'])
        self.assertEqual(result['status'], 'failed prefix parity')

    def test_missing_row_rejected(self):
        result = compare_prefix_bytes(wave([0, 1e-7, 2e-7, 2.19e-7]), wave([0, 2e-7, 1.02e-6]))
        self.assertFalse(result['numeric_rows_exact'])

    def test_incomplete_or_nonfinite_rejected(self):
        for raw in [wave([0, 1e-7]), wave([0, 2e-7, 2.19e-7], 'nan')]:
            with self.assertRaises(AssertionError):
                select_prefix(raw)

    def test_header_bytes_required(self):
        raw = wave([0, 2e-7, 2.19e-7])
        result = compare_prefix_bytes(raw, raw.replace(b'v0 v1', b'v0  v1'))
        self.assertTrue(result['numeric_rows_exact'])
        self.assertFalse(result['decoded_bytes_exact'])

    def test_full_endpoint_validates_original_measurement(self):
        self.assertEqual(require_measurements_inside_prefix('meas tran qs_sample find v(q) at=9.402e-7\n',1.02e-6), [('qs_sample', '9.402e-7')])


if __name__ == '__main__':
    unittest.main()
