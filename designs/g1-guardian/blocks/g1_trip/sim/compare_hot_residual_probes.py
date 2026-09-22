#!/usr/bin/env python3
"""Audit exactly declared hot shunt probes; preserve original residual acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

SIM=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_deck(directory, case, expected_shunt):
    text=(directory/(case+'.cir')).read_text().replace(directory.name,'@RUN@')
    match=re.findall(r'^Vsh shp 0 dc (\S+)$',text,re.M)
    assert len(match)==1 and float(match[0])==expected_shunt
    text,n=re.subn(r'^Vsh shp 0 dc \S+$','Vsh shp 0 dc @DECLARED_SHUNT@',text,flags=re.M)
    assert n==1
    text,n=re.subn(r'(shunt input set )\S+( so the soft comparator)',r'\1@DECLARED_SHUNT@\2',text)
    assert n==1
    return text


def decision(values):
    if len(values)!=3 or not all(math.isfinite(v) for v in values):return None
    if all(v>.6 for v in values):return True
    if all(v<.6 for v in values):return False
    return None


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',required=True)
    p.add_argument('--runs',nargs=2,required=True)
    p.add_argument('--expected-shunts',nargs=2,type=float,required=True)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    refdir=SIM/'qualification'/a.reference
    reference=json.loads((refdir/'summary.json').read_text())[0]
    refprov=json.loads((refdir/'provenance.json').read_text())
    refargs=refprov['runner_arguments']
    assert reference['shunt_V']==.0245 and refprov['seed']==71002
    assert float(refargs[refargs.index('--temperature')+1])==125
    assert [int(refargs[refargs.index(k)+1]) for k in ['--soft-code','--hard-code']]==[136,154]
    assert decision(reference['both_sampled_output_V']['hard']) is True
    assert sorted(a.expected_shunts)==[.024,.02425]
    normalized=normalized_deck(refdir,reference['case'],reference['shunt_V'])
    cases=[]
    for name,expected_shunt in zip(a.runs,a.expected_shunts):
        directory=SIM/'qualification'/name
        result=json.loads((directory/'summary.json').read_text())[0]
        provenance=json.loads((directory/'provenance.json').read_text())
        checks={'numerical_complete':result['solver_status']==reference['solver_status']=='passed',
                'declared_shunt_exact':result['shunt_V']==expected_shunt,
                'entire_deck_exact_except_declared_shunt_and_run_label':normalized_deck(directory,result['case'],expected_shunt)==normalized,
                'sources_exact':all(sha(directory/n)==sha(refdir/n) for n in ['sense.spice','trip.spice','bgr.spice']),
                'model_tool_pdk_solver_seed_exact':all(provenance[k]==refprov[k] for k in ['model_sha256','image_id_observed_by_host','pdk_commit','ngspice_version','solver','seed']),
                'all27_parameters_exact':len(result['fingerprints'])==27 and result['fingerprints']==reference['fingerprints']}
        outputs=result.get('both_sampled_output_V',{})
        decisions={channel:decision(outputs.get(channel,[])) for channel in ['soft','hard']}
        checks['three_unanimous_late_decisions']=all(v is not None for v in decisions.values())
        cases.append({'run':name,'shunt_V':result['shunt_V'],'checks':checks,'decisions':decisions,
            'late_outputs_V':outputs,'quiet_soft_hard_V':result.get('quiet_soft_hard_V'),
            'measures':result.get('measures'),'wall_s':result.get('wall_s'),
            'summary_sha256':sha(directory/'summary.json'),'provenance_sha256':sha(directory/'provenance.json'),
            'deck_sha256':sha(directory/(result['case']+'.cir'))})
    passed=all(all(c['checks'].values()) for c in cases)
    points=[{'run':c['run'],'shunt_V':c['shunt_V'],'hard_high':c['decisions']['hard']} for c in cases]
    points.append({'run':a.reference,'shunt_V':reference['shunt_V'],'hard_high':decision(reference.get('both_sampled_output_V',{}).get('hard',[]))})
    points.sort(key=lambda x:x['shunt_V'])
    bracket=None
    monotonic=all(x['hard_high'] is not None for x in points) and all(x['hard_high']<=y['hard_high'] for x,y in zip(points,points[1:]))
    lows=[x['shunt_V'] for x in points if x['hard_high'] is False]
    highs=[x['shunt_V'] for x in points if x['hard_high'] is True]
    if passed and monotonic and lows and highs:bracket=[max(lows),min(highs)]
    report={'status':'passed controlled diagnostic comparison' if passed else 'failed comparison contract',
        'cases':cases,'reference':a.reference,'reference_summary_sha256':sha(refdir/'summary.json'),
        'prospective_sampling':{'hard_times_s':[290.2e-9,390.2e-9,490.2e-9],'soft_times_s':[240e-9,340e-9,440e-9],'logic_threshold_V':.6,'rule':'All three strictly on the same side; no majority vote.'},
        'sampled_hard_points':points,'sampled_point_monotonicity':monotonic,
        'observed_low_high_shunt_bracket_V':bracket,
        'nominal25mV_minus_observed_bracket_V':[.025-bracket[1],.025-bracket[0]] if bracket else None,
        'original500uV_residual_acceptance':'failed: preserved24.5mV reference is hardHIGH; diagnostic does not rewrite acceptance',
        'characterization_clock_Hz':10000000,'nominal_actual_comparator_clock_Hz':5000000,
        'scope':'Exactly two declared shunt changes at fixed seed/source/calibrationcodes136/154 and125C. Sparse selected points do not establish a unique continuous offset or monotonicity between unsampled points. Clock frequency remains10MHz characterization, not nominal5MHz equivalence. No isolated block attribution, fresh calibration, midpoint authorization or qualification waiver.'}
    with a.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':main()
