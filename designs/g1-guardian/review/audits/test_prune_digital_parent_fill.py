#!/usr/bin/env python3
import unittest
import pya
from prune_digital_parent_fill import fill_payload


class Controls(unittest.TestCase):
    def fixture(self,datatype=22):
        l=pya.Layout();l.dbu=.001;c=l.create_cell('M2_FILL_CELL')
        c.shapes(l.layer(10,datatype)).insert(pya.Box(0,0,100,100))
        return l,c

    def test_pure_fill(self):
        l,c=self.fixture();info,poly=fill_payload(l,c)
        self.assertEqual((info.layer,info.datatype),(10,22));self.assertEqual(poly.area(),10000)

    def test_functional_drawing_rejected(self):
        l,c=self.fixture(0)
        with self.assertRaises(AssertionError):fill_payload(l,c)

    def test_mixed_cell_rejected(self):
        l,c=self.fixture();c.shapes(l.layer(10,0)).insert(pya.Box(0,0,100,100))
        with self.assertRaises(AssertionError):fill_payload(l,c)

    def test_child_rejected(self):
        l,c=self.fixture();child=l.create_cell('CHILD');c.insert(pya.CellInstArray(child.cell_index(),pya.Trans()))
        with self.assertRaises(AssertionError):fill_payload(l,c)

    def test_repetition_not_clipped(self):
        l,c=self.fixture();top=l.create_cell('TOP')
        i=top.insert(pya.CellInstArray(c.cell_index(),pya.Trans(),pya.Vector(200,0),pya.Vector(0,200),3,2))
        info,poly=fill_payload(l,c);window=pya.Region(pya.Box(250,50,270,70))
        removed=[];kept=[]
        for tr in i.cell_inst.each_cplx_trans():
            p=poly.transformed(tr)
            (kept if (pya.Region(p)&window).is_empty() else removed).append(p)
        self.assertEqual(len(removed),1);self.assertEqual(len(kept),5)
        self.assertEqual(removed[0].area(),10000)


if __name__=='__main__':unittest.main()
