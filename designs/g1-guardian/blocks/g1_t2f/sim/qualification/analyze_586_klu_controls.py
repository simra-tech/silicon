#!/usr/bin/env python3
"""Matched corner KLU controls; preserve exact failures and descriptive differences."""
import argparse,gzip,json
from pathlib import Path
import numpy as np
from prepare_586_klu_controls import HERE,REFERENCES,sha


def wave(run):
    with gzip.open(run/'phase0.dat.gz','rb') as stream:blob=stream.read()
    data=np.array([list(map(float,l.split())) for l in blob.splitlines()[1:] if l.strip()])
    assert data.shape[1]==13 and np.isfinite(data).all() and abs(data[-1,0]-32e-6)<1e-12
    return blob,data


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    records={}
    for corner,name in REFERENCES.items():
        paths=[HERE/'runs'/n for n in [name,'t2f586-klu-'+corner+'-replay-20260923-a','t2f586-klu-'+corner+'-repeat-20260923-a']]
        if any(not (r/'summary.json').exists() for r in paths):records[corner]=dict(status='not run; missing control');continue
        rows=[json.loads((r/'summary.json').read_text())[0] for r in paths]
        if any(not r['control_status'].startswith('passed') for r in rows):records[corner]=dict(status='failed control; full comparison not run');continue
        original=rows[0]['phases'][0];expected=original['parameters_before']
        assert expected==original['parameters_after']==rows[1]['parameters_before']==rows[1]['parameters_after']==rows[2]['parameters_before']==rows[2]['parameters_after']
        blobs,data=zip(*(wave(r) for r in paths));assert all(b.splitlines()[0]==blobs[0].splitlines()[0] for b in blobs)
        grid=np.unique(np.concatenate([data[0][:,0],data[1][:,0]]));names=blobs[0].splitlines()[0].decode().split()
        errors={n:float(np.max(np.abs(np.interp(grid,data[1][:,0],data[1][:,i])-np.interp(grid,data[0][:,0],data[0][:,i])))) for i,n in enumerate(names[1:],1)}
        repeat=blobs[1]==blobs[2]
        records[corner]=dict(status='passed fullparameters and KLU exactrepeat' if repeat else 'failed KLU exactrepeat',
            full3180_status='passed',klu_repeat_decoded_bytes_exact=repeat,
            sparse_klu_exactwave_status='passed' if blobs[0]==blobs[1] else 'failed exactbyte comparison',
            sparse_klu_exactgrid_status='passed' if np.array_equal(data[0][:,0],data[1][:,0]) else 'failed exactgrid comparison',
            uniongrid_maximum_abs_difference=errors,units={n:'A' if n.startswith('i(') else 'V' for n in names[1:]},
            frequencies_Hz=[original['measurements']['freq'],rows[1]['measurements']['freq'],rows[2]['measurements']['freq']],
            wall_s=[r['runtime']['wall_s'] for r in rows],receipts_sha256={p.name:{n:sha(p/n) for n in ['summary.json','provenance.json','probe.cir','phase0.dat.gz']} for p in paths})
    status='completed matched controls; no adoption' if len(records)==3 and all(r['status'].startswith('passed') for r in records.values()) else 'failed or not run; no adoption'
    a.output.write_text(json.dumps(dict(status=status,corners=records,scope='Original exact comparison failures retained. Descriptive differences impose no tolerance or adoption waiver; original failed seeds remain in denominator.',analyzer_sha256=sha(Path(__file__))),indent=2)+'\n');print(status)


if __name__=='__main__':main()
