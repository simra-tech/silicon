import unittest
from rename_digital_clock_instances import rename_instances
from run_digital_cts_fanout import root_split_tcl


class NameTests(unittest.TestCase):
    def text(self):
        return 'module g1_digital(A,X); input A; output X;\n' + ''.join(
            'wire clkbuf_fanout_split%d_osc_clk;\nsg13g2_buf_16 clkbuf_fanout_split%d_osc_clk (.A(A),.X(clkbuf_fanout_split%d_osc_clk));\n' % (i,i,i)
            for i in (0,1)) + 'endmodule\n'

    def test_two_instances_only(self):
        out, mapping = rename_instances(self.text())
        self.assertEqual(len(mapping), 2)
        self.assertEqual(out.count('_cell'), 2)
        self.assertIn('wire clkbuf_fanout_split0_osc_clk;', out)

    def test_collision_rejected(self):
        with self.assertRaises(AssertionError):
            rename_instances(self.text() + '// clkbuf_fanout_split0_osc_clk_cell\n')

    def test_wrong_output_rejected(self):
        with self.assertRaises(AssertionError):
            rename_instances(self.text().replace('.X(clkbuf_fanout_split0_osc_clk)', '.X(X)'))

    def test_new_cts_names_distinct(self):
        script = root_split_tcl()
        self.assertIn('set inst_name ${name}_cell', script)
        self.assertIn('dbInst_create $::block $master $inst_name', script)
        self.assertIn('dbNet_create $::block $name', script)


if __name__ == '__main__':
    unittest.main()
