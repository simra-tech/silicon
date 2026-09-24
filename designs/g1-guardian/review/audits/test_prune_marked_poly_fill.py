import unittest
import pya
from prune_marked_poly_fill import payload


class Controls(unittest.TestCase):
    def fixture(self, datatype=22):
        layout=pya.Layout();cell=layout.create_cell('POLY_FILL_CELL')
        shape=cell.shapes(layout.layer(5,datatype)).insert(pya.Box(0,0,1000,1000))
        return layout,cell,shape

    def test_pure_fill(self):
        ly,cell,shape=self.fixture();self.assertEqual(payload(ly,cell),shape.polygon)

    def test_functional_poly_rejected(self):
        ly,cell,shape=self.fixture(0)
        with self.assertRaises(AssertionError):payload(ly,cell)

    def test_properties_rejected(self):
        ly,cell,shape=self.fixture();shape.set_property('net','not-floating')
        with self.assertRaises(AssertionError):payload(ly,cell)

    def test_mixed_rejected(self):
        ly,cell,shape=self.fixture();cell.shapes(ly.layer(5,0)).insert(pya.Box(0,0,1,1))
        with self.assertRaises(AssertionError):payload(ly,cell)

    def test_hierarchical_cell_rejected(self):
        ly,cell,shape=self.fixture();other=ly.create_cell('OTHER')
        cell.insert(pya.CellInstArray(other.cell_index(),pya.Trans()))
        with self.assertRaises(AssertionError):payload(ly,cell)


if __name__=='__main__':unittest.main()
