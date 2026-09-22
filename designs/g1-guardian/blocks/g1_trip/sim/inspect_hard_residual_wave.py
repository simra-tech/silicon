#!/usr/bin/env python3
"""Read retained hard-channel waveforms around reset/evaluation; no simulation."""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
from wave_archive import open_wave

SIM=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(name):
    directory=SIM/'qualification'/name
    summary=json.loads((directory/'summary.json').read_text())[0]
    provenance=json.loads((directory/'provenance.json').read_text())
    assert summary['solver_status']=='passed'
    deck=(directory/(summary['case']+'.cir')).read_text()
    assert 'Vclk clk 0 pulse(0 1.2 20n 0.2n 0.2n 50n 100n)' in deck
    assert 'v(clk) v(xt.icmp) v(xt.vth_soft) v(xt.vth_hard) v(cmp_soft) v(cmp_hard) v(isense)' in deck
    with open_wave(directory/(summary['case']+'.dat')) as stream:
        next(stream)
        data=[list(map(float,line.split())) for line in stream if line.strip()]
    assert data and all(len(row)==8 and all(math.isfinite(v) for v in row) for row in data)
    times=[row[0] for row in data]
    assert all(a<=b for a,b in zip(times,times[1:]))
    def at(t):
        index=bisect.bisect_left(times,t)
        assert 0<index<len(times)
        lo,hi=data[index-1],data[index]
        f=(t-lo[0])/(hi[0]-lo[0])
        return [u+f*(v-u) for u,v in zip(lo,hi)]
    def crossing(col,start,stop):
        found=[]
        for lo,hi in zip(data,data[1:]):
            if not start<=hi[0]<=stop:continue
            if (lo[col]-.6)*(hi[col]-.6)<0:
                t=lo[0]+(.6-lo[col])/(hi[col]-lo[col])*(hi[0]-lo[0])
                found.append({'time_s':t,'direction':'rising' if hi[col]>lo[col] else 'falling'})
        return found
    cycles=[]
    offsets=[19.8,20,20.2,21,40,69.8,70,70.2,70.25,70.3,70.35,70.4,70.5,70.7,70.95,71.2,72.2,75.2,80.2,90.2,99.8]
    for cycle in range(5):
        rows=[]
        for offset in offsets:
            t=(100*cycle+offset)*1e-9
            row=at(t)
            rows.append({'time_s':t,'offset_ns':offset,'external_clk_V':row[1],
                'conditioner_V':row[2],'hard_DAC_V':row[4],'hard_differential_V':row[2]-row[4],
                'hard_common_mode_V':(row[2]+row[4])/2,'hard_output_V':row[6],'isense_V':row[7]})
        pre=next(r for r in rows if r['offset_ns']==70)
        kick=next(r for r in rows if r['offset_ns']==71.2)
        sample=next(r for r in rows if r['offset_ns']==90.2)
        interval=[r for r in data if (cycle*100+70)*1e-9<=r[0]<=(cycle*100+90.2)*1e-9]
        cycles.append({'cycle':cycle,'samples':rows,
            'top_clock_threshold_crossings':crossing(1,(cycle*100+19)*1e-9,(cycle*100+72)*1e-9),
            'hard_output_threshold_crossings':crossing(6,(cycle*100+19)*1e-9,(cycle*100+99.8)*1e-9),
            'hard_differential_pre_V':pre['hard_differential_V'],
            'hard_differential_kick_1ns_V':kick['hard_differential_V']-pre['hard_differential_V'],
            'hard_differential_sample_V':sample['hard_differential_V'],
            'hard_differential_excursion_minmax_V':[min(r[2]-r[4] for r in interval),max(r[2]-r[4] for r in interval)],
            'late_hard_output_V':sample['hard_output_V']})
    args=provenance['runner_arguments']
    return {'run':name,'temperature_C':float(args[args.index('--temperature')+1]),
        'shunt_V':summary['shunt_V'],'quiet_hard_differential_V':summary['quiet_soft_hard_V'][1],
        'fixed_soft_hard_codes':[int(args[args.index('--soft-code')+1]),int(args[args.index('--hard-code')+1])],
        'fingerprints':summary['fingerprints'],'cycles':cycles,
        'initial_saved_time_s':data[0][0],'initial_saved_external_clk_V':data[0][1],
        'initial_saved_hard_output_V':data[0][6],
        'whole_wave_hard_output_threshold_crossings':crossing(6,data[0][0],data[-1][0]),
        'summary_sha256':sha(directory/'summary.json'),
        'provenance_sha256':sha(directory/'provenance.json'),'deck_sha256':sha(directory/(summary['case']+'.cir')),
        'sources':{n:sha(directory/n) for n in ['sense.spice','trip.spice','bgr.spice']}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    cases=[inspect(name) for name in a.runs]
    checks={'all27_same_observed_parameters':all(len(c['fingerprints'])==27 and c['fingerprints']==cases[0]['fingerprints'] for c in cases),
            'same_source_bytes':all(c['sources']==cases[0]['sources'] for c in cases),
            'same_calibration_codes':all(c['fixed_soft_hard_codes']==cases[0]['fixed_soft_hard_codes'] for c in cases)}
    report={'status':'passed read-only waveform extraction' if all(checks.values()) else 'failed comparison contract',
        'checks':checks,'characterization_clock_Hz':10000000,'nominal_actual_comparator_clock_Hz':5000000,
        'timing_scope':'Top clock rises20+100n ns and falls70.2+100n ns. Its measured0.6V crossings are recorded. Hard receives the inverted clock: top high is nominal hard reset, top low nominal hard evaluation. Internal inverter delay/reset nodes were not saved; those transitions cannot be measured here. Output SR keeper can retain a decision during front-end reset, so persistent q is not by itself proof of failed reset.',
        'acceptance_scope':'Read-only interpolation of the retained10MHz fixture, not a5MHz equivalence proof or a revised acceptance rule. Quiet values are initial OP differentials, not standalone comparator threshold measurements. Three stable late samples and all declared failed residuals remain preserved; combined source drift, kickback and comparator offset are not causally isolated.',
        'cases':cases}
    with a.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({'status':report['status'],'checks':checks,'cases':[{'run':c['run'],'temp_C':c['temperature_C'],'quiet_hard_differential_V':c['quiet_hard_differential_V'],'last_cycle':{k:v for k,v in c['cycles'][-1].items() if k!='samples'}} for c in cases]},indent=2))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__=='__main__':main()
