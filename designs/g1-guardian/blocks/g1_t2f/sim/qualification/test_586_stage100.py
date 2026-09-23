import unittest
from audit_586_stage100 import terminal_outcome, isolated_watchdog


class Stage100Tests(unittest.TestCase):
    def test_completed_failures_are_retained_but_running_is_not_terminal(self):
        self.assertTrue(terminal_outcome({'status':'failed original linear calibration'}))
        self.assertTrue(terminal_outcome({'status':'failed numerical leaf'}))
        for status in [None,'running','not run','paused before next leaf; remaining conditions not run']:
            self.assertFalse(terminal_outcome({'status':status}))

    def test_only_original_isolated_watchdog_gets_numerical_disposition(self):
        runtime = dict(status='timeout',timeout_s=600,returncode=-15)
        self.assertTrue(isolated_watchdog(runtime,dict(runtime=runtime,errors=[])))
        self.assertFalse(isolated_watchdog(runtime,dict(runtime=runtime,errors=['parameter mismatch'])))
        for changed in [dict(runtime,status='completed',returncode=0),dict(runtime,timeout_s=1200)]:
            self.assertFalse(isolated_watchdog(changed,dict(runtime=changed,errors=[])))


if __name__ == '__main__':
    unittest.main()
