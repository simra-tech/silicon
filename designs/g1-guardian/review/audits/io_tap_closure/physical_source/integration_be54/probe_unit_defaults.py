#!/usr/bin/env python3
"""Unchanged old/new SENSE native units with the full-chip stock default switches."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import pya

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'flow/run.sh').is_file())
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def describe(path):
    db=pya.LayoutVsSchematic();db.read(str(path));nl=db.netlist();rows=[]
    for circuit in nl.each_circuit():
        counts=Counter();params={}
        for device in circuit.each_device():
            klass=device.device_class();counts[klass.name]+=1
            params.setdefault(klass.name,set()).add(tuple(p.name for p in klass.parameter_definitions()))
        rows.append(dict(name=circuit.name,devices=dict(counts),nets=sum(1 for _ in circuit.each_net()),
            pins=[p.name() for p in circuit.each_pin()],
            subcircuits=[s.circuit_ref().name for s in circuit.each_subcircuit()],
            class_parameter_schemas={k:[list(x) for x in sorted(v)] for k,v in params.items()}))
    return dict(database_sha256=sha(path),circuits=rows,
        duplicate_circuit_names={k:v for k,v in Counter(r['name'] for r in rows).items() if v>1})


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    bulk=Path(os.environ['G1_RESULTS_ROOT']);pdk=Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    cases=[('old','sense-ring-routing-20260922-r8a','8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7',
        'sense-ring-reference-20260922-r8a','e3e3c22fa0e59c61f5acc79f3733833ec2a144fe3f133ed09f7922a395deec20',
        'sense-ring-stock-20260922-r8a','708f33a1580c2767e9859f8b3a2c1b9178a07d2df3ddd082bfe1913215e80b20'),
        ('current','sense-comp45-native-build-20260923-r9','cec94187d33b60a654cb12213cfb7e0904fc2a0b5d70a3763fd9d223f44d34f7',
        'sense-comp45-native-reference-20260923-r3','8a9c92bd68f75d94fb3a08b95d7082d2a24e2dfd0827e9ba06e1ee84637cef5c',
        'sense-comp45-native-stock-20260923-r2','7973e55e36401813c08370022948a0b676ef9b064d4ce0eee2ba8b6dca412be3')]
    a.output.mkdir(parents=True);result=dict(status='running unit-default diagnostic',cases=[],
        scope='Stock native unit diagnostic with fullchip defaults; not fullchip LVS or acceptance relaxation')
    def save():(a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    rules={str(p):sha(p) for p in (pdk/'libs.tech/klayout/tech/lvs').rglob('*') if p.is_file()};save()
    for name,gfolder,ghash,sfolder,shash,dbfolder,dbhash in cases:
        gds=bulk/gfolder/'g1_sense_physical.gds';source=bulk/sfolder/'g1_sense_physical.cdl';db=bulk/dbfolder/'lvs/g1_sense_physical.lvsdb'
        assert sha(gds)==ghash and sha(source)==shash and sha(db)==dbhash
        folder=a.output/name;folder.mkdir();inventory=describe(db)
        (folder/'qualified_unit_database.json').write_text(json.dumps(inventory,indent=2)+'\n')
        cmd=['python3',str(pdk/'libs.tech/klayout/tech/lvs/run_lvs.py'),'--layout',str(gds),'--netlist',str(source),
            '--topcell','g1_sense_physical','--run_mode','deep','--top_lvl_pins','--spice_comments','--run_dir',str(folder/'reports')]
        with (folder/'console.log').open('x') as log:
            run=run_bounded(cmd,log,folder/'run.json',120,cwd=ROOT,
                env=dict(os.environ,KLAYOUT_PATH=str(pdk/'libs.tech/klayout')),interval_s=2)
        engine=folder/'reports/g1_sense_physical.log';log=engine.read_text() if engine.exists() else ''
        saved=folder/'reports/g1_sense_physical.lvsdb'
        row=dict(name=name,inputs={str(gds):ghash,str(source):shash,str(db):dbhash},command=cmd,run=run,
            actual_engine_match='Congratulations! Netlists match.' in log,
            actual_engine_mismatch="ERROR : Netlists don't match" in log,raw_log_sha256=sha(engine) if engine.exists() else None)
        if saved.exists():row['actual_database']=describe(saved)
        result['cases'].append(row);save()
        assert run['status']=='completed' and run['returncode']==0 and saved.exists(),row
    assert all(sha(Path(p))==h for p,h in rules.items())
    result.update(status='completed two native unit diagnostics; outcomes and applicability separate',stock_rules_unchanged=True,rule_hashes=rules)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes());save()


if __name__=='__main__':main()
