#!/usr/bin/env python3
"""Reject partial-contact or same-side cuts in the weight-free comparison."""
import unittest
from compare_sense_feed_bridge_cuts import separates_all


class Controls(unittest.TestCase):
    def test_all_inside(self): self.assertTrue(separates_all([2, 3, 4], 9, (2, 4)))
    def test_all_outside(self): self.assertTrue(separates_all([2, 3, 4], 9, (8, 10)))
    def test_partial_inside(self): self.assertFalse(separates_all([2, 3, 4], 9, (3, 4)))
    def test_same_inside(self): self.assertFalse(separates_all([2, 3, 4], 3, (2, 4)))
    def test_same_outside(self): self.assertFalse(separates_all([2, 3, 4], 9, (5, 7)))
    def test_duplicate_nodes(self): self.assertTrue(separates_all([2, 2, 3], 9, (2, 3)))
    def test_missing_contacts(self):
        with self.assertRaises(AssertionError): separates_all([], 9, (2, 3))
    def test_unsorted(self):
        with self.assertRaises(AssertionError): separates_all([3, 2], 9, (2, 3))


if __name__ == '__main__': unittest.main()
