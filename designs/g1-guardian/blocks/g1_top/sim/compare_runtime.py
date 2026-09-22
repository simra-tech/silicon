#!/usr/bin/env python3
"""Evaluate the predeclared native deterministic startup-prefix comparison."""
import argparse
import bisect
import hashlib
import json
from pathlib import Path
from check_campaign import read_wave

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def crossings(rows,index):
    result=[]
    for a,b in zip(rows,rows[1:]):
        if (a[index]<.6)!=(b[index]<.6):
            result.append((int(b[index]>=.6),a[0]+(.6-a[index])*(b[0]-a[0])/(b[index]-a[index])))
    return result
def interpolate(rows,times,t,index):
    if not times[0]<=t<=times[-1]:raise ValueError('requested time lies outside observed waveform')
    i=bisect.bisect_right(times,t)
    if i==0:return rows[0][index]
    if i==len(rows):return rows[-1][index]
    a,b=rows[i-1],rows[i]
    return a[index]+(b[index]-a[index])*(t-a[0])/(b[0]-a[0])
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('candidate',type=Path);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    if a.output.exists():ap.error('refusing to overwrite comparison')
    cp=HERE/'campaigns/native_prefix_contract_20260921.json';contract=json.loads(cp.read_text())
    ref=HERE/'campaigns'/contract['reference'];runs=[]
    checks={};identities=[]
    for label,path in [('reference',ref),('candidate',a.candidate)]:
        m=json.loads((path/'run.json').read_text());r=json.loads((path/'assessment.json').read_text())
        wave=path/'observations.tsv';cols,rows=read_wave(wave)
        checks[label+'_complete']=r['completion']=='passed' and abs(rows[-1][0]-contract['endpoint_s'])<1e-12
        checks[label+'_hash']=sha(wave)==r['observation_sha256']
        checks[label+'_source']=m['source_deck_sha256']==contract['source_sha256']
        rtl=m.get('rtl_sha256');origin=None
        if rtl is None:
            origin=HERE/'logs'/(Path(m['source_deck']).stem+'.json')
            original=json.loads(origin.read_text())
            rtl={k:v for k,v in original['input_sha256'].items() if '/rtl/' in k}
        identities.append(dict(manifest_sha256=sha(path/'run.json'),wave_sha256=sha(wave),
                               source_manifest_sha256=sha(origin) if origin else None,rtl=rtl,
                               model_cards=m['model_sha256'],image=m['image_id'],included=m['included_sha256']))
        runs.append((cols,rows,m))
    left,right=identities
    checks.update(model_cards_identical=left['model_cards']==right['model_cards'],rtl_identical=bool(left['rtl']) and left['rtl']==right['rtl'],
                  included_sources_identical=left['included']==right['included'],candidate_image=right['image']==contract['candidate_image'])
    if not all(checks.values()):
        result=dict(status='failed',checks=checks,waveform_comparison='not run',
                    reason='Complete endpoints and matching fixture identity are required; no extrapolation of partial observations.',
                    identities=identities,contract_sha256=sha(cp),checker_sha256=sha(Path(__file__)))
        a.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='identities'},indent=2));raise SystemExit(1)
    rc,rr,_=runs[0];cc,cr,_=runs[1];ri={c:i for i,c in enumerate(rc)};ci={c:i for i,c in enumerate(cc)};ct=[r[0] for r in cr]
    analog={c:max(abs(r[ri[c]]-interpolate(cr,ct,r[0],ci[c])) for r in rr) for c in contract['analog_vectors']}
    checks['analog_max_within_limit']=all(x<=contract['analog_max_difference_V'] for x in analog.values())
    edges={}
    for c in contract['digital_vectors']:
        x,y=crossings(rr,ri[c]),crossings(cr,ci[c])
        equal=len(x)==len(y) and all(a[0]==b[0] for a,b in zip(x,y))
        error=max((abs(a[1]-b[1]) for a,b in zip(x,y)),default=0) if equal else None
        edges[c]=dict(reference_count=len(x),candidate_count=len(y),max_time_difference_s=error)
        checks[c+'_edges']=equal and error<=contract['edge_tolerance_s']
        checks[c+'_final_logic']=(rr[-1][ri[c]]>=.6)==(cr[-1][ci[c]]>=.6)
    result=dict(status='passed' if all(checks.values()) else 'failed',checks=checks,
                analog_max_differences_V=analog,digital_edges=edges,identities=identities,
                contract_sha256=sha(cp),checker_sha256=sha(Path(__file__)),limitations=contract['limitations'])
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='identities'},indent=2))
    if result['status']!='passed':raise SystemExit(1)
if __name__=='__main__':main()
