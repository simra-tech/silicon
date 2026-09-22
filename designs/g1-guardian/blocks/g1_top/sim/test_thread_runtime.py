import unittest
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from compare_thread_runtime import normalize_init


class ThreadInitTests(unittest.TestCase):
    def test_full_cli_exact_threads_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, threads in [('reference', 2), ('candidate', 1)]:
                path = root / name
                path.mkdir()
                wave = 'time v(a)\n0 0\n4e-6 1\n'
                init = 'osdi fixed\nset num_threads=%d\n' % threads
                (path / 'observations.tsv').write_text(wave)
                (path / '.spiceinit').write_text(init)
                (path / 'run.log').write_text('Complete\n')
                m = {k: 'identity' for k in ['image_id', 'pdk_commit', 'source_deck_sha256', 'ngspice_version', 'byteorder']}
                m.update(status='completed', returncode=0, wall_s=2, options={'threads': threads},
                         init_sha256=hashlib.sha256(init.encode()).hexdigest(), included_sha256={'a': 'b'},
                         model_sha256={'c': 'd'}, rtl_sha256={'e': 'f'})
                (path / 'run.json').write_text(json.dumps(m))
                (path / 'assessment.json').write_text(json.dumps(dict(completion='passed', requested_end_s=4e-6,
                    observation_sha256=hashlib.sha256(wave.encode()).hexdigest())))
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('compare_thread_runtime.py')),
                str(root / 'reference'), str(root / 'candidate'), '--output', str(root / 'result.json')],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((root / 'result.json').read_text())['status'], 'passed')
            self.assertEqual(json.loads((root / 'result_strict_host.json').read_text())['status'], 'failed')

    def test_thread_only_normalization(self):
        self.assertEqual(normalize_init('osdi fixed\nset num_threads=2\n', 2),
                         normalize_init('osdi fixed\nset num_threads=4\n', 4))
        self.assertNotEqual(normalize_init('osdi changed\nset num_threads=2\n', 2),
                            normalize_init('osdi fixed\nset num_threads=4\n', 4))

    def test_missing_duplicate_wrong_thread_rejected(self):
        for text in ['osdi fixed\n', 'set num_threads=1\n',
                     'set num_threads=2\nset num_threads=4\n']:
            with self.assertRaises(ValueError):
                normalize_init(text, 2)


if __name__ == '__main__':
    unittest.main()
