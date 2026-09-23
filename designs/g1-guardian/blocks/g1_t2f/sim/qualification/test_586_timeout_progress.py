import unittest
from analyze_586_timeout_progress import assess


class Progress(unittest.TestCase):
    def test_advancing_and_cpu(self):
        rows=[dict(wall_s=t,last_reported_sim_time_s=t*1e-8,cpu_ticks=[str(t*90),'0']) for t in range(601)]
        r=assess(rows,100)
        self.assertAlmostEqual(r['simulated_seconds_per_wall_second'],1e-8)
        self.assertAlmostEqual(r['process_cpu_to_wall_ratio'],.9)

    def test_stuck_no_cpu_not_invented(self):
        rows=[dict(wall_s=t,last_reported_sim_time_s=1e-6) for t in range(601)]
        r=assess(rows,100)
        self.assertEqual(r['longest_unchanged_reported_time_interval_s'],60)
        self.assertNotIn('linear_remaining_wall_s_at_observed_slope',r)
        self.assertTrue(r['process_cpu_status'].startswith('not run'))


if __name__=='__main__':unittest.main()
