"""Pure command and fail-closed controls; no EDA or bulk outputs."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import rebuild_current_rz_candidate as r


class RebuildTests(unittest.TestCase):
    def test_plan_sequence_and_fresh_output(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / 'in'
            root.mkdir()
            out = root / 'fresh'
            with patch.object(r, 'pinned', side_effect=lambda base, spec: base / spec[0]), \
                 patch.object(r.binding, 'sha', return_value=r.projection.ORIGINAL_SHA):
                commands = r.plan(root, out)
                self.assertEqual(len(commands), 7)
                self.assertEqual([Path(c[1]).name for c in commands], [
                    'flatten_current_fill.py', 'prove_rz_recipe_records.py',
                    'keepout_rz_fill.py', 'prove_rz_recipe_records.py',
                    'normalize_rz_port_text.py', 'prove_rz_port_text.py',
                    'prove_rz_recipe_records.py'])
                self.assertIn('--input-record-proof', commands[2])
                self.assertIn('--input-record-proof', commands[4])
                out.mkdir()
                with self.assertRaisesRegex(ValueError, 'fresh'):
                    r.plan(root, out)

    def test_altered_original_rejected(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / 'in'
            root.mkdir()
            with patch.object(r, 'pinned', side_effect=lambda base, spec: base / spec[0]), \
                 patch.object(r.binding, 'sha', return_value='0' * 64):
                with self.assertRaisesRegex(ValueError, 'original native GDS changed'):
                    r.plan(root, root / 'fresh')

    def test_gate_negative_controls(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / 'gate.json'
            now = datetime.now(timezone.utc)
            good = dict(status='passed', checks={k: True for k in r.REQUIRED_CHECKS}, utc=now.isoformat(),
                        coordinated_allocation={'cpus': [0]}, ram_available_bytes=16 * r.GIB,
                        external_allocation={'available_bytes': 2 * r.GIB, 'inodes_free': 1000})
            path.write_text(json.dumps(good))
            self.assertEqual(r.gate_ok(path, 0, now)['status'], 'passed')
            for change, message in [({'status': 'failed'}, 'failed'),
                                    ({'checks': {}}, 'failed'),
                                    ({'coordinated_allocation': {'cpus': [1]}}, 'absent'),
                                    ({'ram_available_bytes': 16 * r.GIB - 1}, 'RAM'),
                                    ({'external_allocation': {'available_bytes': 2 * r.GIB - 1,
                                                               'inodes_free': 1000}}, 'bulk'),
                                    ({'utc': (now - timedelta(seconds=301)).isoformat()}, 'stale')]:
                bad = dict(good, **change)
                path.write_text(json.dumps(bad))
                with self.assertRaisesRegex(ValueError, message):
                    r.gate_ok(path, 0, now)


if __name__ == '__main__':
    unittest.main()
