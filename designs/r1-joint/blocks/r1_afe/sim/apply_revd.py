#!/usr/bin/env python3
"""Write the revision-D netlist of record: apply the screened development edits (run_afe.devvar) to the D16 netlist,
so that schematic/r1_afe.spice is exactly the variant that was screened. Usage: python3 apply_revd.py <variant>
(revision D: l2+cx25_13+np2+o2i1.5+ro11.55_44.7_<WCOS>). Run once; it refuses a netlist that already has the edits."""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('ra', os.path.join(HERE, 'run_afe.py'))
ra = importlib.util.module_from_spec(spec); spec.loader.exec_module(ra)
src = open(ra.NETLIST).read()
if 'XCX1' in src:
    raise SystemExit('netlist already carries revision-D edits')
for e in ra.devvar(sys.argv[1]):
    src = ra.apply_edit(src, e, sys.argv[1])
open(ra.NETLIST, 'w').write(src)
print('applied', sys.argv[1])
