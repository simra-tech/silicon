#!/usr/bin/env python3
"""Bind qualified static outputs before any warm-continuation execution."""
import argparse
import json
from pathlib import Path
from prepare_dac586_chunk_controls import SIM,ROOT,sha


def freeze(prefix,static_audit,output):
    audit=json.loads(static_audit.read_text())
    assert audit['status']=='passed static anchor qualification' and audit['completed_controls']==11
    assert all(row['status']=='passed' for row in audit['controls']) and audit['repeat_full12']['status']=='passed'
    implementation=SIM/'qualification/dac586-static-execution-20260923-a.json'
    assert sha(implementation)==audit['implementation_sha256']
    static=json.loads(implementation.read_text())
    assert all(sha(ROOT/name)==value for name,value in static['source_sha256'].items())
    bindings=dict(static['source_sha256'])
    paths=[Path(__file__).resolve(),SIM/'prepare_dac586_chunk_controls.py',SIM/'run_dac586_chunk_control.py',
           SIM/'test_dac586_chunk_controls.py',SIM/'test_dac586_chunk_runtime.py',
           SIM/'audit_dac586_chunk_controls.py',implementation,static_audit]
    packets={}
    for label in ['room','hot']:
        out=SIM/'qualification'/(prefix+'-'+label);prep=json.loads((out/'preparation.json').read_text())
        packets[str((out/'preparation.json').relative_to(ROOT))]=sha(out/'preparation.json')
        for name in [prep['initial_reference'],prep['anchor128_reference']]:
            ref=SIM/'qualification'/name
            row=next(row for row in audit['controls'] if row['run']==name)
            assert all(sha(ref/file)==value for file,value in row['receipts_sha256'].items())
            paths.extend(ref/file for file in ['preparation.json','summary.json','run.json','run.log','provenance.json','op0.dat','dac_static.cir'])
    bindings.update({str(path.relative_to(ROOT)):sha(path) for path in paths})
    result=dict(status='staticqualified; warmcontinuation NOTRUN',prefix=prefix,preparations_sha256=packets,
        static_audit=str(static_audit.relative_to(ROOT)),static_audit_sha256=sha(static_audit),
        source_and_reference_sha256=bindings,maximum_concurrent=1,watchdog_s=600,
        gate='All11512/27 plus exact12column127/128/returned127; no tolerance substitution or20/100release.')
    assert not output.exists();output.write_text(json.dumps(result,indent=2)+'\n')
    return sha(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prefix',required=True)
    p.add_argument('--static-audit',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    print(freeze(a.prefix,ROOT/a.static_audit,ROOT/a.output))
