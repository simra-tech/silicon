#!/usr/bin/env python3
"""Analyze saved SENSE OP rows; no inference of joint-chain trim reach or yield."""
import argparse,json,math,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--extra',type=Path,nargs='*',default=[]);a=p.parse_args()
rows=json.loads((a.directory/'summary.json').read_text())
for extra in a.extra: rows+=json.loads((extra/'summary.json').read_text())
assert len({r['seed'] for r in rows})==len(rows), 'duplicate seeds cannot be counted as independent samples'
results=[]
for s in rows:
    if s['status']!='passed':continue
    r=s['rows'];nom=51/53*1.04
    calibration=(r['t0_c0_s0.025'][0]-nom)/20-.025
    calrow=r['t0_c0_s0.025']
    # Offline ideal DAC/comparator diagnostic; no switch/comparator/BGR mismatch.
    crossing_code=530*(calrow[0]/2)/calrow[2]-255
    correction_real=crossing_code-.025*5300/1.04
    correction=math.floor(correction_real+.5)
    trim=max(-128,min(127,correction))
    hard_unclipped=254+trim;soft_unclipped=153+trim
    headroom={'interior25mV_crossing_code':crossing_code,'signed_code_correction':correction,'trim_register_clipped':trim!=correction,
              'hard_effective_code':max(0,min(255,hard_unclipped)),'hard_clipped':not 0<=hard_unclipped<=255,
              'soft_effective_code':max(0,min(255,soft_unclipped)),'soft_clipped':not 0<=soft_unclipped<=255}
    residues=[];residual_points=[];gains=[]
    for ti in range(3):
        for cm in [-.1,0,.3]:
            gains.append((r[f't{ti}_c{cm}_s0.05'][0]-r[f't{ti}_c{cm}_s0'][0])/.05)
            for sh in [0,.025,.05]:
                residues.append((r[f't{ti}_c{cm}_s{sh}'][0]-nom)/20-sh-calibration)
                residual_points.append({'temperature_C':[25,-40,125][ti],'sense_n_V':cm,'shunt_V':sh,'residual_V':residues[-1]})
    worst=max(residual_points,key=lambda x:abs(x['residual_V']))
    ti=[25,-40,125].index(worst['temperature_C'])
    wr=r[f"t{ti}_c{worst['sense_n_V']}_s{worst['shunt_V']}"]
    cr=r['t0_c0_s0.025']
    ped_delta=(wr[1]-cr[1])/20
    main_delta=-21*((wr[3]-wr[4])-(cr[3]-cr[4]))/20
    decomposition={'pedestal_input_referred_V':ped_delta,'main_closed_loop_input_difference_V':main_delta,
                   'resistor_network_remainder_V':worst['residual_V']-ped_delta-main_delta}
    results.append({'seed':s['seed'],'uncalibrated_input_error_V':calibration,'worst_frozen_continuous_correction_residual_V':max(map(abs,residues)),
                    'worst_point':worst,'worst_point_decomposition':decomposition,'ideal_DAC_headroom_diagnostic':headroom,
                    'gain_min':min(gains),'gain_max':max(gains),'frozen_random_fingerprint':s['frozen_sample'],
                    'returned_25C_identical':all(r[k]==r[k.replace('t0_','t3_')] for k in r if k.startswith('t0_')),
                    'offset_target_status':'passed' if max(map(abs,residues))<.0005 else 'failed',
                    'gain_target_status':'passed' if min(gains)>=19.9 and max(gains)<=20.1 else 'failed'})
summary={'source_run_directories':[str(a.directory)]+[str(x) for x in a.extra],'attempted':len(rows),'completed':len(results),'failed':sum(s['status']=='failed' for s in rows),'timed_out':sum(s['status']=='not run to completion' for s in rows),
         'calibration':'Ideal continuous one-point correction at25C/CM0/shunt25mV; gain fixed20; ideal VREF/PTAT. This does not prove digital trim reach or joint-chain accuracy.',
         'sample_results':results}
if results:
    x=[r['uncalibrated_input_error_V'] for r in results]
    summary.update(uncalibrated_input_error_mean_V=statistics.mean(x),uncalibrated_input_error_population_sigma_V=statistics.pstdev(x),
        worst_frozen_continuous_correction_residual_V=max(r['worst_frozen_continuous_correction_residual_V'] for r in results),
        offset_target_failures=sum(r['offset_target_status']=='failed' for r in results),gain_target_failures=sum(r['gain_target_status']=='failed' for r in results),
        ideal_DAC_hard_clipping_samples=sum(r['ideal_DAC_headroom_diagnostic']['hard_clipped'] for r in results),
        ideal_DAC_soft_clipping_samples=sum(r['ideal_DAC_headroom_diagnostic']['soft_clipped'] for r in results),
        headroom_scope='Offline SENSE-only diagnostic using sample VREF_BUF and an ideal(255+code)/530 DAC, zero comparator offset, nominal interior25mV calibration. Actual DAC loading/mismatch/BGR/comparator not included; not joint-chain yield.')
(a.directory/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='sample_results'},indent=2))
