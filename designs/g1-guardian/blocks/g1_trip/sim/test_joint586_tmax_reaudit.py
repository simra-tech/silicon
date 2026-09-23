"""Representation controls; no numerical or acceptance transformation."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from wave_archive import archive_new_wave,open_wave,resolve_wave


class Tests(unittest.TestCase):
    def test_plain_and_verified_archive_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'wave.dat';blob=b'time v(a)\n0 1\n1 2\n';path.write_bytes(blob)
            with open_wave(path,'rb') as stream:self.assertEqual(stream.read(),blob)
            with patch.dict(os.environ,{'G1_ARCHIVE_NEW_WAVES':'1'}):archive_new_wave(path)
            self.assertFalse(path.exists());self.assertEqual(resolve_wave(path).suffix,'.gz')
            with open_wave(path,'rb') as stream:self.assertEqual(stream.read(),blob)

    def test_corrupt_archive_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'wave.dat';path.write_bytes(b'time v(a)\n0 1\n')
            with patch.dict(os.environ,{'G1_ARCHIVE_NEW_WAVES':'1'}):archive_new_wave(path)
            Path(str(path)+'.gz').write_bytes(b'corrupted')
            with self.assertRaises(AssertionError):resolve_wave(path)


if __name__=='__main__':unittest.main()
