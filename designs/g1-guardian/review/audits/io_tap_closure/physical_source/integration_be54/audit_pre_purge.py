#!/usr/bin/env python3
"""Read the diagnostic checkpoint; restore only independently captured floats."""
import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time
import klayout.db as k


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def val(obj,name):
    item=getattr(obj,name)
    return item() if callable(item) else item


def topology(nl):
    rows=[]
    nid=lambda n:None if n is None else n.cluster_id
    for c in nl.each_circuit():
        rows.append(dict(name=c.name,nets=[(n.cluster_id,n.name) for n in c.each_net()],
            pins=[(p.id(),p.name(),nid(c.net_for_pin(p.id()))) for p in c.each_pin()],
            devices=[(d.id(),d.name,d.device_class().name,
                [(t.name,nid(d.net_for_terminal(t.name))) for t in d.device_class().terminal_definitions()]) for d in c.each_device()],
            subcircuits=[(s.id(),s.name,s.circuit_ref().name,
                [(p.id(),nid(s.net_for_pin(p.id()))) for p in s.circuit_ref().each_pin()]) for s in c.each_subcircuit()]))
    return rows


def main():
    ap=argparse.ArgumentParser()
    for name in ('snapshot','sidecar','output'):ap.add_argument('--'+name,type=Path,required=True)
    for name in ('snapshot-sha','sidecar-sha'):ap.add_argument('--'+name,required=True)
    ap.add_argument('--purge-circuit')
    ap.add_argument('--purge-all',action='store_true')
    a=ap.parse_args();assert len(os.sched_getaffinity(0))==1 and not a.output.exists()
    assert not (a.purge_circuit and a.purge_all)
    assert k.__version__=='0.30.9' and sha(a.snapshot)==a.snapshot_sha and sha(a.sidecar)==a.sidecar_sha
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    start=time.monotonic();db=k.LayoutToNetlist();db.read(str(a.snapshot));nl=db.netlist()
    graph_before=topology(nl)
    rows=json.loads(a.sidecar.read_text());expected={tuple(r[:5]):r[5] for r in rows};assert len(expected)==len(rows)
    actual={};devices={};before_topology=[]
    for c in nl.each_circuit():
        for d in c.each_device():
            identity=(c.name,d.id(),d.name,d.device_class().name);devices[identity]=d
            terminals=[(t.name,None if d.net_for_terminal(t.name) is None else d.net_for_terminal(t.name).cluster_id)
                for t in d.device_class().terminal_definitions()]
            before_topology.append((identity,terminals))
            for p in d.device_class().parameter_definitions():actual[identity+(p.name,)]=d.parameter(p.name)
    assert set(actual)==set(expected)
    rounded=[]
    for key,hexvalue in expected.items():
        exact=struct.unpack('>d',bytes.fromhex(hexvalue))[0];assert math.isfinite(exact)
        if struct.pack('>d',actual[key]).hex()!=hexvalue:rounded.append(dict(identity=key,native_text=actual[key],captured_binary64=hexvalue))
        devices[key[:4]].set_parameter(key[4],exact)
    assert all(struct.pack('>d',devices[key[:4]].parameter(key[4])).hex()==value for key,value in expected.items())
    after_topology=[]
    for c in nl.each_circuit():
        for d in c.each_device():
            identity=(c.name,d.id(),d.name,d.device_class().name)
            after_topology.append((identity,[(t.name,None if d.net_for_terminal(t.name) is None else d.net_for_terminal(t.name).cluster_id)
                for t in d.device_class().terminal_definitions()]))
    assert after_topology==before_topology
    assert topology(nl)==graph_before
    circuits=[];hotnets=[]
    for c in nl.each_circuit():
        nets=list(c.each_net());ds=list(c.each_device());subs=list(c.each_subcircuit());pins=list(c.each_pin())
        passive=[n for n in nets if val(n,'terminal_count')+val(n,'subcircuit_pin_count')==0]
        for n in nets:
            count=val(n,'subcircuit_pin_count')
            if count>=100:hotnets.append(dict(circuit=c.name,net=n.name,cluster=n.cluster_id,subcircuit_pins=count))
        circuits.append(dict(name=c.name,nets=len(nets),devices=len(ds),subcircuits=len(subs),pins=len(pins),
            references=len(list(c.each_ref())),passive_nets=len(passive),
            passive_pins=sum(val(n,'pin_count') for n in passive),
            all_nets_passive=len(nets)==len(passive),models=dict(collections.Counter(d.device_class().name for d in ds))))
    result=dict(status='passed pre-purge snapshot inventory and exact parameter recovery; diagnostic only',
        inputs={str(a.snapshot):sha(a.snapshot),str(a.sidecar):sha(a.sidecar)},
        elapsed_seconds=time.monotonic()-start,circuits=circuits,high_fanout_nets=hotnets,
        exact_parameter_count=len(expected),native_text_rounded_parameters=rounded,
        all_device_terminal_incidence_held=True,all_net_pin_subcircuit_ids_and_incidence_held=True,
        restored_graph_sha256=hashlib.sha256(json.dumps(graph_before,sort_keys=True).encode()).hexdigest(),
        geometry_roundtrip='not run',native_LVS='not run')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if a.purge_circuit:
        c=nl.circuit_by_name(a.purge_circuit);assert c is not None
        (a.output/'purge_started.json').write_text(json.dumps(dict(circuit=c.name,epoch=time.time()))+'\n')
        begin=time.monotonic();c.purge_nets()
        (a.output/'purge_completed.json').write_text(json.dumps(dict(circuit=a.purge_circuit,seconds=time.monotonic()-begin,
            scope='isolated copied native Circuit.purge_nets; not acceptance'),indent=2)+'\n')
    if a.purge_all:
        (a.output/'purge_started.json').write_text(json.dumps(dict(scope='copied native Netlist.purge',epoch=time.time()))+'\n')
        begin=time.monotonic();nl.purge()
        (a.output/'purge_completed.json').write_text(json.dumps(dict(seconds=time.monotonic()-begin,
            circuits_remaining=[c.name for c in nl.each_circuit()],
            scope='isolated copied native Netlist.purge; not acceptance'),indent=2)+'\n')
    assert sha(a.snapshot)==a.snapshot_sha and sha(a.sidecar)==a.sidecar_sha


if __name__=='__main__':main()
