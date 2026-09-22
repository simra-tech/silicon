"""Output-only replay tests use synthetic bytes, no simulations."""
import unittest
from run_bias_observation_probe import compare_original_columns, quiet_values
from analyze_bias_observation import decompose


class OutputObservationContract(unittest.TestCase):
    def setUp(self):
        self.original = [(' '.join('n%d' % i for i in range(13)) + ' \n').encode(),
                         (' '.join(str(i / 10) for i in range(13)) + ' \n').encode()]
        self.observed = [line[:-1] + b' 1 2 3 4 5\n' for line in self.original]

    def test_exact_projection(self):
        result, data = compare_original_columns(self.original, self.observed)
        self.assertTrue(result['status'].startswith('passed'))
        self.assertEqual(len(data[0]), 18)

    def test_rounded_value_is_not_exact_byte_parity(self):
        self.observed[1] = self.observed[1].replace(b'0.1', b'.10')
        with self.assertRaises(AssertionError):
            compare_original_columns(self.original, self.observed)

    def test_missing_new_vector_rejected(self):
        self.observed[1] = self.observed[1].replace(b' 4 5\n', b' 4\n')
        with self.assertRaises(AssertionError):
            compare_original_columns(self.original, self.observed)

    def test_missing_row_rejected(self):
        with self.assertRaises(AssertionError):
            compare_original_columns(self.original, self.observed[:-1])

    def test_nan_new_vector_rejected(self):
        self.observed[1] = self.observed[1].replace(b' 4 5\n', b' 4 nan\n')
        with self.assertRaises(AssertionError):
            compare_original_columns(self.original, self.observed)

    def test_tagged_quiet_nodes(self):
        nodes = ['vref', 'iptat', 'vref_buf', 'vped', 'shp', 'isense', 'xt.icmp', 'xt.vth_soft', 'xt.vth_hard']
        log = 'BIAS_OBSERVATION_OP\n' + ''.join('v(%s) = 1.0\n' % name for name in nodes) + 'BIAS_OBSERVATION_OP_END\n'
        self.assertEqual(len(quiet_values(log)), 9)
        with self.assertRaises(AssertionError):
            quiet_values(log.replace('v(vped) = 1.0\n', ''))

    def test_nominal_ratio_identity_keeps_all_residuals(self):
        for index in range(20):
            nodes = dict(vref=1.01+index*.001, vref_buf=.99+index*.001,
                         vped=.95, shp=.0245, isense=1.49+index*.001,
                         icmp=.745, vth_soft=.75, vth_hard=.78)
            for channel, code in [('soft', 136), ('hard', 154)]:
                with self.subTest(index=index, channel=channel):
                    result = decompose(nodes, code, channel)
                    self.assertLess(abs(result['identity_reconstruction_error_V']), 2e-15)


if __name__ == '__main__':
    unittest.main()
