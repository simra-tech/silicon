import unittest
from run_joint_calibration import calibration_codes, analysis_arguments
class CalibrationArithmetic(unittest.TestCase):
 def test_positive_correction_raises_dac_and_saturates_hard(self):
  r=calibration_codes({'soft':[147,148],'hard':[147,148]})
  self.assertEqual(r['signed_correction_codes'],{'soft':20,'hard':20})
  self.assertEqual(r['corrected_codes'],{'soft':173,'hard':255})
  self.assertEqual(r['clipped'],{'soft':False,'hard':True})
 def test_negative_correction_and_independent_comparators(self):
  r=calibration_codes({'soft':[107,108],'hard':[117,118]})
  self.assertEqual(r['signed_correction_codes'],{'soft':-20,'hard':-10})
  self.assertEqual(r['corrected_codes'],{'soft':133,'hard':244})
 def test_rounding_at_nominal_interior_point(self):
  r=calibration_codes({'soft':[127,128],'hard':[127,128]})
  self.assertEqual(r['corrected_codes'],{'soft':153,'hard':254})
 def test_signed_overflow_does_not_wrap(self):
  r=calibration_codes({'soft':[255,256],'hard':[255,256]})
  self.assertEqual(r['raw_independent_correction_codes']['soft'],128)
  self.assertEqual(r['signed_correction_codes']['soft'],127)
  self.assertEqual(r['corrected_codes'],{'soft':255,'hard':255})
  self.assertTrue(all(r['clipped'].values()))
class RecoveryArguments(unittest.TestCase):
 def test_only_run_and_watchdog_metadata_may_change(self):
  old=['--run-id','old','--seed','71002','--maxstep-ns','.2','--tight','--gear']
  new=['--run-id','new','--seed','71002','--maxstep-ns','.2','--tight','--gear','--timeout-s','600','--replay-reference','old']
  self.assertEqual(analysis_arguments(old),analysis_arguments(new))
 def test_sample_and_numerical_changes_remain_visible(self):
  old=['--seed','71002','--maxstep-ns','.2','--tight','--gear']
  for changed in [['--seed','71003','--maxstep-ns','.2','--tight','--gear'], ['--seed','71002','--maxstep-ns','.5','--tight','--gear'], ['--seed','71002','--maxstep-ns','.2','--tight']]:
   self.assertNotEqual(analysis_arguments(old),analysis_arguments(changed))
if __name__=='__main__':unittest.main()
