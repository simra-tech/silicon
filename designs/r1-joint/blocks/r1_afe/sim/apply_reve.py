#!/usr/bin/env python3
"""Write the revision-E netlist of record: apply the screened development edits (run_afe.devvar) to the revision-D
netlist after WCCB 20.4u -> 24u was set by hand (instance XA1). Usage: python3 apply_reve.py rz1_21+cxs15+rz2_10
Run once; it refuses a netlist whose XA1 already has LRZ=21u."""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('ra', os.path.join(HERE, 'run_afe.py'))
ra = importlib.util.module_from_spec(spec); spec.loader.exec_module(ra)
src = open(ra.NETLIST).read()
if 'LRZ=21u' in src:
    raise SystemExit('netlist already carries revision-E edits')
for e in ra.devvar(sys.argv[1]):
    src = ra.apply_edit(src, e, sys.argv[1])
open(ra.NETLIST, 'w').write(src)
print('applied', sys.argv[1])
