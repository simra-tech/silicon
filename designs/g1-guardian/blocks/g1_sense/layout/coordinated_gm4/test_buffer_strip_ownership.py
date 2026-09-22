#!/usr/bin/env python3
"""Exercise endpoint and internal adjacency without PCells or saved geometry."""
import unittest
from buffer_strip_ownership import drain_owner

class DrainOwnershipTest(unittest.TestCase):
    def check_owners(self, owners):
        for strip in range(1, len(owners)+1, 2):
            adjacent=owners[max(0,strip-1):min(len(owners),strip+1)]
            self.assertTrue(adjacent)
            self.assertEqual(len(set(adjacent)), 1)
            self.assertEqual(drain_owner(owners,strip), adjacent[0])

    def test_nf1_endpoint(self):
        self.check_owners(['M'])
        self.assertEqual(drain_owner(['M'],1),'M')

    def test_nf3_endpoint_and_internal(self):
        self.check_owners(['M']*3)
        self.assertEqual(drain_owner(['M']*3,3),'M')

    def test_even_native_arrays(self):
        for nf in (2,4,16,64):
            self.check_owners(['M']*nf)

    def test_even_complementary_split_arrays(self):
        for nf in (16,64):
            for pattern in ('ABBA','BAAB'):
                groups=pattern*(nf//8)
                owners=[groups[gate//2] for gate in range(nf)]
                self.check_owners(owners)
                self.assertEqual(owners.count('A'),nf//2)
                self.assertEqual(owners.count('B'),nf//2)

if __name__=='__main__':unittest.main()
