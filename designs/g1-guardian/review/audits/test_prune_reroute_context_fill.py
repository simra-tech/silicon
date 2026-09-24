import unittest
import pya
from prune_reroute_context_fill import payload,LAYERS
class Controls(unittest.TestCase):
 def fixture(self,layer=134,datatype=22):
  ly=pya.Layout();c=ly.create_cell('TM2_FILL_CELL');s=c.shapes(ly.layer(layer,datatype)).insert(pya.Box(0,0,1000,1000));return ly,c,s
 def test_all_layers(self):
  for n in LAYERS:
   ly,c,s=self.fixture(n);self.assertEqual(payload(ly,c)[0],n)
 def test_drawing_rejected(self):
  ly,c,s=self.fixture(datatype=0)
  with self.assertRaises(AssertionError):payload(ly,c)
 def test_unknown_layer_rejected(self):
  ly,c,s=self.fixture(layer=235)
  with self.assertRaises(AssertionError):payload(ly,c)
 def test_mixed_rejected(self):
  ly,c,s=self.fixture();c.shapes(ly.layer(134,0)).insert(pya.Box(0,0,1,1))
  with self.assertRaises(AssertionError):payload(ly,c)
 def test_properties_rejected(self):
  ly,c,s=self.fixture();s.set_property('test','held')
  with self.assertRaises(AssertionError):payload(ly,c)
 def test_child_rejected(self):
  ly,c,s=self.fixture();other=ly.create_cell('OTHER');c.insert(pya.CellInstArray(other.cell_index(),pya.Trans()))
  with self.assertRaises(AssertionError):payload(ly,c)
if __name__=='__main__':unittest.main()
