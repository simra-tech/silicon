import unittest
from audit_analog_pad_slew_attribution import validate_violation,source_tables

class Controls(unittest.TestCase):
    def test_exact_and_wrong_violator_rejection(self):
        row='pad07_vdda/pad 3.500000000 200.000000000 -196.499984741 (VIOLATED)'
        nl='sg13g2_IOPadAnalog pad07_vdda (.pad(VDDA));'
        self.assertEqual(validate_violation(row,nl)['reported_slew_ns'],200)
        for bad in [row.replace('200.000000000','201.000000000'),row.replace('/pad ','/c2p '),row.replace('3.500000000','5.000000000')]:
            with self.assertRaises(AssertionError):validate_violation(bad,nl)
        with self.assertRaises(AssertionError):validate_violation(row,nl.replace('IOPadAnalog','IOPadOut4mA'))
    def test_constant_table_and_wrong_value_rejection(self):
        tables=''.join(k+' (delay_template_2x2) {values ("'+','.join([v]*4)+'");}' for k,v in [('rise_transition','200'),('fall_transition','200'),('cell_rise','1000'),('cell_fall','1000')])
        lib='cell (sg13g2_IOPadAnalog) {timing_model_type : "abstracted"; pin (pad) {direction : "inout"; timing () {related_pin : "pad";'+tables+'}} pin (padbare) {direction : "inout";}}'
        self.assertEqual(len(source_tables(lib)),4)
        for bad in [lib.replace('200','201',1),lib.replace('"abstracted"','"nonlinear"'),lib.replace('related_pin : "pad"','related_pin : "c2p"')]:
            with self.assertRaises(AssertionError):source_tables(bad)

if __name__=='__main__':unittest.main()
