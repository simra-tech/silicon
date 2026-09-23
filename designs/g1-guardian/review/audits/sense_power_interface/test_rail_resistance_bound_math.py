#!/usr/bin/env python3
"""Analytic controls only; no actual SENSE graph/current solve."""
from fractions import Fraction as F
import unittest
from rail_resistance_bound_math import graph_bounds, balanced_positive_budget


class Controls(unittest.TestCase):
    def test_line(self):
        r=graph_bounds([0,1,2],[(0,1,2),(1,2,3)])
        self.assertEqual(r['tree_diameter_upper_ohm'],5)
        self.assertEqual(r['bridge_diameter_lower_ohm'],3)
    def test_parallel(self):
        r=graph_bounds([0,1],[(0,1,10),(0,1,20)])
        self.assertEqual(r['tree_diameter_upper_ohm'],10)
        self.assertEqual(r['bridge_diameter_lower_ohm'],F(20,3))
    def test_triangle(self):
        r=graph_bounds([0,1,2],[(0,1,1),(1,2,1),(2,0,1)])
        self.assertEqual(r['tree_diameter_upper_ohm'],2)
        self.assertEqual(r['bridge_diameter_lower_ohm'],0)
        self.assertLess(F(2,3),r['tree_diameter_upper_ohm'])
    def test_disconnected(self):
        with self.assertRaises(AssertionError):graph_bounds([0,1,2],[(0,1,1)])
    def test_invalid_resistance(self):
        for value in (0,-1):
            with self.assertRaises(AssertionError):graph_bounds([0,1],[(0,1,value)])
    def test_signed_cancellation(self):
        self.assertEqual(balanced_positive_budget([1,-1,2,-2]),3)
        self.assertEqual(sum([1,-1,2,-2]),0)  # Signed total is not an absolute-current bound.
    def test_missing_external_current(self):
        with self.assertRaises(AssertionError):balanced_positive_budget([1,2])
    def test_return_and_circulation(self):
        self.assertEqual(balanced_positive_budget([1,-1]),1)
        self.assertEqual(balanced_positive_budget([1,-1,5,-5]),6)
    def test_exact_binary64_sums(self):
        r=graph_bounds([0,1,2],[(0,1,.1),(1,2,.2)])
        self.assertEqual(r['tree_diameter_upper_ohm'],F(.1)+F(.2))
    def test_bridge_partition_intervals(self):
        nodes=set(range(6));edges=[(0,1,1),(1,2,1),(2,0,1),(2,3,2),(3,4,3),(3,4,4),(0,5,1)]
        r=graph_bounds(nodes,edges)
        self.assertEqual(len(r['bridges']),3)
        for bridge in r['bridges']:
            cut=set(bridge['nodes']);reached={bridge['nodes'][0]};changed=True
            while changed:
                changed=False
                for a,b,_ in edges:
                    if {a,b}==cut:continue
                    if a in reached and b not in reached:reached.add(b);changed=True
                    if b in reached and a not in reached:reached.add(a);changed=True
            first,last=bridge['descendant_discovery_interval']
            reported={n for n,index in r['node_discovery'].items() if first<=index<=last}
            self.assertTrue(reported==reached or reported==nodes-reached)


if __name__=='__main__':unittest.main()
