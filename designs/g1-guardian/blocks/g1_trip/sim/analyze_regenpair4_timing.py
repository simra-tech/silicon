"""Saved-wave regeneration observations, not a new acceptance or latency limit."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from wave_archive import open_wave

SIM=Path(__file__).resolve().parent
Q=SIM/'qualification'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def persistent_crossing(time,values,start,end,level):
    indexes=np.flatnonzero((time>=start)&(time<=end))
    assert len(indexes)>1
    good=np.abs(values[indexes])>=level
    # The final uninterrupted run above the diagnostic threshold, not an early glitch.
    if not good[-1]:return dict(status='not reached persistently by observation end')
    lastbad=np.flatnonzero(~good)
    j=indexes[lastbad[-1]+1] if len(lastbad) else indexes[0]
    k=max(0,j-1)
    a,b=abs(values[k]),abs(values[j])
    crossing=time[j] if b==a else time[k]+(level-a)*(time[j]-time[k])/(b-a)
    crossing=max(float(start),float(crossing))
    return dict(status='observed',delay_s=crossing-start,time_s=crossing,bracket_s=[float(time[k]),float(time[j])],
                resolved_sign=1 if values[j]>0 else -1,level_V=level)


def inspect(run,vdd):
    leaf=Q/run;d=json.loads((leaf/'summary.json').read_text())
    assert d.get('numerical_status',d.get('status'))=='passed'
    state=json.loads((leaf/'run.json').read_text());assert state['status']=='completed' and state['returncode']==0
    with open_wave(leaf/'phase0.dat','rb') as stream:blob=stream.read()
    header=blob.splitlines()[0].decode().split();assert header[11:13]==['v(xt.xch.xn)','v(xt.xch.yn)']
    data=np.array([list(map(float,line.split())) for line in blob.splitlines()[1:] if line.strip()]);assert np.isfinite(data).all()
    assert len(header)==data.shape[1]==19 and abs(data[-1,0]-1.02e-6)<1e-18
    differential=data[:,11]-data[:,12]
    observations=[persistent_crossing(data[:,0],differential,edge,edge+20e-9,.9*vdd)
                  for edge in d['wave_analysis']['actual_clock_rising_crossings_s']['hard']]
    return dict(run=run,hashes={n:sha(leaf/n) for n in ['summary.json','run.json','probe.cir']},
                decoded_wave_sha256=hashlib.sha256(blob).hexdigest(),frontend_regeneration_90pct_rail_observations=observations,
                hard_late=d['wave_analysis']['comparators']['hard'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    audit=Q/'joint586-regenpair4-c45rz62-20260923-a-audit.json';d=json.loads(audit.read_text())
    assert len(d['records'])==2 and all(r['independent_reconstruction']=='passed' for r in d['records'])
    rows=[]
    for index,vdd in [(57,1.08),(61,1.32)]:
        rows.append(inspect('joint586-fast-nodeset-calibration-s78101-20260923-a/p%d'%index,vdd))
        if index==57:rows.append(inspect('joint586-c45rz62-knownfailure-s78101-p57-20260923-a',vdd))
        rows.append(inspect('joint586-regenpair4-c45rz62-20260923-a-p%d'%index,vdd))
    result=dict(status='completed saved-wave timing diagnostic',audit_sha256=sha(audit),analyzer_sha256=sha(Path(__file__)),records=rows,
        geometric_gate_area_um2=dict(original_each=.39,candidate_each=1.56,original_pair=.78,candidate_pair=3.12),
        measured_terminal_capacitance='not run; area4 is geometry, not a measured4x capacitance',
        rail_and_clock_power='not run; no qualified rail-current vectors in these original fixtures',
        scope='Diagnostic90%configuredrail threshold on |xn-yn| sustained through actualedge+20ns, allfiveedges retained. Not a new acceptance limit. Original20ns decisions and ±0.5mV limits unchanged. Native-grid linear crossing interpolation with saved brackets is not a universal error bound. Power/native fit/statistical qualification remain not run.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.output.name,sha(a.output))


if __name__=='__main__':main()
