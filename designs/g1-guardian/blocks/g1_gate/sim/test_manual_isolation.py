#!/usr/bin/env python3
"""Source-only contract controls, not electrical or hardware qualification."""
from pathlib import Path
import unittest
from prepare_manual_isolation import build, HERE


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (HERE/'campaigns/fet_20260921T151805Z_168cb700/fixture.cir').read_bytes()

    def fixture(self, **overrides):
        args = dict(raw=self.raw, pad_path=Path('/results/pad.spi'),
            core_path=Path('/results/core.spi'),fet_path=Path('/results/fet.lib'),
            output=Path('/results/fixture'),sequence='io_first',closed=False,capacitance=10e-6)
        args.update(overrides)
        return build(**args)

    def test_source_inverse_and_open_not_clamp(self):
        deck, record = self.fixture()
        self.assertTrue(record['source_inverse_exact'])
        self.assertIn('Rdisconnect rawbus bus 10000000',deck)
        self.assertIn('Dfly drain bus fixture_clamp',deck)
        self.assertNotIn('Vbus bus 0 0',deck)
        self.assertNotIn(' uic',deck)
        self.assertIn('XPE en_pad en_core vdd 0 vdda 0 0 G1_VSS_DERIVATIVE__sg13g2_IOPadIn',deck)

    def test_negative_only_switch_changes(self):
        opened, _ = self.fixture()
        closed, report = self.fixture(closed=True)
        self.assertEqual(closed.replace('Rdisconnect rawbus bus 0.01','Rdisconnect rawbus bus 10000000'),opened)
        self.assertEqual(report['prospective_acceptance']['all_window_load_abs_max_A'],.01)

    def test_endpoint_energy_and_units(self):
        for cap in [.1e-6,10e-6]:
            _, record = self.fixture(capacitance=cap)
            self.assertEqual(record['retained_initial_energy_limit_J']['bus_capacitor_max'],.5*cap*.01**2)
        self.assertEqual(.01**2*5*16e-6,8e-9)

    def test_unknown_sequence_or_source_rejected(self):
        for kwargs in [dict(sequence='unknown'),dict(raw=self.raw+b'* modified\n'),dict(capacitance=1e-6)]:
            with self.assertRaises(AssertionError):
                self.fixture(**kwargs)


if __name__=='__main__':
    unittest.main()
