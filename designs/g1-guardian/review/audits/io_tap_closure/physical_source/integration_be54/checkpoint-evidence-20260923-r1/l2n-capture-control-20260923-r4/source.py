#!/usr/bin/env python3
"""Prove output-only L2N plus exact binary64 sidecar on a synthetic graph."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import time
import klayout.db as k


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and k.__version__=='0.30.9'
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    layout=k.Layout();layout.dbu=.001;cell=layout.create_cell('CAPTURE_CONTROL')
    metal=layout.layer(8,0);labels=layout.layer(8,25)
    for name,x in [('A',0),('B',10000)]:
        cell.shapes(metal).insert(k.Box(x,0,x+1000,1000));cell.shapes(labels).insert(k.Text(name,k.Trans(x+500,500)))
    layout.write(str(a.output/'input.gds'))
    snap=a.output/'before.l2n';exact=a.output/'exact.json';deck=a.output/'control.lvs'
    deck.write_text('require "json"\nsource('+json.dumps(str(a.output/'input.gds'))+')\n'
        'm=input(8,0)\nt=input(8,25)\nconnect(m,t)\n'
        'nl=netlist\nklass=RBA::DeviceClassResistor.new\nklass.name="CONTROL_R"\nnl.add(klass)\n'
        'c=nl.circuit_by_name("CAPTURE_CONTROL")\ndev=c.create_device(klass,"R1")\n'
        'dev.connect_terminal("A",c.net_by_name("A"))\ndev.connect_terminal("B",c.net_by_name("B"))\n'
        'dev.set_parameter("R",123.456789012345)\n'
        'before=nl.to_s\nrows=[]\n'
        'nl.each_circuit { |c| c.each_device { |d| d.device_class.parameter_definitions.each { |p| rows << [c.name,d.id,d.name,d.device_class.name,p.name,[d.parameter(p.id)].pack("G").unpack1("H*")] } } }\n'
        'File.write('+json.dumps(str(exact))+',JSON.generate(rows))\n'
        'l2n_data.write_l2n('+json.dumps(str(snap))+')\n'
        'raise "capture mutated native graph" unless before==nl.to_s\n')
    start=time.monotonic();result=subprocess.run(['klayout','-b','-r',str(deck)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
    (a.output/'engine.log').write_bytes(result.stdout);assert result.returncode==0,result.stdout.decode(errors='replace')
    db=k.LayoutToNetlist();db.read(str(snap));nl=db.netlist();top=nl.top_circuit()
    assert sorted(n.name for n in top.each_net())==['A','B']
    devices=list(top.each_device());assert len(devices)==1
    original=123.456789012345;serialized=devices[0].parameter('R');assert serialized!=original
    rows=json.loads(exact.read_text());assert len(rows)==5
    def restore(records):
        for cn,di,dn,cl,pn,value in records:
            c=nl.circuit_by_name(cn);assert c is not None
            found=[d for d in c.each_device() if d.id()==di];assert len(found)==1
            d=found[0];assert d.name==dn and d.device_class().name==cl
            assert pn in [p.name for p in d.device_class().parameter_definitions()]
            d.set_parameter(pn,struct.unpack('>d',bytes.fromhex(value))[0])
    # Reject wrong identity before restoring any value from that row.
    bad=[list(r) for r in rows];bad[0][2]='WRONG'
    rejected=False
    try:restore(bad)
    except AssertionError:rejected=True
    assert rejected
    restore(rows);assert devices[0].parameter('R')==original
    actual=[]
    for c in nl.each_circuit():
        for d in c.each_device():
            for p in d.device_class().parameter_definitions():
                actual.append([c.name,d.id(),d.name,d.device_class().name,p.name,struct.pack('>d',d.parameter(p.id())).hex()])
    assert actual==rows
    assert devices[0].net_for_terminal('A').name=='A' and devices[0].net_for_terminal('B').name=='B'
    (a.output/'summary.json').write_text(json.dumps(dict(status='passed exact-sidecar capture control',
        elapsed_seconds=time.monotonic()-start,version=k.__version__,live_graph_unchanged=True,
        native_text_binary64_roundtrip='failed retained',native_serialized_R=serialized,original_R=original,
        exact_sidecar_all_parameters=True,identity_negative_rejected=True,terminal_identity_exact=True,
        snapshot_sha256=hashlib.sha256(snap.read_bytes()).hexdigest(),sidecar_sha256=hashlib.sha256(exact.read_bytes()).hexdigest(),
        fullchip_graph_and_geometry_roundtrip='not run',native_LVS='not applicable'),indent=2)+'\n')


if __name__=='__main__':main()
