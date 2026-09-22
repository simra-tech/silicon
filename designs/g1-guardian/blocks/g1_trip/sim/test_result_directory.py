import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from result_directory import allocate_run


class ResultDirectory(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.repository = base / 'repo'
        self.sim = self.repository / 'designs/g1/blocks/g1_trip/sim'
        self.sim.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(self.repository)], check=True)
        self.external = base / 'results'
        self.external.mkdir()

    def test_external_link_is_exactly_ignored_and_lexical(self):
        with patch.dict(os.environ, {'G1_RESULTS_ROOT': str(self.external)}):
            result = allocate_run(self.sim, 'new-run')
        self.assertEqual(result, self.sim / 'qualification/new-run')
        self.assertTrue(result.is_symlink())
        self.assertEqual(result.resolve(), self.external / 'g1_trip/new-run')
        self.assertEqual(result.relative_to(self.sim), Path('qualification/new-run'))
        self.assertEqual(subprocess.run(['git', 'check-ignore', '--quiet', str(result)], cwd=self.repository).returncode, 0)
        self.assertEqual(subprocess.run(['git', 'check-ignore', '--quiet', str(result)+'-other'], cwd=self.repository).returncode, 1)

    def test_default_is_plain_local_directory(self):
        with patch.dict(os.environ, {'G1_RESULTS_ROOT': ''}):
            result = allocate_run(self.sim, 'local-run')
        self.assertTrue(result.is_dir())
        self.assertFalse(result.is_symlink())

    def test_nested_existing_public_hierarchy(self):
        with patch.dict(os.environ, {'G1_RESULTS_ROOT': str(self.external)}):
            result = allocate_run(self.sim, 'nested-run', relative_parent='qualification/runs')
        self.assertEqual(result, self.sim / 'qualification/runs/nested-run')
        self.assertTrue(result.is_symlink())
        self.assertEqual(subprocess.run(['git', 'check-ignore', '--quiet', str(result)], cwd=self.repository).returncode, 0)

    def test_invalid_run_hierarchy_rejected(self):
        with self.assertRaises(ValueError):
            allocate_run(self.sim, 'bad-parent', relative_parent='../outside')

    def test_existing_run_is_preserved(self):
        with patch.dict(os.environ, {'G1_RESULTS_ROOT': str(self.external)}):
            result = allocate_run(self.sim, 'existing')
            (result / 'evidence').write_text('retained')
            with self.assertRaises(FileExistsError):
                allocate_run(self.sim, 'existing')
        self.assertEqual((result / 'evidence').read_text(), 'retained')

    def test_parent_traversal_is_rejected_before_writes(self):
        with patch.dict(os.environ, {'G1_RESULTS_ROOT': str(self.external)}):
            with self.assertRaises(ValueError):
                allocate_run(self.sim, '../escape')
        self.assertEqual(list(self.external.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
