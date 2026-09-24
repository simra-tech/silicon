#!/usr/bin/env python3
import unittest
import pya
from prepare_digital_reroute_native_hierarchy import hierarchy


class Controls(unittest.TestCase):
    def fixture(self):
        ly=pya.Layout();top=ly.create_cell('TOP');child=ly.create_cell('NATIVE')
        child.shapes(ly.layer(8,0)).insert(pya.Box(0,0,100,100))
        top.insert(pya.CellInstArray(child.cell_index(),pya.Trans()))
        return ly,top,child

    def test_exact_copy_and_orphan_exclusion(self):
        ly,top,c=self.fixture();ly.create_cell('ORPHAN')
        clone=pya.Layout();clone.dbu=ly.dbu;ct=clone.create_cell(top.name);ct.copy_tree(top)
        self.assertEqual(hierarchy(ly,top),hierarchy(clone,ct));self.assertNotIn('ORPHAN',hierarchy(ly,top))

    def test_shape_change_detected(self):
        ly,t,c=self.fixture();old=hierarchy(ly,t);c.shapes(ly.layer(8,0)).insert(pya.Box(200,0,300,100))
        self.assertNotEqual(old,hierarchy(ly,t))

    def test_text_change_detected(self):
        ly,t,c=self.fixture();old=hierarchy(ly,t);c.shapes(ly.layer(8,25)).insert(pya.Text('DIFFERENT',pya.Trans()))
        self.assertNotEqual(old,hierarchy(ly,t))

    def test_transform_change_detected(self):
        ly,t,c=self.fixture();old=hierarchy(ly,t);next(t.each_inst()).trans=pya.Trans(10,0)
        self.assertNotEqual(old,hierarchy(ly,t))

    def test_shape_property_change_detected(self):
        ly,t,c=self.fixture();old=hierarchy(ly,t)
        next(c.shapes(ly.layer(8,0)).each()).set_property(126,'different annotation')
        self.assertNotEqual(old,hierarchy(ly,t))

    def test_property_copy_exact(self):
        ly,t,c=self.fixture();next(c.shapes(ly.layer(8,0)).each()).set_property(126,'native annotation')
        clone=pya.Layout();clone.dbu=ly.dbu;ct=clone.create_cell(t.name);ct.copy_tree(t)
        self.assertEqual(hierarchy(ly,t),hierarchy(clone,ct))


if __name__=='__main__':unittest.main()
