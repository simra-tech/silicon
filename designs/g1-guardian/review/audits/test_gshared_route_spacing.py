import unittest
from repair_gshared_route_spacing import transform,wire_only_patch,expected_serialization,NET_HEADER,SERIALIZED_HEADER,OLD,NEW

class Controls(unittest.TestCase):
    def sample(self):
        return 'UNITS DISTANCE MICRONS 1000 ;\nNETS 1 ;\n    - g_shared_bare ( a p ) ( b q ) + USE SIGNAL\n'+''.join(OLD)+';\nEND NETS\n'
    def test_exact_inverse(self):
        source=self.sample();changed,block=transform(source)
        for old,new in zip(OLD,NEW):changed=changed.replace(new,old)
        self.assertEqual(changed,source)
        self.assertEqual(block.count('360480'),3)
    def test_missing_duplicate_wrong_net_wrong_units_rejected(self):
        source=self.sample()
        for bad in [source.replace(OLD[0],''),source+OLD[0],source.replace('g_shared_bare','other_net'),source.replace('MICRONS 1000','MICRONS 2000')]:
            with self.assertRaises(AssertionError):transform(bad)
    def test_preexisting_successor_coordinate_rejected(self):
        with self.assertRaises(AssertionError):transform(self.sample()+NEW[0])
    def test_wire_patch_preserves_all_route_text_without_reconnecting(self):
        block=NET_HEADER+''.join(NEW)+';\n'
        result=wire_only_patch('a\nb\nc\nd\ne\n',block)
        self.assertIn('    - g_shared_bare + USE SIGNAL\n'+''.join(NEW)+';\n',result)
        self.assertNotIn('pad19_g_shared',result)
        self.assertNotIn('i_core.u_dose',result)
        with self.assertRaises(AssertionError):wire_only_patch('a\n',block.replace('padbare','wrongpin'))
    def test_declared_pin_serialization_only(self):
        original=self.sample().replace('    - g_shared_bare ( a p ) ( b q ) + USE SIGNAL\n',NET_HEADER)
        result=expected_serialization(original).replace(SERIALIZED_HEADER,NET_HEADER)
        for old,new in zip(OLD,NEW):result=result.replace(new,old)
        self.assertEqual(result,original)
        for bad in [original.replace('padbare','badpin'),original+SERIALIZED_HEADER]:
            with self.assertRaises(AssertionError):expected_serialization(bad)

if __name__=='__main__':unittest.main()
