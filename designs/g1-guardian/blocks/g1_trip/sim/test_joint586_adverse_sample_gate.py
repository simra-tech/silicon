import unittest
from audit_joint586_adverse_calibration import first_sample_gate,validate_passed_runtime


class FirstSample(unittest.TestCase):
    def fixture(self):
        leaves=[dict(kind=k,status='passed') for k in ['calibration']*10+['guard']*40+['residual']*20]
        row=dict(evidence_status='passed',complete=True,bracket_status='passed selected probes',leaves=leaves,
            status='failed electrical or numerical check',qualified_control_seed_variation={
                'all':dict(primitive_count=3500,primitives_with_changed_values=3500)})
        return dict(status='passed read-only evidence audit',requested_samples=1,completed_samples=1,records=[row])

    def test_valid_electrical_failure_retained_without_blocking_characterization(self):
        self.assertTrue(first_sample_gate(self.fixture()))

    def test_numerical_failure_blocks(self):
        r=self.fixture();r['records'][0]['leaves'][0]['status']='failed'
        self.assertFalse(first_sample_gate(r))

    def test_incomplete_condition_matrix_blocks(self):
        r=self.fixture();r['records'][0]['leaves'].pop()
        self.assertFalse(first_sample_gate(r))

    def test_unqualified_realization_blocks(self):
        r=self.fixture();r['records'][0]['qualified_control_seed_variation']['all']['primitives_with_changed_values']=3499
        self.assertFalse(first_sample_gate(r))

    def test_exit_zero_with_timestep_error_is_rejected(self):
        state=dict(status='completed',returncode=0,wall_s=5)
        entry=dict(watchdog_status='completed',returncode=0,wall_s=5,errors=[])
        with self.assertRaises(AssertionError):
            validate_passed_runtime(state,entry,'doAnalyses: TRAN: Timestep too small\nJOINT_POPULATION_TRAN_END\n')

    def test_timeout_marked_passed_is_rejected(self):
        state=dict(status='timeout',returncode=-15,wall_s=1200)
        entry=dict(watchdog_status='completed',returncode=0,wall_s=1200,errors=[])
        with self.assertRaises(AssertionError):validate_passed_runtime(state,entry,'JOINT_POPULATION_TRAN_END\n')

    def test_missing_end_marker_is_rejected(self):
        state=dict(status='completed',returncode=0,wall_s=5)
        entry=dict(watchdog_status='completed',returncode=0,wall_s=5,errors=[])
        with self.assertRaises(AssertionError):validate_passed_runtime(state,entry,'')


if __name__=='__main__':unittest.main()
