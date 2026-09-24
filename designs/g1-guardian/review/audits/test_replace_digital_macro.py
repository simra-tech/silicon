#!/usr/bin/env python3
import unittest
import klayout.db as k
from replace_digital_macro_candidate import cell_signature, protected_cells, equal_macro


class Controls(unittest.TestCase):
    def fixture(self):
        l=k.Layout();l.dbu=.001
        top=l.create_cell('TOP'); macro=l.create_cell('MACRO');shared=l.create_cell('SHARED');inside=l.create_cell('INSIDE')
        top.insert(k.CellInstArray(macro.cell_index(),k.Trans()))
        top.insert(k.CellInstArray(shared.cell_index(),k.Trans(200,0)))
        macro.insert(k.CellInstArray(shared.cell_index(),k.Trans()))
        macro.insert(k.CellInstArray(inside.cell_index(),k.Trans()))
        shared.shapes(l.layer(8,0)).insert(k.Box(0,0,100,100))
        return l,top,macro,shared,inside

    def test_protected_shared_and_external_only(self):
        l,t,m,s,i=self.fixture()
        self.assertEqual(set(protected_cells(t,m)),{'TOP','SHARED'})

    def test_non_target_geometry_change_rejected(self):
        l,t,m,s,i=self.fixture(); before=cell_signature(l,s)
        s.shapes(l.layer(8,0)).insert(k.Box(200,200,300,300))
        self.assertNotEqual(before,cell_signature(l,s))

    def test_non_target_label_change_rejected(self):
        l,t,m,s,i=self.fixture(); before=cell_signature(l,s)
        s.shapes(l.layer(8,25)).insert(k.Text('PORT',k.Trans()))
        self.assertNotEqual(before,cell_signature(l,s))

    def test_root_transform_change_rejected(self):
        l,t,m,s,i=self.fixture();before=cell_signature(l,t)
        next(t.each_inst()).trans=k.Trans(10,10)
        self.assertNotEqual(before,cell_signature(l,t))

    def test_macro_exact_copy(self):
        l,t,m,s,i=self.fixture(); other=k.Layout();other.dbu=l.dbu
        copy=other.create_cell('COPY');copy.copy_tree(m)
        equal_macro(l,m,other,copy)

    def test_macro_metal_change_rejected(self):
        l,t,m,s,i=self.fixture();other=k.Layout();other.dbu=l.dbu
        copy=other.create_cell('COPY');copy.copy_tree(m)
        copy.shapes(other.layer(8,0)).insert(k.Box(40,40,50,150))
        with self.assertRaises(AssertionError):equal_macro(l,m,other,copy)


if __name__=='__main__':unittest.main()
