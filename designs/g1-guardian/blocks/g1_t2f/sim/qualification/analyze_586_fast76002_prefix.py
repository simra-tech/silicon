#!/usr/bin/env python3
"""Saved early trajectories only; not frequency/accuracy or full-run recovery."""
import argparse
import bisect
import gzip
import hashlib
import json
import math
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();assert not a.output.exists()
    run=HERE/'runs/t2f586-fast76002-prefix2us-20260923-a'
    result,=json.loads((run/'summary.json').read_text())
    assert result['control_status']=='passed waveform-only diagnostic' and result['full3180_status']=='passed'
    assert result['parameters_before']==result['parameters_after']
    with gzip.open(str(run/'phase0.dat.gz'),'rb') as stream:payload=stream.read()
    assert hashlib.sha256(payload).hexdigest()==result['waveform_sha256']
    lines=payload.decode().splitlines();names=lines[0].split()
    data=[list(map(float,line.split())) for line in lines[1:] if line.strip()]
    assert len(data)==855 and len(names)==13 and all(len(r)==13 and all(math.isfinite(x) for x in r) for r in data)
    times=[r[0] for r in data]
    assert times[0]==0 and times[-1]==2e-6 and all(x<=y for x,y in zip(times,times[1:]))
    snapshots=[]
    for target in [0,1e-6,1.01e-6,1.25e-6,1.5e-6,1.75e-6,2e-6]:
        i=bisect.bisect_left(times,target)
        if times[i]==target:row=data[i];scope='saved exact-time row'
        else:
            lo,hi=data[i-1],data[i];f=(target-lo[0])/(hi[0]-lo[0]);row=[x+f*(y-x) for x,y in zip(lo,hi)];scope='linear interpolation between saved bracketing rows'
        snapshots.append(dict(time_s=target,values=dict(zip(names[1:],row[1:])),scope=scope))
    windows=[]
    for start,stop,label in [(0,1e-6,'enable low'),(1e-6,1.01e-6,'enable rising'),(1.01e-6,2e-6,'after enable ramp')]:
        rows=[r for r in data if start<=r[0]<=stop]
        intervals=[b[0]-a[0] for a,b in zip(rows,rows[1:]) if b[0]>a[0]]
        windows.append(dict(label=label,start_s=start,stop_s=stop,saved_rows=len(rows),
            saved_positive_interval_min_s=min(intervals),saved_positive_interval_max_s=max(intervals),
            vector_minmax={name:[min(r[i] for r in rows),max(r[i] for r in rows)] for i,name in enumerate(names) if i}))
    crossings=[]
    for left,right in zip(data,data[1:]):
        if left[1]<.6<=right[1]:
            crossings.append(left[0]+(.6-left[1])/(right[1]-left[1])*(right[0]-left[0]))
    log=(run/'run.log').read_text();initial,positive=log.split('Initial Transient Solution',1)
    output=dict(status='passed read-only finite early-wave observation',run=run.name,seed=76002,corner='fast',
        full3180_before_after_status='passed exact original failed-leaf BEFORE and prefix BEFORE/AFTER',
        saved_rows=len(data),decoded_wave_sha256=result['waveform_sha256'],snapshots=snapshots,windows=windows,
        observed_fout_rising_0p6V_crossings_s=crossings,
        warnings_before_initial_transient=len(re.findall('warning',initial,re.I)),
        warnings_after_initial_transient=len(re.findall('warning',positive,re.I)),
        original_full600s_status='failed numerical qualification; unchanged',
        frequency_accuracy_return_and_fast30_status='not qualified by this diagnostic',
        original_wave_prefix_comparison='not run; original full run exported no waveform',
        receipts_sha256={n:sha(run/n) for n in ['summary.json','provenance.json','preparation.json','probe.cir','run.json','run.log','phase0.dat.gz']},
        analyzer_sha256=sha(Path(__file__)),
        interpretation='Only accepted exported0..2us data. Output intervals are saved-grid intervals, not a reconstruction of all rejected internal solver steps. FOUTcrossings are event observations, not the original10..30us frequency measurement. No data exist here at the original2.275us stop; finiteearlywave doesnotlocate laternumericalcause or justify blindtimeout extension. No source/model/tolerance/calibration change.')
    a.output.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ['snapshots','windows','receipts_sha256']},indent=2))


if __name__=='__main__':main()
