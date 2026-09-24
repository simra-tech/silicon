import unittest
import klayout.db as k
from replace_sense_only_candidate import replace, protected, root_without, structural_digest


class Controls(unittest.TestCase):
    def fixture(self):
        def macro(name, width):
            layout=k.Layout();layout.dbu=.001;top=layout.create_cell(name)
            child=layout.create_cell(name+'_child')
            child.shapes(layout.layer(8,0)).insert(k.Box(0,0,width,1000))
            child.shapes(layout.layer(8,2)).insert(k.Text('pin',k.Trans(0,0)))
            top.insert(k.CellInstArray(child.cell_index(),k.Trans()))
            return layout,top
        old,oc=macro('old',1000);new,nc=macro('new',1200)
        ly=k.Layout();ly.dbu=.001;top=ly.create_cell('parent')
        top.shapes(ly.layer(189,4)).insert(k.Box(-10000,-10000,10000,10000))
        target=ly.create_cell('target');target.copy_tree(oc)
        top.insert(k.CellInstArray(target.cell_index(),k.Trans(100,200)))
        other=ly.create_cell('other');other.shapes(ly.layer(10,0)).insert(k.Box(5,5,10,10))
        top.insert(k.CellInstArray(other.cell_index(),k.Trans()))
        return ly,top,old,oc,new,nc

    def execute(self, data, transform='r0 *1 100,200'):
        ly,top,old,oc,new,nc=data
        return replace(ly,top,'target',transform,old,oc,new,nc)

    def test_positive_nested_identity_and_root(self):
        data=self.fixture();ly,top,old,oc,new,nc=data
        root=root_without(top,set());held=protected(top,{'target'})
        self.execute(data)
        self.assertEqual(root_without(top,set()),root)
        self.assertEqual(protected(top,{'target'}),held)
        self.assertEqual(structural_digest(ly.cell('target')),structural_digest(nc))

    def test_wrong_transform_rejected(self):
        with self.assertRaises(AssertionError):self.execute(self.fixture(),'r0 *1 101,200')

    def test_old_geometry_rejected(self):
        data=self.fixture();ly=data[0]
        ly.cell('target').shapes(ly.layer(8,0)).insert(k.Box(2000,2000,2100,2100))
        with self.assertRaises(AssertionError):self.execute(data)

    def test_duplicate_placement_rejected(self):
        data=self.fixture();ly,top=data[:2]
        top.insert(k.CellInstArray(ly.cell('target').cell_index(),k.Trans(500,200)))
        with self.assertRaises(ValueError):self.execute(data)

    def test_cross_parent_alias_rejected(self):
        data=self.fixture();ly=data[0]
        other=ly.create_cell('second_parent')
        other.insert(k.CellInstArray(ly.cell('target').cell_index(),k.Trans()))
        with self.assertRaises(AssertionError):self.execute(data)

    def test_properties_rejected(self):
        data=self.fixture();data[0].cell('target').set_property('purpose','modified')
        with self.assertRaises(AssertionError):self.execute(data)

    def test_flattened_pin_hierarchy_rejected(self):
        data=self.fixture();data[0].cell('target').flatten(True)
        with self.assertRaises(AssertionError):self.execute(data)


if __name__=='__main__':unittest.main()
