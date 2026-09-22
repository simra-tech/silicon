from pathlib import Path
import tempfile
import unittest
from compare_hot_residual_probes import decision,normalized_deck


class ProspectiveDiagnosticContracts(unittest.TestCase):
    def test_three_unanimous_finite_samples_required(self):
        self.assertIs(decision([0,0,0]),False)
        self.assertIs(decision([1.2,1.2,1.2]),True)
        for values in [[0,1.2,1.2],[.6,.6,.6],[1.2,1.2],[float('inf')]*3,[float('nan')]*3]:
            self.assertIsNone(decision(values))

    def test_only_declared_shunt_and_run_label_can_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for name,value,end in [('reference',.0245,'.52u'),('candidate',.024,'.52u'),('bad',.024,'.53u')]:
                directory=root/name;directory.mkdir()
                (directory/'case.cir').write_text('* shunt input set %s so the soft comparator\nVsh shp 0 dc %s\n.include qualification/%s/sense.spice\n.control\ntran .2n %s\n'%(value,value,name,end))
            reference=normalized_deck(root/'reference','case',.0245)
            self.assertEqual(reference,normalized_deck(root/'candidate','case',.024))
            self.assertNotEqual(reference,normalized_deck(root/'bad','case',.024))
            with self.assertRaises(AssertionError):normalized_deck(root/'candidate','case',.02425)


if __name__=='__main__':unittest.main()
