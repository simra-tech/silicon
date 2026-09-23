import unittest
from audit_digital_routed_sta import annotation_control


class AnnotationControl(unittest.TestCase):
    def setUp(self):
        self.instances = {'clkload%d'%i:dict(master='sg13g2_buf_1', connections={'A':'clk'}) for i in range(60)}
        self.report = 'Found 60 unannotated drivers.\n'+''.join(' clkload%d/X\n'%i for i in range(60))+'Found 0 partially unannotated drivers.\n'

    def test_complete(self):
        self.assertEqual(annotation_control(self.report, self.instances), 60)

    def test_foreign_driver(self):
        with self.assertRaises(AssertionError):
            annotation_control(self.report.replace('clkload0/X', 'data/X'), self.instances)

    def test_connected_output(self):
        self.instances['clkload0']['connections']['X'] = 'data'
        with self.assertRaises(AssertionError):
            annotation_control(self.report, self.instances)

    def test_wrong_output(self):
        with self.assertRaises(AssertionError):
            annotation_control(self.report.replace('clkload0/X', 'clkload0/Y'), self.instances)

    def test_partial(self):
        with self.assertRaises(AssertionError):
            annotation_control(self.report.replace('Found 0 partially', 'Found 1 partially'), self.instances)

    def test_duplicate(self):
        with self.assertRaises(AssertionError):
            annotation_control(self.report.replace('clkload0/X', 'clkload1/X'), self.instances)


if __name__ == '__main__':
    unittest.main()
