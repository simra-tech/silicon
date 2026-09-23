#!/usr/bin/env python3
"""Read-only audit of preserved gm4 ideal-reference noise and finite-band windows."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from run_loaded_noise_audit import SOURCE, SIM, integrate, sha, table, tests

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); assert not a.output.exists()
    old=SIM/'qualification/noise-gm4-comp3-loaded-20260922-a'
    assert sha(old/'sense.spice')==SOURCE
    summary=json.loads((old/'summary.json').read_text())
    assert summary['status']=='passed'
    data=table(old/'noise.dat',['frequency','onoise_spectrum','inoise_spectrum'])
    assert data.shape==(701,3) and np.all(data[:,1:]>0)
    controls=tests(); rows=[]
    for band in summary['bands']:
        lower,upper=band['frequency_Hz']; totals=[0.,0.]
        for lo,hi in zip(data[:-1],data[1:]):
            end=min(hi[0],upper)
            if end<=lo[0]:continue
            q=(end-lo[0])/(hi[0]-lo[0])
            for c in [1,2]:
                endpsd=lo[c]**2+q*(hi[c]**2-lo[c]**2)
                totals[c-1]+=(lo[c]**2+endpsd)*(end-lo[0])/2
        rms=[math.sqrt(v) for v in totals]
        assert rms==[band['output_rms_V'],band['input_referred_rms_V']]
        actual_upper=min(upper,float(data[-1,0]))
        rows.append(dict(requested_upper_Hz=upper,actual_upper_Hz=actual_upper,preserved_trapezoid_rms_V=rms,
            loglinear_rms_V=[math.sqrt(integrate(data[:,0],data[:,c]**2,lower,actual_upper)) for c in [1,2]],
            assumed_boxcar=[dict(duration_s=t,rms_V=[math.sqrt(integrate(data[:,0],data[:,c]**2,lower,actual_upper,t)) for c in [1,2]]) for t in [20e-9,200e-9,1e-6]]))
    last=rows[-1]['preserved_trapezoid_rms_V']; printed=summary['ngspice_integrated_1Hz_10MHz']
    result=dict(status='passed exact preserved-band replay and independent integrator controls',
        sha256={p.name:sha(p) for p in [old/'sense.spice',old/'noise.cir',old/'noise.dat',old/'noise.log',old/'summary.json',old/'provenance.json']},
        rows=701,source_exact=True,controls=controls,bands=rows,
        native_integrated_total_relative_to_saved_trapezoid=dict(output=printed['onoise_total']/last[0]-1,input=printed['inoise_total']/last[1]-1),
        limitations=['Ideal reference/PTAT, passive TRIP load, not actualBGR/fullTRIP.',
            'No allocated noise limit; no physicalPEX or device-boundary closure.',
            'Native input-total vs independently integrated PSD discrepancy retained, not waived.',
            '20ns latency is not measurement aperture; all boxcar filters are declared sensitivity assumptions.',
            'No new simulator run. Finite1Hz..10MHz band, out-of-band variance unknown.'])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['bands','controls']},indent=2))

if __name__=='__main__':main()
