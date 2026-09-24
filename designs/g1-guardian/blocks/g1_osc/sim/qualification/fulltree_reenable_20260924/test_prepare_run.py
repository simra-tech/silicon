import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import prepare_run as fixture


class PreparationTests(unittest.TestCase):
    def test_both_exact_saved_inputs(self):
        for case in ('nominal', 'slowhot'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary) / 'run'
                result = fixture.prepare(case, target)
                manifest = json.loads((fixture.HERE / (case + '_manifest.json')).read_text())
                for name, digest in result['inputs_sha256'].items():
                    self.assertEqual(hashlib.sha256((target / name).read_bytes()).hexdigest(), digest)
                    self.assertEqual(digest, manifest['input_bindings'][name])
                self.assertFalse((target / 'receiver.dat').exists())

    def test_existing_directory_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileExistsError):
                fixture.prepare('nominal', Path(temporary))

    def test_unknown_case_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(KeyError):
                fixture.prepare('unknown', Path(temporary) / 'new')


if __name__ == '__main__':
    unittest.main()
