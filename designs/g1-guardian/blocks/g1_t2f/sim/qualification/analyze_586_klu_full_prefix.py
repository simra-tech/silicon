#!/usr/bin/env python3
"""Retrospective same-KLU prefix observation, not a changed acceptance gate."""
import argparse,gzip,json
from pathlib import Path
from prepare_586_fast76002_solver import HERE,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    paths=[HERE/'runs'/n for n in ['t2f586-fast76002-klu2us-20260923-a','t2f586-fast76002-klu32us-20260923-a']]
    rows=[json.loads((p/'summary.json').read_text())[0] for p in paths]
    assert all(r['control_status'].startswith('passed') for r in rows)
    assert rows[0]['parameters_before']==rows[0]['parameters_after']==rows[1]['parameters_before']==rows[1]['parameters_after']
    blobs=[]
    for path,row in zip(paths,rows):
        with gzip.open(path/'phase0.dat.gz','rb') as stream:blob=stream.read()
        import hashlib
        assert hashlib.sha256(blob).hexdigest()==row['waveform_sha256']
        lines=blob.splitlines();blobs.append([lines[0]]+[line for line in lines[1:] if float(line.split()[0])<=1.9e-6])
    result=dict(status='completed retrospective same-KLU prefix observation',through_s=1.9e-6,
        excluded_endpoint_s=2e-6,rows=[len(b)-1 for b in blobs],decoded_rows_exact=blobs[0]==blobs[1],
        full3180_exact=True,receipts={r.name:{n:sha(r/n) for n in ['summary.json','probe.cir','phase0.dat.gz']} for r in paths},
        scope='Selected after completion to inspect common interior0..1.9us, deliberately excludes2us endpoint. Not an original prospective acceptance gate or independent repeat; endpoints differ. Original SPARSE wave/grid failures remain failed; no solver adoption.',analyzer_sha256=sha(Path(__file__)))
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['decoded_rows_exact'])


if __name__=='__main__':main()
