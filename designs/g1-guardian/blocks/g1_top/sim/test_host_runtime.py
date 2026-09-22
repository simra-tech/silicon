"""Host-parity gate must reject incomplete or changed replay evidence."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CHECKER = Path(__file__).with_name('compare_host_runtime.py')

class HostParityTest(unittest.TestCase):
    def check_case(self, change=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = [root / 'reference', root / 'candidate']
            for index, path in enumerate(paths):
                path.mkdir()
                wave = 'time v(a)\n0 0\n4e-6 1\n'
                if index and change == 'value':
                    wave = 'time v(a)\n0 0\n4e-6 1.000000000000001\n'
                if index and change == 'endpoint':
                    wave = 'time v(a)\n0 0\n3e-6 1\n'
                (path / 'observations.tsv').write_text(wave)
                (path / 'run.log').write_text('Unable to open input file.\n' if index and change == 'cosim' else 'Completed\n')
                manifest = {k: 'identity' for k in ['image_id', 'pdk_commit', 'source_deck_sha256',
                    'ngspice_version', 'init_sha256', 'byteorder']}
                manifest.update(status='completed', returncode=0, options={'threads': 2},
                    included_sha256={'source': 'abc'}, model_sha256={'card': 'def'}, rtl_sha256={'rtl': 'ghi'})
                if index and change == 'source':
                    manifest['source_deck_sha256'] = 'changed'
                (path / 'run.json').write_text(json.dumps(manifest))
                assessment = dict(completion='passed', requested_end_s=4e-6,
                    observation_sha256=hashlib.sha256(wave.encode()).hexdigest())
                (path / 'assessment.json').write_text(json.dumps(assessment))
            result = subprocess.run([sys.executable, str(CHECKER), str(paths[0]), str(paths[1]),
                                     '--output', str(root / 'result.json')], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, universal_newlines=True)
            self.assertTrue((root / 'result.json').exists(), result.stderr)
            return result.returncode, json.loads((root / 'result.json').read_text())

    def test_complete_exact_replay(self):
        code, result = self.check_case()
        self.assertEqual(code, 0)
        self.assertEqual(result['mismatched_values'], 0)

    def test_changed_saved_value(self):
        code, result = self.check_case('value')
        self.assertNotEqual(code, 0)
        self.assertEqual(result['mismatched_values'], 1)

    def test_missing_endpoint_despite_pass_label(self):
        code, result = self.check_case('endpoint')
        self.assertNotEqual(code, 0)
        self.assertFalse(result['checks']['candidate_completion'])

    def test_changed_source(self):
        code, result = self.check_case('source')
        self.assertNotEqual(code, 0)
        self.assertFalse(result['checks']['source_deck_sha256_identical'])

    def test_missing_cosimulator_despite_complete_analog(self):
        code, result = self.check_case('cosim')
        self.assertNotEqual(code, 0)
        self.assertFalse(result['checks']['candidate_solver_log_valid'])

if __name__ == '__main__':
    unittest.main()
