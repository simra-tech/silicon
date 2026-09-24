#!/usr/bin/env python3
import unittest
from pathlib import Path
from export_digital_egress_lef import ports
from export_closed_macro_lef import subtract_rectangle


class Controls(unittest.TestCase):
    def test_all_original_ports(self):
        f=Path(__file__).resolve().parents[2]/'blocks/g1_ctrl/layout/g1_digital.lef'
        p=ports(f.read_text());self.assertEqual(len(p),46)
        self.assertEqual(len(p['VDD']),10);self.assertEqual(len(p['VSS']),10)
        self.assertIn('osc_trim[3]',p);self.assertEqual(p['cmp_hard'],[(30,[359600,202660,360000,203060])])

    def test_duplicate_pin_rejected(self):
        x='  PIN foo\n    PORT\n      LAYER Metal3 ;\n        RECT 0 0 1 1 ;\n    END\n  END foo\n'
        with self.assertRaises(AssertionError):ports(x+x)

    def test_boundary_port_subtraction_exact_area(self):
        parts=subtract_rectangle([0,0,360000,360000],[359600,202660,360000,203060])
        self.assertEqual(sum((r-l)*(t-b) for l,b,r,t in parts),360000**2-400**2)

    def test_unknown_layer_rejected(self):
        with self.assertRaises(ValueError):ports('  PIN p\n    PORT\n      LAYER Unknown ;\n        RECT 0 0 1 1 ;\n    END\n  END p\n')


if __name__=='__main__':unittest.main()
