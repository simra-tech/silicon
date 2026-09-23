#!/usr/bin/env python3
"""Isolate pinned comparator behavior with sparse versus fresh pin metadata."""
import argparse
import hashlib
import json
from pathlib import Path
import pya


def value(obj, name):
    result = getattr(obj, name)
    return result() if callable(result) else result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case', choices=('fresh','sparse','compact','compact_wrongwire'), required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    (a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    def make(sparse=False, wrong=False):
        nl = pya.Netlist()
        k = pya.DeviceClassResistor()
        k.name = 'R'
        nl.add(k)
        c = pya.Circuit()
        c.name = 'TOP'
        nl.add(c)
        nets = {name:c.create_net(name) for name in ('A','X','B')}
        for name,lo,hi,r in [('R1','A','X',1000.125),('R2','A' if wrong else 'X','B',2000.25)]:
            d = c.create_device(k,name)
            d.set_parameter('R',r)
            d.connect_terminal('A',nets[lo])
            d.connect_terminal('B',nets[hi])
        if sparse:
            for i in range(71):
                p = c.create_pin('INTERNAL'+str(i))
                c.connect_pin(p.id(),nets['X'])
            for p in reversed(list(c.each_pin())):
                c.remove_pin(p.id())
        for name in ('A','B'):
            p = c.create_pin(name)
            c.connect_pin(p.id(),nets[name])
        return nl,c
    left,lc = make(a.case!='fresh')
    right,rc = make(False,a.case=='compact_wrongwire')
    def graph(c):
        return dict(nets=[(n.cluster_id,n.name) for n in c.each_net()], devices=[
            (value(d,'id'),d.name,d.device_class().name,
             [(p.name,float(d.parameter(p.name)).hex()) for p in d.device_class().parameter_definitions()],
             [(t.name,d.net_for_terminal(t.name).name) for t in d.device_class().terminal_definitions()])
            for d in c.each_device()])
    before = graph(lc)
    old_ids = [p.id() for p in lc.each_pin()]
    if a.case.startswith('compact'):
        # This controlled graph is reconstructed from its exact fixture; the
        # prospective fullchip remedy must clone every actual saved record.
        left,lc = make()
        assert graph(lc) == before
    result = dict(case=a.case,status='running comparison', pins_before=old_ids,
                  pins_compared=[p.id() for p in lc.each_pin()], graph_exact=graph(lc)==before,
                  KLayout=pya.__version__, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    report = a.output/'summary.json'
    report.write_text(json.dumps(result,indent=2)+'\n')
    xr = pya.NetlistCrossReference()
    compare = pya.NetlistComparer()
    compare.max_resistance = 1e9
    compare.min_capacitance = 1e-18
    equivalent = compare.compare(left,right,xr)
    pins = []
    for pair in xr.each_circuit_pair():
        for p in xr.each_pin_pair(pair):
            pins.append((None if p.first is None else p.first.name(),None if p.second is None else p.second.name(),str(p.status)))
    strict = equivalent and bool(pins) and all(l is not None and l==r and status=='Match' for l,r,status in pins)
    expected = a.case!='compact_wrongwire'
    result.update(status='passed expected disposition' if strict==expected else 'failed expected disposition',
                  engine_equivalent=equivalent,strict=strict,pin_pairs=pins)
    report.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])
    raise SystemExit(0 if strict==expected else 1)


if __name__ == '__main__':
    main()
