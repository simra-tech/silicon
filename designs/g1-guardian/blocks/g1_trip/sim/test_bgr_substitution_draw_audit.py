"""Tests for complete OP query contracts; no analog analysis."""
from pathlib import Path
import unittest
from run_bgr_substitution_draw_audit import read_group
from prepare_bgr_substitution_draw_audit import inventory_non_bgr

SIM = Path(__file__).resolve().parent


class DrawAuditContract(unittest.TestCase):
    def test_expanded_source_inventory_includes_caps(self):
        sense = SIM.parents[1] / 'g1_sense/reports/resume-server-20260922/gm4comp3-qualified-source.spice'
        trip = SIM / 'netlist/g1_trip.spice'
        result = inventory_non_bgr(sense.read_text(), trip.read_text())
        self.assertEqual(len(result['queries']), 8670)
        self.assertEqual(len([q for q in result['queries'] if q.startswith('@c.')]), 6)

    def test_ordered_values(self):
        log = 'TEST_BEGIN\n@n.first[w] = 1.000e-06\n@c.second[scale] = 1.0001\nTEST_END\n'
        self.assertEqual(len(read_group(log, 'TEST', ['@n.first[w]', '@c.second[scale]'])), 2)

    def test_missing_cap_query_fails_closed(self):
        with self.assertRaises(AssertionError):
            read_group('TEST_BEGIN\n@n.first[w] = 1e-6\nTEST_END\n', 'TEST', ['@n.first[w]', '@c.second[scale]'])

    def test_nonfinite_query_fails_closed(self):
        with self.assertRaises(AssertionError):
            read_group('TEST_BEGIN\n@c.second[scale] = nan\nTEST_END\n', 'TEST', ['@c.second[scale]'])

    def test_changed_order_fails_closed(self):
        with self.assertRaises(AssertionError):
            read_group('TEST_BEGIN\n@n.second[w] = 1e-6\n@n.first[w] = 1e-6\nTEST_END\n',
                       'TEST', ['@n.first[w]', '@n.second[w]'])


if __name__ == '__main__':
    unittest.main()
