"""Streaming evidence must distinguish recoverable records from completed runs."""
import pathlib,struct,tempfile,unittest
from run_stream import read_raw,normal_name
class RawEvidenceTests(unittest.TestCase):
 def fixture(self,points,rows,extra=b''):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=pathlib.Path(t.name)/'raw'
  h=f'Title: fixture\nFlags: real\nNo. Variables: 2\nNo. Points: {points}\nVariables:\n\t0\ttime\ttime\n\t1\ti(v1)\tcurrent\nBinary:\n'
  p.write_bytes(h.encode()+b''.join(struct.pack('=dd',*r) for r in rows)+extra);return p
 def test_incomplete_header_retains_complete_records(self):
  names,rows,meta=read_raw(self.fixture('',[(0,1),(1e-6,2)],b'abc'))
  self.assertEqual(meta['complete_records'],2);self.assertIsNone(meta['declared_points']);self.assertEqual(meta['trailing_bytes'],3)
 def test_complete_header_and_current_names(self):
  names,rows,meta=read_raw(self.fixture('2',[(0,1),(1e-6,2)]))
  self.assertEqual(meta['declared_points'],2);self.assertEqual(normal_name('v1#branch'),'i(v1)');self.assertEqual(normal_name(names[1]),'i(v1)')
 def test_nonfinite_rejected(self):
  with self.assertRaises(ValueError):read_raw(self.fixture('1',[(0,float('nan'))]))
 def test_reversed_time_rejected(self):
  with self.assertRaises(ValueError):read_raw(self.fixture('3',[(0,1),(2e-6,2),(1e-6,3)]))
if __name__=='__main__':unittest.main()
