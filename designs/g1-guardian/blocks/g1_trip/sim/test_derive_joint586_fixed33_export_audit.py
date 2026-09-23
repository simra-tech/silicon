import unittest
from derive_joint586_fixed33_export_audit import derive

class ExactProjection(unittest.TestCase):
    def audit(self):
        rows=[dict(seed=s,run=str(s),complete=True,status='failed calibration' if s==73095 else 'passed fullcalibration guard residual') for s in range(73001,73101)]
        return dict(status='passed read-only evidence audit',records=rows,requested_samples=100,completed_samples=100,fully_passed_samples=99,failed_completed_samples=1,auditor_sha256='source')
    def test_all_original_failures_retained(self):
        source=self.audit();result=derive(source,'parent');self.assertEqual(result['records'],source['records'][67:]);self.assertEqual(result['failed_completed_samples'],1)
    def test_missing_or_duplicate_rejected(self):
        for duplicate in [False,True]:
            source=self.audit()
            if duplicate:source['records'][-1]=source['records'][-2]
            else:source['records'].pop()
            with self.assertRaises(AssertionError):derive(source,'parent')
    def test_incomplete_rejected(self):
        source=self.audit();source['records'][-1]['complete']=False
        with self.assertRaises(AssertionError):derive(source,'parent')

if __name__=='__main__':unittest.main()
