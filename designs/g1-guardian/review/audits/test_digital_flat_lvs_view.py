#!/usr/bin/env python3
import unittest
import klayout.db as k
from prepare_digital_flat_lvs_view import verify_geometry


def fixture():
    layout = k.Layout(); layout.dbu = .001
    top = layout.create_cell('TOP'); child = layout.create_cell('INV')
    metal = layout.layer(8, 0); label = layout.layer(8, 25)
    child.shapes(metal).insert(k.Box(0, 0, 100, 100))
    child.shapes(label).insert(k.Text('A', k.Trans(0, 0)))
    top.insert(k.CellInstArray(child.cell_index(), k.Trans(20, 20)))
    top.shapes(label).insert(k.Text('PORT', k.Trans(20, 20)))
    return layout, top, child, metal, label


class Controls(unittest.TestCase):
    def pair(self):
        source, original, _, _, _ = fixture()
        out, top, child, metal, label = fixture()
        child.shapes(label).clear(); top.flatten(-1, True)
        return source, original, out, top, metal, label

    def test_exact_geometry_and_top_text(self):
        a,b,c,d,_,_ = self.pair(); verify_geometry(a,b,c,d)

    def test_added_metal_rejected(self):
        a,b,c,d,m,_ = self.pair(); d.shapes(m).insert(k.Box(30,30,150,150))
        with self.assertRaises(AssertionError): verify_geometry(a,b,c,d)

    def test_missing_metal_rejected(self):
        a,b,c,d,m,_ = self.pair(); d.shapes(m).clear()
        with self.assertRaises(AssertionError): verify_geometry(a,b,c,d)

    def test_top_text_change_rejected(self):
        a,b,c,d,_,t = self.pair(); d.shapes(t).clear()
        with self.assertRaises(AssertionError): verify_geometry(a,b,c,d)

    def test_promoted_child_text_rejected(self):
        a,b,c,d,_,t = self.pair(); d.shapes(t).insert(k.Text('A',k.Trans(20,20)))
        with self.assertRaises(AssertionError): verify_geometry(a,b,c,d)

    def test_missing_empty_layer_allowed(self):
        a,b,c,d,_,_ = self.pair(); a.layer(999,0)
        verify_geometry(a,b,c,d)

    def test_missing_nonempty_layer_rejected(self):
        a,b,c,d,_,_ = self.pair(); b.shapes(a.layer(999,0)).insert(k.Box(1,1,10,10))
        with self.assertRaises(AssertionError): verify_geometry(a,b,c,d)


if __name__ == '__main__':
    unittest.main()
