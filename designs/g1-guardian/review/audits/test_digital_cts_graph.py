import unittest
from audit_digital_cts_graph import normalize


def row(master, **connections):
    return dict(master=master, connections=connections)


class GraphTests(unittest.TestCase):
    def test_buffer_contraction_counts_load(self):
        graph, fanout, count = normalize(dict(clkbuf_0=row('sg13g2_buf_8', A='clk', X='c1'),
            clkload0=row('sg13g2_inv_1', A='c1'), ff=row('sg13g2_dfrbpq_1', CLK='c1', D='d', Q='q')))
        self.assertEqual(graph['ff']['connections']['CLK'], 'clk')
        self.assertEqual(fanout, {'clkbuf_0': 2})
        self.assertEqual(count, 1)

    def test_cycle_rejected(self):
        with self.assertRaises(AssertionError):
            normalize(dict(clkbuf_0=row('sg13g2_buf_8', A='c1', X='c2'),
                           clkbuf_1=row('sg13g2_buf_8', A='c2', X='c1')))

    def test_inverter_not_silently_collapsed(self):
        with self.assertRaises(AssertionError):
            normalize(dict(clkbuf_0=row('sg13g2_inv_1', A='clk', X='c1')))

    def test_used_dummy_output_rejected(self):
        with self.assertRaises(AssertionError):
            normalize(dict(clkload0=row('sg13g2_buf_8', A='clk', X='used')))

    def test_changed_data_pin_retained(self):
        before = normalize(dict(ff=row('sg13g2_dfrbpq_1', CLK='clk', D='d', Q='q')))[0]
        after = normalize(dict(ff=row('sg13g2_dfrbpq_1', CLK='clk', D='wrong', Q='q')))[0]
        self.assertNotEqual(before, after)


if __name__ == '__main__':
    unittest.main()
