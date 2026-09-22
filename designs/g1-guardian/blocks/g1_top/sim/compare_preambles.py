#!/usr/bin/env python3
"""Compare completed compact/baseline c_mid armed states before their fault events."""
import argparse
import json
from pathlib import Path
from check_campaign import read_wave
from check_stream import CONTRACTS, sha

# Declared before the new baseline simulation reaches its comparison interval.
# These compare settled deterministic state, not MC accuracy or SEU history.
ANALOG_LIMIT_V=1e-3
ANALOG=['v(vref)','v(iptat)','v(isense)','v(xtrip.icmp)','v(xtrip.vth_soft)','v(xtrip.vth_hard)','v(vdda)','v(vdd)']
DIGITAL=['v(en_core)','v(inrush_active)','v(dig_trip)','v(fast_en)','v(cause1)','v(cause0)']+[f'v({p}{i})' for p in ['soft','hard'] for i in range(8)]

def interval(cols, rows, start, end):
    ix={c:i for i,c in enumerate(cols)}
    selected=[r for r in rows if start<=r[0]<=end]
    if len(selected)<2 or selected[0][0]>start+10e-9 or selected[-1][0]<end-10e-9:
        raise ValueError('armed comparison interval not sufficiently covered')
    span=selected[-1][0]-selected[0][0]
    means={c:sum((b[0]-a[0])*(a[ix[c]]+b[ix[c]])/2 for a,b in zip(selected,selected[1:]))/span for c in ANALOG}
    states={}
    for c in DIGITAL:
        levels={0 if r[ix[c]]<.2 else 1 if r[ix[c]]>1 else None for r in selected}
        states[c]=next(iter(levels)) if len(levels)==1 else None
    return means,states

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('compact',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    if a.output.exists():ap.error('preserve prior comparison')
    data=[];identity=[]
    for path in [a.compact,a.baseline]:
        m=json.loads((path/'run.json').read_text());r=json.loads((path/'assessment.json').read_text())
        contract=CONTRACTS[m['source_deck_sha256']]
        if r['completion']!='passed':ap.error('both waveform endpoints must be complete')
        w=path/'observations.tsv'
        if sha(w)!=r['observation_sha256']:ap.error('waveform hash mismatch')
        cols,rows=read_wave(w);data.append(interval(cols,rows,contract['event']-1e-6,contract['event']-.05e-6))
        identity.append(dict(campaign=path.name,source_sha256=m['source_deck_sha256'],wave_sha256=sha(w),models=m['model_sha256'],rtl=m['rtl_sha256'],image=m['image_id']))
    diffs={c:abs(data[0][0][c]-data[1][0][c]) for c in ANALOG}
    checks=dict(same_models=identity[0]['models']==identity[1]['models'],same_rtl=identity[0]['rtl']==identity[1]['rtl'],same_image=identity[0]['image']==identity[1]['image'],
        analog_means_close=all(v<=ANALOG_LIMIT_V for v in diffs.values()),states_equal=all(data[0][1][c] is not None and data[0][1][c]==data[1][1][c] for c in DIGITAL))
    out=dict(status='passed' if all(checks.values()) else 'failed',checks=checks,mean_differences_V=diffs,mean_limit_V=ANALOG_LIMIT_V,
        means=[d[0] for d in data],states=[d[1] for d in data],identity=identity,checker_sha256=sha(Path(__file__)),
        limitations='Pre-fault settled states only. Full SEU fill, clock phase/soft accumulator histories and comparator numerical accuracy are not qualified by this comparison.')
    a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='identity'},indent=2))
    if out['status']!='passed':raise SystemExit(1)

if __name__=='__main__':main()
