import unittest
from run_dac586_chunk_control import timing


class TimingTests(unittest.TestCase):
    def test_interval_from_byte_observation(self):
        log=b'prefix\nDAC_CHUNK_WARM_BEGIN\nwork\nDAC_CHUNK_WARM_END\n'
        first=log.index(b'work');last=len(log)
        rows=[dict(wall_s=0,log_bytes=0),dict(wall_s=4,log_bytes=7),
              dict(wall_s=5,log_bytes=first),dict(wall_s=9,log_bytes=first+4),
              dict(wall_s=10,log_bytes=last)]
        result=timing(log,rows)
        self.assertEqual(result['initial_two_OP_plus_query_output_wall_s'],[4,5])
        self.assertEqual(result['warm_two_OP_plus_query_output_wall_s'],[4,6])

    def test_missing_end_refuses_time_claim(self):
        with self.assertRaises(AssertionError):
            timing(b'DAC_CHUNK_WARM_BEGIN\n', [dict(wall_s=1,log_bytes=21)])

    def test_duplicate_marker_rejected(self):
        with self.assertRaises(AssertionError):
            timing(b'DAC_CHUNK_WARM_BEGIN\nDAC_CHUNK_WARM_BEGIN\nDAC_CHUNK_WARM_END\n',[])


if __name__=='__main__':unittest.main()
