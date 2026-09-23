import tempfile
from pathlib import Path
import unittest
from run_dac586_lowcarry_probe import analyze

class Tests(unittest.TestCase):
    def test_timeout_never_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'run.log').write_text('POPULATION_OP_END\n')
            self.assertEqual(analyze(out,{},dict(status='timeout',returncode=0))['numerical_status'],'failed')
    def test_zero_exit_fatal_never_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'run.log').write_text('Error: Timestep too small\nPOPULATION_OP_END\n')
            self.assertEqual(analyze(out,{},dict(status='completed',returncode=0))['numerical_status'],'failed')
    def test_missing_end_never_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'run.log').write_text('Using SPARSE 1.3 as Direct Linear Solver\n')
            self.assertEqual(analyze(out,{},dict(status='completed',returncode=0))['numerical_status'],'failed')

if __name__=='__main__':unittest.main()
