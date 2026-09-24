import unittest
from audit_replaced_expanded_sta import drivers,check_annotation


class AnnotationTests(unittest.TestCase):
    def setUp(self):
        self.instances={'clkload%d'%i:dict(master='sg13g2_buf_1',connections={'A':'clk'}) for i in range(60)}
        self.report='Found 61 unannotated drivers.\n SCLK\n'+''.join(' i_core.u_digital/clkload%d/X\n'%i for i in range(60))+'Found 0 partially unannotated drivers.\n'

    def test_open_outputs_classified_not_top_waived(self):
        self.assertEqual(check_annotation(self.report,self.instances),['SCLK'])

    def test_duplicate_rejected(self):
        with self.assertRaises(AssertionError):drivers(self.report.replace(' SCLK',' i_core.u_digital/clkload0/X'))

    def test_count_mismatch_rejected(self):
        with self.assertRaises(AssertionError):drivers(self.report.replace('Found 61','Found 60'))

    def test_partial_rejected(self):
        with self.assertRaises(AssertionError):drivers(self.report.replace('Found 0 partially','Found 1 partially'))

    def test_connected_dummy_rejected(self):
        self.instances['clkload0']['connections']['X']='real'
        with self.assertRaises(AssertionError):check_annotation(self.report,self.instances)

    def test_foreign_macro_driver_rejected(self):
        with self.assertRaises(AssertionError):check_annotation(self.report.replace('clkload0/X','data/X'),self.instances)


if __name__=='__main__':unittest.main()
