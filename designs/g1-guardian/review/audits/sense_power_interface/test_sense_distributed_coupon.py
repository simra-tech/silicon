#!/usr/bin/env python3
"""Synthetic analyzer controls; never a simulator or actual model qualification."""
import copy
import math
import unittest
from fractions import Fraction
from analyze_sense_distributed_coupon import audit, inspect_log, normalize_vector, parse_waveform
from prepare_sense_distributed_coupon import prepare


class FakeWave:
    def __init__(self, text): self.text = text
    def read_text(self): return self.text


def rows(wrong=False):
    out = []
    for index in range(13):
        t = index*1.2e-6/12
        p0 = math.sin(index); p1 = .2*math.cos(index)
        model_v = (p0+2*p1)/3; current = .001*math.cos(2*index)
        i0 = (-1 if wrong else 1)*current/3+p0*1e-12
        i1 = 2*current/3+p1*1e-12
        out.append([t, p0, model_v, p0, p1, -current, current, i0, i1, model_v, p0, p1])
    return out


class Controls(unittest.TestCase):
    def test_signed_current_power(self): self.assertEqual(audit(rows())['status'], 'passed')
    def test_wrong_current_sign(self):
        result = audit(rows(True)); self.assertEqual(result['status'], 'failed')
        self.assertGreater(result['signed_current_residual_A'], 1e-12)
        self.assertGreater(result['power_residual_W'], 1e-12)
    def test_nan(self):
        data = rows(); data[2][3] = float('nan'); self.assertEqual(audit(data)['status'], 'failed')
    def test_short(self): self.assertEqual(audit(rows()[:-1])['status'], 'failed')
    def test_reversed_time(self): self.assertEqual(audit(rows()[::-1])['status'], 'failed')
    def test_wrong_voltage(self):
        data = rows(); data[2][2] += .01; self.assertEqual(audit(data)['status'], 'failed')
    def test_missing_vector(self):
        data = rows(); data[2].pop(); self.assertEqual(audit(data)['status'], 'failed')
    def test_contact_offset(self):
        data = rows(); data[2][10] += .01; self.assertEqual(audit(data)['status'], 'failed')
    def test_no_shunt_accounting(self):
        data = rows()
        for row in data: row[7] += 1e-9
        self.assertEqual(audit(data)['status'], 'failed')
    def test_direct(self):
        data = [[r[0], r[2], r[2], -r[6], r[6]] for r in rows()]
        self.assertEqual(audit(data, True)['status'], 'passed')
    def test_swapped_columns_rejected(self):
        with self.assertRaises(AssertionError):
            parse_waveform(FakeWave('time v(m) v(a)\n0 1 2\n'), ['time', 'v(a)', 'v(m)'])
    def test_exact_header_normalization(self):
        self.assertEqual(parse_waveform(FakeWave('time V(a) vdrive#branch\n0 1 2\n'),
                                        ['time', 'v(a)', 'i(Vdrive)']), [[0., 1., 2.]])
        self.assertNotEqual(normalize_vector('v(a)'), normalize_vector('i(a)'))
    def test_unknown_vector_exit_zero_rejected(self):
        self.assertEqual(inspect_log('Warning from check\nError: no such vector v(a)\n') ['status'], 'failed')
    def test_error_after_completed_vectors_rejected(self):
        self.assertEqual(inspect_log('No. of Data Rows: 1200\nError: command failed\n')['status'], 'failed')
    def test_warning_preserved(self):
        result = inspect_log('Warning: generic diagnostic\nNo. of Data Rows: 1200\n')
        self.assertEqual(result['status'], 'passed'); self.assertEqual(len(result['warning_lines']), 1)
    def test_fatal_variants(self):
        for text in ('Fatal: failed', 'doAnalyses: TRAN: failed', 'Timestep too small',
                     'run simulation(s) aborted', 'unknown vector x', 'singular matrix'):
            self.assertEqual(inspect_log(text)['status'], 'failed', text)
    def test_differential_expression_identity(self):
        # Coefficient identity: w0*v0+w1*v1 == v0+w1*(v1-v0)
        # for arbitrary v0/v1 whenever w0+w1=1, including simplex endpoints.
        for w0 in [Fraction(i, 7) for i in range(8)]+[Fraction(1, 3)]:
            w1 = 1-w0
            self.assertEqual((1-w1, w1), (w0, w1))
            for a in range(-4, 5):
                for b in range(-4, 5):
                    v0 = Fraction(a, 7); v1 = Fraction(b, 11)
                    self.assertEqual(w0*v0+w1*v1, v0+w1*(v1-v0))
    def test_only_one_expression_changes(self):
        old = 'Eaverage av 0 POLY(2) p0 0 p1 0 0 {1/3} {2/3}'
        new = 'Eaverage av 0 POLY(2) p0 0 p1 p0 0 1 {2/3}'
        for name in ('direct-zero-r', 'adapter-zero-r', 'distributed-r', 'unequal-voltage', 'wrong-current-sign'):
            before, columns = prepare(name, 'weighted'); after, new_columns = prepare(name, 'differential')
            self.assertEqual(columns, new_columns); self.assertEqual(after.replace(new, old), before)
            self.assertEqual(after.count(new), 0 if name == 'direct-zero-r' else 1)


if __name__ == '__main__': unittest.main()
