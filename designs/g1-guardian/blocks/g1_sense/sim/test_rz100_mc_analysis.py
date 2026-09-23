#!/usr/bin/env python3
"""Mutation tests against a retained paired-method packet, without simulation."""
import argparse,shutil,tempfile,unittest
from pathlib import Path
from analyze_rz100_mc_smoke import bound_inputs
from analyze_rz100_error_budget import controls

class Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='g1-r100-audit-')
        self.addCleanup(tmp.cleanup)
        self.packet=Path(tmp.name)/'packet';self.packet.mkdir()
        self.method=Path(tmp.name)/'method';self.method.mkdir()
        for name in ['candidate.cir','candidate.spice','contract.json']:
            shutil.copyfile(PACKET/name,self.packet/name)
        for name in ['summary.json','provenance.json']:
            shutil.copyfile(METHOD/name,self.method/name)
    def test_exact(self):bound_inputs(self.packet,self.method)
    def test_template_mutation(self):
        p=self.packet/'candidate.cir';p.write_text(p.read_text().replace('setseed 41039','setseed 41040'))
        with self.assertRaises(AssertionError):bound_inputs(self.packet,self.method)
    def test_runtime_mutation(self):
        p=self.method/'provenance.json';p.write_text(p.read_text()+'\n')
        with self.assertRaises(AssertionError):bound_inputs(self.packet,self.method)
    def test_source_mutation(self):
        p=self.packet/'candidate.spice';p.write_text(p.read_text()+'\n')
        with self.assertRaises(AssertionError):bound_inputs(self.packet,self.method)
    def test_algebra(self):self.assertEqual(len(controls()),3)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--packet',type=Path,required=True)
    ap.add_argument('--method',type=Path,required=True)
    a=ap.parse_args();PACKET=a.packet;METHOD=a.method
    unittest.main(argv=['test_rz100_mc_analysis'])
