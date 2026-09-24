import hashlib
import tempfile
import unittest
from pathlib import Path

import prepare_run as fixture


class PreparationTests(unittest.TestCase):
    def check_case(self, case):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'run'
            result = fixture.prepare(case, target)
            self.assertEqual(len(result['inputs_sha256']), 5)
            for name, digest in result['inputs_sha256'].items():
                self.assertEqual(hashlib.sha256((target / name).read_bytes()).hexdigest(), digest)
            self.assertFalse((target / 'receiver.dat').exists())

    def test_nominal_zero(self):
        self.check_case('nominal_code0')

    def test_nominal_eight(self):
        self.check_case('nominal_code8')

    def test_slowhot_zero(self):
        self.check_case('slowhot_code0')

    def test_slowhot_fifteen(self):
        self.check_case('slowhot_code15')

    def test_existing_destination_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileExistsError):
                fixture.prepare('nominal_code0', Path(temporary))

    def test_unknown_case_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'never-created'
            with self.assertRaises(KeyError):
                fixture.prepare('unknown', target)
            self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
