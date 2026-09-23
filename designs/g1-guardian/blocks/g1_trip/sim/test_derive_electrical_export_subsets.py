import unittest
from derive_electrical_export_subsets import derive

class Controls(unittest.TestCase):
    def data(self):return dict(status='passed read-only evidence audit',requested_samples=100,completed_samples=100,auditor_sha256='source',
        records=[dict(seed=s,complete=True,status='failed' if s==74193 else 'passed') for s in range(74101,74201)])
    def test_exact55_includes_failure(self):
        d=self.data();r=derive(d,'t2f-fixed55','parent')
        self.assertEqual(r['records'],d['records'][45:]);self.assertEqual(r['failed_complete_samples'],1)
    def test_missing_complete_blocks(self):
        d=self.data();d['records'][0]['complete']=False
        with self.assertRaises(AssertionError):derive(d,'t2f-fixed55','parent')
    def test_changed_order_blocks(self):
        d=self.data();d['records'].reverse()
        with self.assertRaises(AssertionError):derive(d,'t2f-fixed55','parent')
    def test_slow_gate_required(self):
        d=dict(status='passed read-only evidence audit',requested_samples=1,completed_samples=1,auditor_sha256='a',first_sample_gate_passed=False,records=[dict(seed=77101,corner='slow',complete=True,status='passed fullcalibration guard residual')])
        with self.assertRaises(AssertionError):derive(d,'slow-firstsample','parent')
        d['first_sample_gate_passed']=True;self.assertEqual(derive(d,'slow-firstsample','parent')['fully_passed_samples'],1)

if __name__=='__main__':unittest.main()
