#!/usr/bin/env python3
"""Source-only negative controls; these do not qualify model runtime fields."""
from pathlib import Path
import unittest
from prepare_loaded_bandwidth_observation import build
from run_loaded_followthrough import get_reference, adverse_deck


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run, ref, prep, expected, op = get_reference('adverse', 'slow')
        cls.source = (ref/'sense.spice').read_text()
        cls.groups = prep['groups']
        cls.old = Path('/results/baseline')
        cls.new = Path('/results/observation')
        cls.deck = adverse_deck((ref/'population_transient.cir').read_text(),
                               cls.old, 'differential', run, prep['groups'])

    def test_exact_inverse_and_count(self):
        deck, ledger = build(self.deck, self.source, self.groups, self.old, self.new)
        self.assertTrue(ledger['source_inverse_exact'])
        self.assertEqual(len(ledger['op_queries']), 190)
        self.assertEqual(len(ledger['vectors']), 18)
        self.assertEqual(deck.split('.control\n')[0], self.deck.split('.control\n')[0])
        self.assertIn('v(xs.xota.out1)', ledger['vectors'])
        self.assertNotIn('v(xs.xota.vbn)', ledger['vectors'])  # Formal port is top iptat.

    def test_missing_device_rejected(self):
        groups = dict(self.groups)
        groups['NON_BGR'] = [q for q in groups['NON_BGR'] if '.xota.xm1.' not in q]
        with self.assertRaises(AssertionError):
            build(self.deck, self.source, groups, self.old, self.new)

    def test_unknown_source_node_rejected(self):
        source = self.source.replace('XM20 out out1 vdd vdd', 'XM20 out unknown vdd vdd')
        with self.assertRaises(AssertionError):
            build(self.deck, source, self.groups, self.old, self.new)

    def test_duplicate_op_rejected(self):
        with self.assertRaises(AssertionError):
            build(self.deck.replace('\nop\n', '\nop\nop\n'), self.source,
                  self.groups, self.old, self.new)


if __name__ == '__main__':
    unittest.main()
