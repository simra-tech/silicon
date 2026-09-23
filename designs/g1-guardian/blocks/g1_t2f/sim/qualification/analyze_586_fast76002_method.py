#!/usr/bin/env python3
"""Matched numerical-method differences; no solver adoption or source-failure inference."""
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np
from prepare_586_fast76002_method import HERE,GEAR,sha


def load(run):
    row,=json.loads((run/'summary.json').read_text())
    assert row['control_status']=='passed waveform-only diagnostic' and row['full3180_status']=='passed'
    with gzip.open(str(run/'phase0.dat.gz'),'rb') as stream:blob=stream.read()
    assert hashlib.sha256(blob).hexdigest()==row['waveform_sha256']
    names=blob.splitlines()[0].decode().split();data=np.array([list(map(float,l.split())) for l in blob.splitlines()[1:] if l.strip()])
    assert data.shape[1]==13 and np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
    return row,blob,names,data


def edges(data,rising=True):
    result=[]
    for lo,hi in zip(data,data[1:]):
        crossed=lo[1]<.6<=hi[1] if rising else lo[1]>.6>=hi[1]
        if crossed:result.append(float(lo[0]+(.6-lo[1])/(hi[1]-lo[1])*(hi[0]-lo[0])))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    run=HERE/'runs'/a.run_id
    first,old,names,x=load(GEAR);second,new,other,y=load(run)
    assert names==other and first['parameters_before']==first['parameters_after']==second['parameters_before']==second['parameters_after']
    assert (run/'probe.cir').read_text().replace('method=trap','method=gear')==(GEAR/'probe.cir').read_text()
    assert all(sha(run/n)==sha(GEAR/n) for n in ['bgr.spice','t2f.spice','.spiceinit','population_inventory.json'])
    union=np.unique(np.concatenate([x[:,0],y[:,0]]));errors={}
    for i,name in enumerate(names[1:],1):
        delta=np.interp(union,y[:,0],y[:,i])-np.interp(union,x[:,0],x[:,i])
        errors[name]=dict(unit='A' if name.startswith('i(') else 'V',maximum_abs_difference=float(np.max(np.abs(delta))),
            rms_difference=float(np.sqrt(np.mean(delta**2))),scope='unweighteduniongrid linearinterpolation, not timeweightedRMS')
    events={}
    for label,rising in [('rising',True),('falling',False)]:
        a0,b0=edges(x,rising),edges(y,rising)
        events[label]=dict(gear_s=a0,trap_s=b0,count_exact=len(a0)==len(b0),
            index_paired_time_deltas_s=[b-a for a,b in zip(a0,b0)],pairing_scope='temporalindex pairs; count mismatch never silentlytruncated aspass')
    trajectories={}
    for label,data in [('gear',x),('trap',y)]:
        dt=np.diff(data[:,0]);trajectories[label]=dict(saved_rows=len(data),minimum_interval_s=float(dt.min()),
            median_interval_s=float(np.median(dt)),maximum_interval_s=float(dt.max()),
            windows=[dict(start_s=start,end_s=stop,rows=int(np.sum((data[:,0]>=start)&(data[:,0]<=stop))))
                for start,stop in [(0,1e-6),(1e-6,1.01e-6),(1.01e-6,2e-6)]],
            scope='Exported accepted-output trajectory only; no inference of rejectedNewton/integrationsteps')
    result=dict(status='completed matched numerical-method observation; no adoption',
        invariant3180_status='passed',exact_decoded_wave_status='passed' if old==new else 'failed exactbyte comparison',
        exact_saved_time_grid_status='passed' if np.array_equal(x[:,0],y[:,0]) else 'failed exactgrid comparison',
        actual_fout_0p6V_events=events,saved_trajectories=trajectories,uniongrid_vector_errors=errors,
        HBT_external_VCE_max_V=dict(gear=first['t2f_hbt_external_vce_max_V'],trap=second['t2f_hbt_external_vce_max_V']),
        wall_seconds=dict(gear=first['runtime']['wall_s'],trap=second['runtime']['wall_s']),
        original600s_full76002_status='failed; unchanged',full32us_retry_and_fast30_status='not run; not released',
        source_and_deck_identity=dict(gear_deck_sha256=sha(GEAR/'probe.cir'),trap_deck_sha256=sha(run/'probe.cir'),
            gear_summary_sha256=sha(GEAR/'summary.json'),trap_summary_sha256=sha(run/'summary.json')),
        analyzer_sha256=sha(Path(__file__)),
        interpretation='Method-dependentnumericaldifferences areobservations, not automatic sourcefailure or acceptancewaiver. Exactcomparisonfailures remainfailed; nodiagnosticbound replaces them. Wholetrajectory/firstevent/terminalcomparison informs anyseparatelyreviewed numericalremedy, not frequencyaccuracy/calibration/population qualification.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='uniongrid_vector_errors'},indent=2))


if __name__=='__main__':main()
