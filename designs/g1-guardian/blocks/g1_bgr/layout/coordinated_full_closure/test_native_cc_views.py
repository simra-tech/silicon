#!/usr/bin/env python3
"""Exact native-fF conversion controls, including smallest positive binary64."""
from decimal import Decimal, localcontext
import math
import unittest
from prepare_native_cc_views import exact_farads


class NativeValues(unittest.TestCase):
    def test_exact_roundtrip(self):
        values = [0.0, float.fromhex('0x0.0000000000001p-1022'), 1e-300,
                  0.0012345678912345678, 1.0, 12345678.901234567, float.fromhex('0x1.fffffffffffffp+1023')]
        with localcontext() as context:
            context.prec = 1200
            for value in values:
                self.assertEqual(float(Decimal(exact_farads(value)) * Decimal('1e15')).hex(), value.hex())

    def test_invalid_rejected(self):
        for value in (-1.0, math.inf, -math.inf, math.nan):
            with self.assertRaises(AssertionError):
                exact_farads(value)


if __name__ == '__main__':
    unittest.main()
