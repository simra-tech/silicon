#!/usr/bin/env python3
"""In-memory native MOS combiner orientation control; no deck or design edits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pya


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def control(reverse):
    nl = pya.Netlist()
    dc = pya.DeviceClassMOS4Transistor()
    dc.name = 'diagnostic_mos4'
    nl.add(dc)
    circuit = pya.Circuit()
    circuit.name = 'diagnostic'
    nl.add(circuit)
    nets = {n:circuit.create_net(n) for n in ('s','g','d','b')}
    for i in range(2):
        dev = circuit.create_device(dc, 'M'+str(i))
        swap = bool(i and reverse)
        for term, net in [('S','d' if swap else 's'),('G','g'),
                          ('D','s' if swap else 'd'),('B','b')]:
            dev.connect_terminal(term,nets[net])
        params = dict(L=2.,W=6.,AS=1.14 if swap else 2.04,
                      AD=2.04 if swap else 1.14,PS=6.38 if swap else 12.68,
                      PD=12.68 if swap else 6.38)
        for k,v in params.items():
            dev.set_parameter(k,v)
    def collect():
        rows=[]
        for d in circuit.each_device():
            rows.append(dict(name=d.name,terminals={q:d.net_for_terminal(q).name for q in ('S','G','D','B')},
                             parameters={q:d.parameter(q) for q in ('L','W','AS','AD','PS','PD')}))
        return rows
    before=collect()
    expected={n:dict(area_um2=0.,perimeter_um=0.) for n in ('s','d')}
    for row in before:
        for term in ('S','D'):
            target=expected[row['terminals'][term]]
            target['area_um2']+=row['parameters']['A'+term]
            target['perimeter_um']+=row['parameters']['P'+term]
    nl.combine_devices()
    after=collect()
    assert len(after)==1 and abs(after[0]['parameters']['W']-12)<1e-12
    actual={}
    for term in ('S','D'):
        actual[after[0]['terminals'][term]]=dict(area_um2=after[0]['parameters']['A'+term],
                                               perimeter_um=after[0]['parameters']['P'+term])
    deltas={n:{k:actual[n][k]-expected[n][k] for k in expected[n]} for n in expected}
    conserved=all(abs(v)<1e-12 for d in deltas.values() for v in d.values())
    return dict(reversed_SD_second_device=reverse,before=before,after=after,expected_per_physical_net=expected,
                actual_per_physical_net=actual,delta=deltas,per_net_AP_conserved=conserved)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert os.sched_getaffinity(0)=={7} and pya.__version__=='0.30.9' and not a.output.exists()
    rows=[control(False),control(True)]
    assert rows[0]['per_net_AP_conserved'] and not rows[1]['per_net_AP_conserved']
    for key in ('area_um2','perimeter_um'):
        assert abs(sum(q[key] for q in rows[1]['actual_per_physical_net'].values())-
                   sum(q[key] for q in rows[1]['expected_per_physical_net'].values()))<1e-12
    result=dict(status='passed diagnostic isolation of reversed-terminal combiner AP attribution failure',
                KLayout=pya.__version__,script_sha256=sha(Path(__file__)),controls=rows,
                source_reference='https://github.com/KLayout/klayout/blob/v0.30.9/src/db/db/dbNetlistDeviceClasses.cc#L279-L365',
                source_binary_rebuild_binding='not run; native installed behavior independently tested',
                changed_decks=False,changed_models=False,changed_design=False,saved_GDS=False,
                simulation='not run',intrinsic_shared_PSP_applicability='not run',
                scope='Diagnostic netlist only. No correction of canonical extraction or golden source.')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
