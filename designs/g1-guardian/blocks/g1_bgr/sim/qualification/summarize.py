#!/usr/bin/env python3
"""Summarize retained runs; never turn solver completion into specification pass."""
import csv,json,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE/'runs'
def cases(name): return json.loads((ROOT/name/'manifest.json').read_text())['cases']
def data(run,name):
 with (ROOT/run/(name+'.dat')).open() as f: return [[float(x) for x in l.split()] for l in list(f)[1:]]
def main():
 qual='bgr_qual_20260921_02'; q=cases(qual)
 a=data(qual,'enabled_a'); b=data(qual,'enabled_repeat'); rev=list(reversed(data(qual,'enabled_reverse')))
 assert a==b
 assert all(r['fingerprints'][:3]==r['fingerprints'][3:] for r in q)
 assert q[0]['fingerprints']!=q[2]['fingerprints']
 assert data(qual,'disabled_a')==data(qual,'disabled_seed2')
 difference=max(abs(x[1]-y[1]) for x,y in zip(a,rev)); assert difference<1e-7
 mc=cases('bgr_mc20_20260921_01')+cases('bgr_mc100_20260921_01'); c=cases('bgr_corners81_20260921_01')
 assert len({r['seed'] for r in mc})==len(mc)==100
 assert all(len(r['fingerprints'])==6 and r['fingerprints'][:3]==r['fingerprints'][3:] for r in mc)
 summary={'qualification':'passed','repeat_vectors_identical':True,'reverse_Vref_max_difference_V':difference,'sample_fingerprints_retained':True,'mc':{'attempted':len(mc),'completed':sum(r['status']=='passed' for r in mc),'tc_failed':sum(r.get('tc_status')=='failed' for r in mc),'vref25_mean_V':statistics.mean(r['vref25'] for r in mc),'vref25_sigma_V':statistics.stdev(r['vref25'] for r in mc),'vref25_min_V':min(r['vref25'] for r in mc),'vref25_max_V':max(r['vref25'] for r in mc),'tc_max_ppm_C':max(r['tc_ppm_C'] for r in mc)},'corners':{'attempted':len(c),'completed':sum(r['status']=='passed' for r in c),'tc_failed':sum(r.get('tc_status')=='failed' for r in c),'worst_tc':max(c,key=lambda r:r['tc_ppm_C']),'hbt_vce_max_V':max(r['hbt_vce_max'] for r in c),'supply_current_max_A':max(r['current_max'] for r in c)}}
 (HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 rows=[{'campaign':campaign,**{k:r.get(k,'') for k in ['name','seed','hbt','mos','res','vdd','status','tc_status','vref25','tc_ppm_C','hbt_vce_max','wall_seconds']}} for campaign,rs in [('mc',mc),('corners',c)] for r in rs]
 with (HERE/'summary.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
 print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
