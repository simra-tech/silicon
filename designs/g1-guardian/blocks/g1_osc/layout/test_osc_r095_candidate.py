"""Host-only preparation checks, not physical qualification."""
import ast
from pathlib import Path
import tempfile
import unittest

import gen_osc_r095_candidate as candidate
import prepare_osc_r095_lvs as reference


class CandidateTests(unittest.TestCase):
    def test_exact_only_length_change(self):
        source = (candidate.HERE/'gen_osc_layout.py').read_bytes()
        changed = candidate.transformed_source(source)
        self.assertEqual(changed.replace(candidate.NEW, candidate.OLD), source.decode())
        ast.parse(changed)
        self.assertEqual(changed.count(candidate.NEW), 1)

    def test_changed_baseline_rejected(self):
        with self.assertRaises(ValueError):
            candidate.transformed_source(b'changed')

    def test_production_name_rejected(self):
        with self.assertRaises(ValueError):
            candidate.generate(candidate.HERE/'g1_osc.gds')

    def test_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'osc_r095.gds'
            path.touch()
            with self.assertRaises(FileExistsError):
                candidate.generate(path)

    def test_ambiguous_parent_rejected(self):
        with tempfile.TemporaryDirectory(suffix='.gds-parent') as folder:
            with self.assertRaises(ValueError):
                candidate.generate(Path(folder)/'osc_r095.gds')

    def test_native_reference_preserves_segmented_devices(self):
        path = candidate.HERE.parent/'sim/qualification/runs/osc_r095_candidate_shard0_20260921_01/osc.spice'
        text, counts = reference.convert(path.read_bytes())
        self.assertEqual(counts['excluded_baseline_wire_capacitors'], 609)
        self.assertEqual(sum(counts['native_devices'].values()), 81)
        self.assertEqual(text.count('l=55.575u'), 4)
        self.assertNotIn('Cext_', text)
        self.assertIn('.subckt g1_osc en trim[0] trim[1] trim[2] trim[3] osc_clk VDD VSS', text)
        for name in ('RR53', 'RR54', 'RR55', 'RR56'):
            line, = [line for line in text.splitlines() if line.startswith(name+' ')]
            self.assertIn('rppd w=1u l=55.575u', line)

    def test_changed_reference_source_rejected(self):
        with self.assertRaises(ValueError):
            reference.convert(b'changed')


if __name__ == '__main__':
    unittest.main()
