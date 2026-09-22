"""Strict parity checker regression using a preserved completed joint fixture."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from compare_host_replay import SIM, compare
from wave_archive import archive_new_wave, resolve_wave
from analyze_joint_waveforms import analyze


class HostReplay(unittest.TestCase):
    def setUp(self):
        self.reference = SIM / 'qualification/joint-calibrated-pilot-20260921-a-s71001-p00'
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.candidate = Path(self.temporary.name) / 'synthetic-replay'
        self.candidate.mkdir()
        for name in ['provenance.json', 'summary.json', 'sense.spice', 'trip.spice',
                     'bgr.spice', 'hard_+0mV.cir', 'hard_+0mV.dat']:
            shutil.copyfile(self.reference / name, self.candidate / name)
        deck = self.candidate / 'hard_+0mV.cir'
        deck.write_text(deck.read_text().replace(self.reference.name, self.candidate.name))

    def test_exact_distinct_copy_passes(self):
        self.assertEqual(compare(self.reference, self.candidate)['status'], 'passed')

    def test_one_parameter_change_fails(self):
        path = self.candidate / 'summary.json'
        rows = json.loads(path.read_text())
        rows[0]['fingerprints'][0][1] = '0'
        path.write_text(json.dumps(rows))
        result = compare(self.reference, self.candidate)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['checks']['all27_parameters_exact'])

    def test_one_saved_analog_value_change_fails(self):
        path = self.candidate / 'hard_+0mV.dat'
        lines = path.read_text().splitlines()
        row = lines[1].split()
        row[1] = str(float(row[1]) + 1e-8)
        lines[1] = ' '.join(row)
        path.write_text('\n'.join(lines) + '\n')
        result = compare(self.reference, self.candidate)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['checks']['whole_saved_waveform_bytes_exact'])

    def test_reusing_same_directory_is_not_host_parity(self):
        result = compare(self.reference, self.reference)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['checks']['different_run_directories'])

    def test_lossless_archived_copy_has_identical_parity(self):
        wave = self.candidate / 'hard_+0mV.dat'
        with patch.dict('os.environ', {'G1_ARCHIVE_NEW_WAVES': '1'}):
            archive_new_wave(wave)
        self.assertFalse(wave.exists())
        self.assertEqual(compare(self.reference, self.candidate)['status'], 'passed')

    def test_archiving_is_disabled_by_default(self):
        wave = self.candidate / 'hard_+0mV.dat'
        with patch.dict('os.environ', {'G1_ARCHIVE_NEW_WAVES': ''}):
            archive_new_wave(wave)
        self.assertTrue(wave.exists())
        self.assertFalse(Path(str(wave)+'.gz').exists())

    def test_joint_waveform_characterization_identical_after_archive(self):
        before = analyze(self.candidate)
        with patch.dict('os.environ', {'G1_ARCHIVE_NEW_WAVES': '1'}):
            archive_new_wave(self.candidate / 'hard_+0mV.dat')
        self.assertEqual(analyze(self.candidate), before)

    def test_corrupted_archive_is_rejected(self):
        wave = self.candidate / 'hard_+0mV.dat'
        with patch.dict('os.environ', {'G1_ARCHIVE_NEW_WAVES': '1'}):
            archive_new_wave(wave)
        compressed = Path(str(wave) + '.gz')
        with compressed.open('ab') as stream:
            stream.write(b'corruption')
        with self.assertRaises(AssertionError):
            resolve_wave(wave)

    def test_compression_failure_preserves_plain_file(self):
        wave = self.candidate / 'hard_+0mV.dat'
        with patch.dict('os.environ', {'G1_ARCHIVE_NEW_WAVES': '1'}):
            with patch('wave_archive.gzip.GzipFile', side_effect=OSError('synthetic failure')):
                with self.assertRaises(OSError):
                    archive_new_wave(wave)
        self.assertTrue(wave.exists())


if __name__ == '__main__':
    unittest.main()
