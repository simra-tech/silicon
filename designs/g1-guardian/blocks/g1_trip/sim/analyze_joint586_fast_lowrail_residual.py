"""Read-only fixed fast-pilot rail contrasts; preserves both electrical failures."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from wave_archive import open_wave

SIM=Path(__file__).resolve().parent
PARENT=SIM/'qualification/joint586-fast-nodeset-calibration-s78101-20260923-a'
INDICES=[56,57,58,59,60,61,62,63]
DELAYS=[-1,0,.1,.3,.5,1,20]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def inspect(index,result):
    entry=result['probes'][index];leaf=SIM/'qualification'/entry['run']
    full=json.loads((leaf/'summary.json').read_text());state=json.loads((leaf/'run.json').read_text())
    assert entry['kind']=='residual' and entry['condition'][4]==0 and entry['wave_columns']==19
    assert state['status']=='completed' and state['returncode']==0 and entry['status']=='passed'
    assert sha(leaf/'summary.json')==entry['summary_sha256'] and sha(leaf/'probe.cir')==entry['deck_sha256']
    assert full['parameter_audit']['parameters_before']==full['parameter_audit']['parameters_after']==result['parameters_before_first_probe']
    with open_wave(leaf/'phase0.dat','rb') as stream:blob=stream.read()
    assert hashlib.sha256(blob).hexdigest()==entry['decoded_wave_sha256']
    lines=blob.splitlines();header=lines[0].decode().split();data=np.array([list(map(float,l.split())) for l in lines[1:] if l.strip()])
    assert data.shape==(entry['wave_rows'],19) and np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
    assert header[-1]=='v(shn)' and abs(data[-1,0]-1.02e-6)<1e-18
    assert max(abs((row[17]+row[18])/2) for row in data)<1e-12
    events=full['wave_analysis']['actual_clock_rising_crossings_s']['hard'][-3:];assert len(events)==3
    observations=[]
    for delay in DELAYS:
        samples=[]
        for edge in events:
            values={n:float(np.interp(edge+delay*1e-9,data[:,0],data[:,i])) for i,n in enumerate(header[1:],1)}
            values['hard_differential_V']=values['v(xt.icmp)']-values['v(xt.vth_hard)']
            samples.append(values)
        observations.append(dict(delay_after_actual_hard_edge_ns=delay,mean_V={k:sum(r[k] for r in samples)/3 for k in samples[0]}))
    return dict(index=index,condition=entry['condition'],shunt_V=entry['shunt_V'],codes=entry['codes'],decisions=entry['decisions'],expected_decisions=entry['expected_decisions'],
        observations=observations,decoded_wave_sha256=entry['decoded_wave_sha256'],receipts_sha256={n:sha(leaf/n) for n in ['probe.cir','run.json','summary.json']})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    audit=SIM/'qualification/joint586-fast-nodeset-s78101-firstsample-audit-20260923.json'
    assert sha(audit)=='e7b0eb6da25567e049c7d688795eb739b510c04bf6eda6217004283a597d688b'
    result,=json.loads((PARENT/'summary.json').read_text());rows=[inspect(i,result) for i in INDICES];lookup={r['index']:r for r in rows}
    assert all(r['codes']==[132,144] for r in rows)
    contrasts=[]
    for temperature,low,high in [(-40,57,61),(125,59,63)]:
        arow,brow=lookup[low],lookup[high]
        assert arow['condition'][1]==brow['condition'][1]==temperature and arow['shunt_V']==brow['shunt_V']==.0255
        for j,delay in enumerate(DELAYS):
            aobs=arow['observations'][j]['mean_V'];bobs=brow['observations'][j]['mean_V']
            slopes={}
            for label,lo,hi in [('lowrail',low-1,low),('highrail',high-1,high)]:
                x=lookup[lo]['observations'][j]['mean_V'];y=lookup[hi]['observations'][j]['mean_V']
                slopes[label]={k:(y[k]-x[k])/.001 for k in ['v(isense)','v(xt.icmp)','v(xt.vth_hard)','hard_differential_V']}
            contrasts.append(dict(temperature_C=temperature,delay_after_actual_hard_edge_ns=delay,
                low_minus_high_rail_V={k:aobs[k]-bobs[k] for k in aobs},periodic_input_finite_difference_V_per_V=slopes))
    report=dict(status='completed read-only lowrail residual triage',records=rows,contrasts=contrasts,auditor_sha256=sha(audit),analyzer_sha256=sha(Path(__file__)),
        original_electrical_failures=[57,59],scope='Same seed/frozen132/144 codes/temperature/trueCM0/shunt paired low3.0/1.08 versus high3.6/1.32 rails. Both rails and enable/clock/bitHIGH move together; not an isolated causal test. Saved-grid interpolation around actual hard edges, not internal rejected steps. ±0.5mV failures remain; no new simulation, source change, recalibration or population omission.')
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(sha(a.output))


if __name__=='__main__':main()
