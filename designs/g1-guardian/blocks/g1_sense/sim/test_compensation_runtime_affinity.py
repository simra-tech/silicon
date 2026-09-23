#!/usr/bin/env python3
"""No simulator: exact and negative CPU ownership controls."""
import unittest
from unittest.mock import patch
from compensation_runtime_affinity import verify_cpu


class Controls(unittest.TestCase):
    def test_exact_allowed_slots(self):
        for cpu in [1,6]:
            with patch('compensation_runtime_affinity.os.sched_getaffinity',return_value={cpu}):
                self.assertEqual(verify_cpu(cpu),[cpu])

    def test_reject_wrong_or_shared_affinity(self):
        for expected,observed in [(1,{6}),(6,{1}),(1,{1,6}),(6,{1,6}),(1,set())]:
            with patch('compensation_runtime_affinity.os.sched_getaffinity',return_value=observed):
                with self.assertRaises(AssertionError):verify_cpu(expected)

    def test_reject_unleased_slot(self):
        for cpu in [0,7,45,48]:
            with patch('compensation_runtime_affinity.os.sched_getaffinity',return_value={cpu}):
                with self.assertRaises(AssertionError):verify_cpu(cpu)


if __name__=='__main__':unittest.main()
