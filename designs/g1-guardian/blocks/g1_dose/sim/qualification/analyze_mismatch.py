#!/usr/bin/env python3
"""Summarize qualified DOSE mismatch samples and select/reconcile hot anchors."""
import argparse,hashlib,json,math,statistics
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--nominal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--hot',type=Path);p.add_argument('--plot',action='store_true');a=p.parse_args();a.output.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(a.output/'runner.py').write_text(Path(__file__).read_text());data=json.loads((a.nominal/'manifest.json').read_text());rows=data['cases'];assert len(rows)==100 and all(r['status']=='passed' and r['frozen_all44'] for r in rows);assert len(set(r['seed'] for r in rows))==100
quantities=['HV_device_A','LV_device_A','HV_external_A','LV_external_A','HV_pad_A','LV_pad_A'];summary={}
def stats(values):
 s=sorted(values);n=len(s)
 def percentile(q):
  f=(n-1)*q;i=int(f);return s[i]+(s[min(i+1,n-1)]-s[i])*(f-i)
 return {'n':n,'mean_A':statistics.mean(s),'sample_sigma_A':statistics.stdev(s) if n>1 else None,'min_A':s[0],'p05_A':percentile(.05),'median_A':statistics.median(s),'p95_A':percentile(.95),'max_A':s[-1],'negative_count':sum(x<0 for x in s)}
for vg in ['0.0','0.3','0.6','1.2']:summary[vg]={q:stats([r['points']['t0_27'][vg][q] for r in rows]) for q in quantities}
lf=sorted(rows,key=lambda r:(r['points']['t0_27']['0.0']['LV_device_A'],r['seed']));hf=sorted(rows,key=lambda r:(r['points']['t0_27']['0.0']['HV_device_A'],r['seed']));picks=[('LV_min',lf[0]),('LV_lower_median',lf[49]),('LV_max',lf[-1]),('HV_min',hf[0]),('HV_max',hf[-1])];selected=[]
for reason,r in picks:
 x=next((x for x in selected if x['seed']==r['seed']),None)
 if x:x['reasons'].append(reason)
 else:selected.append({'seed':r['seed'],'reasons':[reason],'nominal_wave_sha256':r['waves']['t0_27']['sha256']})
fp=lambda r:next(iter(r['fingerprints'].values()));pads=[k for k in fp(rows[0]) if '.xp_' in k];assert len(pads)==36
padfixed=all(all(fp(r)[k]==fp(rows[0])[k] for k in pads) for r in rows)
assert padfixed
unique={dev:len({tuple((k,v) for k,v in fp(r).items() if f'.xm{n}.' in k) for r in rows}) for dev,n in [('LV',1),('HV',2)]}
assert unique=={'LV':100,'HV':100}
ratios={dev:stats([r['points']['t0_27']['0.0'][f'{dev}_pad_A']/r['points']['t0_27']['0.0'][f'{dev}_device_A'] for r in rows]) for dev in ['HV','LV']}
# Ratios are dimensionless; remove the current-unit suffix from the reused statistics keys.
ratios={dev:{k.removesuffix('_A'):v for k,v in x.items()} for dev,x in ratios.items()}
result={'scope':data['scope'],'nominal_samples':100,'temperature_C':27,'source_drain_V':1.2,'core_IO_supplies_V':[1.2,3.3],'source_sha256':sha(a.nominal/'manifest.json'),'script_sha256':sha(Path(__file__)),'current_definition':'device=intrinsic coupon drain terminal after pad/route probe, external=-ideal drain source current, pad=external-device. Signed values retained. No channel-only or on-die power interpretation.','statistics_by_applied_gate_V':summary,'zero_gate_pad_to_device_ratios':ratios,'unique_coupon_fingerprints':unique,'all36_pad_fingerprints_fixed':padfixed,'hot_selection':selected,'hot_selection_rule':'At gate0 choose min/lower-median(rank49)/max LV and min/max HV intrinsic currents; sort value then seed; deduplicate selected seeds. Selection is deliberate, not random statistical hot coverage.','hot_anchors':'not run','distribution_acceptance':'not applicable: no allocated current tolerance; statistical characterization only','physical_leakage_floor_radiation_response':'not run'}
if a.hot:
 hot=json.loads((a.hot/'manifest.json').read_text())['cases'];assert {r['seed'] for r in hot}=={r['seed'] for r in selected};comparisons=[]
 for h in hot:
  n=next(r for r in rows if r['seed']==h['seed']);match=fp(h)==fp(n) and h['waves']['t0_27']==n['waves']['t0_27'];restored=h['waves']['t2_27']==h['waves']['t0_27'];comparisons.append({'seed':h['seed'],'status':h['status'],'all44_params_match_nominal':fp(h)==fp(n),'first27C_wave_matches_nominal':h['waves']['t0_27']==n['waves']['t0_27'],'restored27C_wave_matches':restored,'frozen_all44':h['frozen_all44'],'zero_gate_125C':h['points']['t1_125']['0.0'],'HV_125over27_ratio':h['points']['t1_125']['0.0']['HV_device_A']/n['points']['t0_27']['0.0']['HV_device_A'],'LV_125over27_ratio':h['points']['t1_125']['0.0']['LV_device_A']/n['points']['t0_27']['0.0']['LV_device_A']});assert h['status']=='passed' and match and restored and h['frozen_all44']
 result['hot_anchors']={'status':'passed','source_sha256':sha(a.hot/'manifest.json'),'selected_count':len(hot),'comparisons':comparisons,'full_hot100_sample_ensemble':'not run'}
(a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');(a.output/'hot_seeds.txt').write_text(','.join(str(r['seed']) for r in selected)+'\n')
if a.plot:
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
 for ax,dev in zip(axes,['HV','LV']):
  intrinsic=[r['points']['t0_27']['0.0'][dev+'_device_A']*1e12 for r in rows];external=[r['points']['t0_27']['0.0'][dev+'_external_A']*1e12 for r in rows];ax.hist(intrinsic,bins=15,alpha=.75,label='Coupon terminal');ax.hist(external,bins=15,alpha=.6,label='External with pads') if dev=='LV' else ax.axvline(statistics.mean(external),color='tab:orange',lw=2,label=f'External mean {statistics.mean(external):.3f} pA');ax.set_xscale('log');ax.set_xlabel('Zero-gate drain current (pA), log scale');ax.set_ylabel('Sample count');ax.set_title(dev+' device, 100 samples at27°C');ax.legend();ax.grid(alpha=.2)
 fig.suptitle('Simulated nominal mismatch; no radiation or measurement-floor qualification');fig.savefig(a.output/'zero_gate_distributions.svg');fig.savefig(a.output/'zero_gate_distributions.png',dpi=150);plt.close(fig)
print(json.dumps({'zero_gate':summary['0.0'],'hot_selection':selected,'hot_status':result['hot_anchors']},indent=2))
