"""Positive and rejection controls for the deliberately restricted DEF parser."""
import unittest
from route_inventory import parse, route, parallel_candidates


class Tests(unittest.TestCase):
    def test_extensions_and_inheritance(self):
        row = route('Metal4 ( 10 20 0 ) ( * 40 ) ( 30 * 15 )')
        self.assertEqual(row['points_dbu'], [[10, 20], [10, 40], [30, 40]])
        self.assertEqual(row['endpoint_extensions_dbu'], [0, None, 15])
        self.assertEqual([s['length_dbu'] for s in row['segments']], [20, 20])

    def test_patch_not_segment(self):
        row = route('Metal5 ( 50 60 ) RECT ( -575 -100 0 100 )')
        self.assertEqual(row['segments'], [])
        self.assertEqual(row['patch']['offsets_dbu'], [-575, -100, 0, 100])

    def test_via(self):
        self.assertEqual(route('Metal5 ( 50 60 ) TopVia1EWNS')['via']['name'], 'TopVia1EWNS')

    def test_reject_unsupported(self):
        for text in ['Metal4 ( * 20 ) ( 30 40 )', 'Metal4 ( 10 20 ) ( 30 40 )',
                     'Metal4 ( 10 20 ) UNKNOWN', 'Metal4 ( 10 20 )',
                     'Metal4 ( 10 20 ) ( * * )', 'Metal4 ( 10 20 ) MASK 1',
                     'Metal5 ( 50 60 ) RECT ( 0 0 -5 5 )']:
            with self.subTest(text=text), self.assertRaises((AssertionError, ValueError)):
                route(text)

    def test_parse_and_counts(self):
        text = 'UNITS DISTANCE MICRONS 1000 ;\nNETS 2 ;\n - i_core.sense_p ( A p ) + USE SIGNAL + ROUTED Metal4 ( 0 0 ) ( * 10000 ) ;\n - clk\\[0\\] ( B c ) + USE SIGNAL + ROUTED Metal4 ( 480 0 ) ( * 8000 ) ;\nEND NETS\n'
        units, nets = parse(text)
        self.assertEqual(nets[1]['net'], 'clk[0]')
        candidates = parallel_candidates(nets, units)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]['overlap_um'], 8)
        self.assertEqual(candidates[0]['centerline_separation_um'], .48)
        self.assertEqual(parse(text.replace('USE SIGNAL', 'USE CLOCK'))[1][0]['use'], 'CLOCK')
        with self.assertRaises(AssertionError):
            parse(text.replace('USE SIGNAL', 'USE POWER'))
        with self.assertRaises(AssertionError):
            parse(text.replace('NETS 2', 'NETS 3'))
        with self.assertRaises(AssertionError):
            parse(text.replace('clk\\[0\\]', 'i_core.sense_p'))


if __name__ == '__main__':
    unittest.main()
