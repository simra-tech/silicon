#!/usr/bin/env python3
"""Finite-window synthetic perturbation characterization, not physical phase noise."""
import argparse, bisect, hashlib, json, math, statistics
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--block',choices=['osc','t2f'],required=True)
    ap.add_argument('--run-id',required=True)
    a=ap.parse_args()
    base=HERE.parents[2]/f'g1_{a.block}/sim/qualification'
    source=base/'runs'/a.run_id/'manifest.json'
    manifest=json.loads(source.read_text())
    cases=[]
    for old in manifest['cases']:
        row={k:v for k,v in old.items() if k not in ['periods_s','rising_edges_s']}
        if old['status']=='passed':
            edges=old['rising_edges_s'];period=statistics.mean(old['periods_s'])
            # Fit only a straight time origin/slope for descriptive TIE.
            # This does not change a calibration or remove individual failed cycles.
            n=len(edges);xm=(n-1)/2;ym=statistics.mean(edges)
            slope=sum((i-xm)*(t-ym) for i,t in enumerate(edges))/sum((i-xm)**2 for i in range(n))
            intercept=ym-slope*xm
            tie=[t-(intercept+slope*i) for i,t in enumerate(edges)]
            row['linear_detrended_TIE_rms_s']=math.sqrt(statistics.mean(v*v for v in tie))
            row['linear_detrended_TIE_peak_to_peak_s']=max(tie)-min(tie)
            windows={}
            for duration in [1e-6,5e-6,10e-6]:
                start=old['measurement_window_start_s'];end=old['measurement_window_end_s'];counts=[]
                # Ten fixed phases of the mean period show count-window quantization.
                for phase in range(10):
                    lo=start+phase*period/10
                    while lo+duration<=end:
                        count=bisect.bisect_left(edges,lo+duration)-bisect.bisect_left(edges,lo)
                        counts.append(count);lo+=duration
                windows[f'{duration:g}s']={'window_duration_s':duration,'window_count':len(counts),
                                          'minimum_edge_count':min(counts) if counts else None,
                                          'maximum_edge_count':max(counts) if counts else None,
                                          'count_frequency_std_Hz':statistics.pstdev(counts)/duration if counts else None,
                                          'one_count_frequency_step_Hz':1/duration}
            row['finite_counter_windows']=windows
        cases.append(row)
    result={'run_id':a.run_id,'manifest_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'cases':cases,'expected_amplitudes_mV':[0,1,5],
            'completion_status':'passed' if len(cases)==3 and all(r['status']=='passed' for r in cases) else 'failed or incomplete',
            'acceptance':'Characterization only; no physical phase-noise or jitter-budget pass.',
            'limitations':'Fixed finite external OU waveform, ideal rail/series-reference injection, stand-in output load. TIE slope removal is descriptive only. Counter windows overlap across ten phases and are not independent statistical samples. Count spread includes deterministic quantization and simulator baseline. No extrapolation to longer hardware measurement windows or packaged silicon.'}
    (base/'runs'/a.run_id/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
