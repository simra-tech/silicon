import tempfile
import unittest
from pathlib import Path
from run_dac586_static_control import fatal_errors, read_op, compare_columns, analyze


class RuntimeTests(unittest.TestCase):
    def test_fatal_even_exit_zero(self):
        for text in ['Error: missing', 'doAnalyses: bad', 'analysis aborted', 'timestep too small', 'no such vector']:
            self.assertTrue(fatal_errors(text))

    def test_op_header_and_finite_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'op.dat'
            for text in ['scale wrong\n0 1\n', 'scale v(a)\n0 nan\n', 'scale v(a)\n0 1\n0 2\n']:
                path.write_text(text)
                with self.assertRaises(AssertionError):
                    read_op(path, ['scale', 'v(a)'])

    def test_numeric_equal_not_decoded_byte_equal(self):
        a = ([[b'scale', b'v(a)'], [b'0', b'1.0']], [0., 1.])
        b = ([[b'scale', b'v(a)'], [b'0', b'1.00']], [0., 1.])
        result = compare_columns(a, b, 2)
        self.assertTrue(result['numeric_rows_exact'])
        self.assertFalse(result['decoded_column_token_bytes_exact'])

    def test_exit_zero_error_and_timeout_never_pass(self):
        prep = dict(seed=73001, codes=[135,151], temperatures_C=[25], scope='test', physical_scope='test')
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            for status, log in [('completed', 'analysis aborted\nPOPULATION_OP_END\n'), ('timeout', 'POPULATION_OP_END\n')]:
                (out/'run.log').write_text(log)
                result = analyze(out, prep, dict(status=status, returncode=0, wall_s=1))
                self.assertEqual(result['status'], 'failed')

    def test_post_numerical_audit_error_never_passes(self):
        prep = dict(seed=73001, codes=[135,151], temperatures_C=[25], scope='test', physical_scope='test',
                    expected_full_parameters=[])
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            (out/'run.log').write_text('POPULATION_OP_END\n')
            result = analyze(out, prep, dict(status='completed', returncode=0, wall_s=1))
            self.assertEqual(result['solver_status'], 'passed')
            self.assertEqual(result['status'], 'failed')
            self.assertTrue(result['errors'])


if __name__ == '__main__':
    unittest.main()
