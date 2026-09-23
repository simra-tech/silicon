#!/usr/bin/env python3
"""Source-only controls; this never authorizes a positive-C simulation."""
import argparse,copy,json
from pathlib import Path
from prepare_rz100_actual_partial_c import prepare,tests
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['source','view','rows']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();raw=a.source.read_bytes();view=json.loads(a.view.read_text());rows=json.loads(a.rows.read_text())
    tests();text,report=prepare(raw,view,rows)
    assert prepare(raw,view,report['raw_rows'])[0]==text
    bads=[]
    bad=copy.deepcopy(rows);bad[0]['capacitance_fF']=-1.;bads.append(bad)
    bad=copy.deepcopy(rows);bad[0]['net1']='UNKNOWN';bads.append(bad)
    bad=copy.deepcopy(rows);bad[0]['capacitance_fF_hex']='0x0.0p+0';bads.append(bad)
    bad=copy.deepcopy(rows);bad.append(copy.deepcopy(bad[0]));bads.append(bad)
    bads.append(copy.deepcopy(rows[:-1]))
    for bad in bads:
        try:prepare(raw,view,bad)
        except AssertionError:continue
        raise AssertionError('invalid field/source ledger accepted')
    print(json.dumps(dict(status='passed source-only actual-field preparation controls',positive_roundtrip=True,
        rejected=['negative','unknown node','hex/value mismatch','duplicate pair','missing pair'],
        prospective_source_sha256=report['diagnostic_source_sha256'],electrical='not run by this control'),indent=2))
if __name__=='__main__':main()
