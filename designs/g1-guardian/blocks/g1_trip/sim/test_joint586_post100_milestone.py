import unittest
from audit_joint586_post100_milestone import passed_runtime,SEEDS

class Tests(unittest.TestCase):
    def test_failure_is_not_filtered(self):
        self.assertEqual(len(SEEDS),13);self.assertIn(73115,SEEDS)
    def test_zeroexit_error_and_timeout_rejected(self):
        passed_runtime(dict(status='completed',returncode=0),'JOINT_POPULATION_TRAN_END\n')
        for state,log in [(dict(status='timeout',returncode=0),'JOINT_POPULATION_TRAN_END\n'),
                          (dict(status='completed',returncode=0),'analysis aborted\nJOINT_POPULATION_TRAN_END\n')]:
            with self.assertRaises(AssertionError):passed_runtime(state,log)

if __name__=='__main__':unittest.main()
