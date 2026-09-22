#!/usr/bin/env python3
"""Focused unit controls; synthetic values are never extraction evidence."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import unittest

from prepare_capacitance_views import logical_lines, number


class CapacitanceHelpers(unittest.TestCase):
    def test_exact_atto(self):
        self.assertEqual(number('15.5101a'), Decimal('15.5101e-18'))

    def test_exact_femto(self):
        self.assertEqual(number('1.72175f'), Decimal('1.72175e-15'))

    def test_scientific(self):
        self.assertEqual(number('481.031e-18'), Decimal('481.031e-18'))

    def test_zero_preserved(self):
        self.assertEqual(number('0'), Decimal(0))

    def test_nonfinite_rejected(self):
        for text in ('nan', 'NaN', 'inf', '-inf'):
            with self.assertRaises(AssertionError):
                number(text)

    def test_bad_suffix_rejected(self):
        for text in ('1F', '2garbage', '1ff', ''):
            with self.assertRaises(AssertionError):
                number(text)

    def test_continuation_join(self):
        self.assertEqual(logical_lines('M$1 1 2 3 4 model\n+ L=1u W=2u\nCext_1 1 2 1a\n'),
                         ['M$1 1 2 3 4 model L=1u W=2u', 'Cext_1 1 2 1a'])

    def test_orphan_continuation_rejected(self):
        with self.assertRaises(AssertionError):
            logical_lines('+ L=1u')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CapacitanceHelpers)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'status': 'passed' if result.wasSuccessful() else 'failed', 'tests': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors),
              'scope': 'Synthetic helper unit tests only; no capacitor extraction or electrical simulation',
              'inputs': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in
                         (Path(__file__), Path(__file__).parent / 'prepare_capacitance_views.py')}}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
