"""Guard against simulating stale or ambiguous physical-candidate estimates."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from sense_route_manifest import load_candidate_resistances


class CandidateManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.gds = self.directory / 'g1_chip_top.gds'
        self.gds.write_bytes(b'geometry fixture')
        self.path = self.directory / 'manifest.json'
        self.data = {'candidate_sha256': hashlib.sha256(self.gds.read_bytes()).hexdigest(),
                     'routes': [{'net': 'P', 'total_R_ohm_estimate': 20.51836},
                                {'net': 'N', 'total_R_ohm_estimate': 20.587576}]}

    def load(self):
        self.path.write_text(json.dumps(self.data))
        return load_candidate_resistances(self.path)

    def test_preserves_distinct_branch_estimates(self):
        self.assertEqual(self.load()[1], {'P': 20.51836, 'N': 20.587576})

    def test_changed_gds_cannot_reuse_old_estimates(self):
        self.gds.write_bytes(b'changed geometry fixture')
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            self.load()

    def test_duplicate_branch_does_not_silently_override(self):
        self.data['routes'].append({'net': 'P', 'total_R_ohm_estimate': 1})
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            self.load()

    def test_invalid_resistance_rejected(self):
        for value in (float('nan'), float('inf'), -1, 0, True, '20'):
            with self.subTest(value=value):
                self.data['routes'][0]['total_R_ohm_estimate'] = value
                with self.assertRaises(ValueError):
                    self.load()


if __name__ == '__main__':
    unittest.main()
