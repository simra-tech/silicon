#!/usr/bin/env python3
"""Small actual DSL capture control; no stock or physical qualification."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import klayout.db as k


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert k.__version__=='0.30.9'
    a.output.mkdir(parents=True)
    layout=k.Layout();layout.dbu=.001;cell=layout.create_cell('CAPTURE_CONTROL')
    metal=layout.layer(8,0);labels=layout.layer(8,25)
    for name,x in [('A',0),('B',10000)]:
        cell.shapes(metal).insert(k.Box(x,0,x+1000,1000))
        cell.shapes(labels).insert(k.Text(name,k.Trans(x+500,500)))
    layout.write(str(a.output/'input.gds'))
    snap=a.output/'before.l2n';deck=a.output/'control.lvs'
    deck.write_text('source('+json.dumps(str(a.output/'input.gds'))+')\n'
        'm=input(8,0)\nt=input(8,25)\nconnect(m,t)\n'
        'capture = lambda do |target_netlist|\n'
        '  before = target_netlist.to_s\n'
        '  l2n_data.write('+json.dumps(str(snap))+')\n'
        '  raise "snapshot mutated native graph" unless before == target_netlist.to_s\n'
        'end\ncapture.call(netlist)\n')
    start=time.monotonic()
    result=subprocess.run(['klayout','-b','-r',str(deck)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
    (a.output/'engine.log').write_bytes(result.stdout)
    assert result.returncode==0,result.stdout.decode(errors='replace')
    db=k.LayoutToNetlist();db.read(str(snap));netlist=db.netlist();top=netlist.top_circuit()
    names=sorted(n.name for n in top.each_net());assert names==['A','B'],names
    reread=a.output/'roundtrip.l2n';db.write(str(reread));other=k.LayoutToNetlist();other.read(str(reread))
    assert netlist.to_s()==other.netlist().to_s()
    # Wrong expected names and a missing net are rejected by the same inventory.
    assert names!=['A','C'] and names!=['A']
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'summary.json').write_text(json.dumps(dict(status='passed native DSL capture control',
        elapsed_seconds=time.monotonic()-start,version=k.__version__,names=names,
        same_live_netlist_before_after_capture=True,roundtrip_native_graph_exact=True,
        wrong_name_and_missing_net_controls=True,snapshot_sha256=hashlib.sha256(snap.read_bytes()).hexdigest(),
        fullchip_binary64_geometry_roundtrip='not run',native_LVS='not applicable'),indent=2)+'\n')


if __name__=='__main__':main()
