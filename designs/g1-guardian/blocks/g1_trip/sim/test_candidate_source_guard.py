import hashlib
from pathlib import Path
import tempfile
import unittest
from run_kickback_qualification import frozen_source_text


class CandidateSourceGuard(unittest.TestCase):
    def test_checked_source_matches_default_text_with_universal_newlines(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.spice'
            raw=b'.subckt test a b\r\nR1 a b 1k\r.ends\n'
            path.write_bytes(raw)
            self.assertEqual(frozen_source_text(path,hashlib.sha256(raw).hexdigest()),path.read_text())

    def test_changed_source_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.spice';path.write_text('changed')
            with self.assertRaises(ValueError):frozen_source_text(path,'0'*64)

    def test_real_frozen_candidate_preserves_literal_consumed_text(self):
        path=Path(__file__).resolve().parents[2]/'g1_sense/reports/resume-server-20260922/gm4comp3-qualified-source.spice'
        self.assertEqual(frozen_source_text(path,'baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'),path.read_text())


if __name__=='__main__':unittest.main()
