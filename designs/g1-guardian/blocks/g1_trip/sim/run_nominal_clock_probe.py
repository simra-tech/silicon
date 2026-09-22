#!/usr/bin/env python3
"""Execute one immutable prepared nominal-clock diagnostic, never regenerate inputs."""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from wave_archive import archive_new_wave
from compare_hot_residual_probes import decision

SIM=Path(__file__).resolve().parent
ROOT=SIM.parents[4]
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_saved_nodes(deck,trip):
    assert len(re.findall(r'^XT .+ g1_trip$',deck,re.M))==1
    body=re.search(r'^\.subckt g1_trip\s.+?^\.ends',trip,re.M|re.S).group()
    assert len(re.findall(r'^XCLKI cmp_clk cmp_clk_n vdd vss g1_inv$',body,re.M))==1
    assert len(re.findall(r'^XCH icmp vth_hard cmp_clk_n cmp_hard cmp_hard_n vdd vss g1_cmp$',body,re.M))==1
    comparator=re.search(r'^\.subckt g1_cmp inp inn clk q qb vdd vss\s.+?^\.ends',trip,re.M|re.S).group()
    nodes={word for line in comparator.splitlines() if line.startswith('XM') for word in line.split()[1:5]}
    assert {'xp','xq','xn','yn'}.issubset(nodes)
    expected=['xt.cmp_clk_n','xt.xch.xp','xt.xch.xq','xt.xch.xn','xt.xch.yn']
    for name in expected:
        assert len(re.findall(r'^\.save .+v\('+re.escape(name)+r'\)',deck,re.M))==1
        assert len(re.findall(r'^wrdata .+v\('+re.escape(name)+r'\)',deck,re.M))==1
    return {'status':'passed declared source-hierarchy audit','saved_internal_nodes':expected,
            'scope':'Exact prepared XT→g1_trip→XCH→g1_cmp instance chain and node declarations inspected. Runtime additionally requires13finite waveform columns; absent/invalid saved vectors fail closed.'}


def analyze_wave(data, sampling):
    assert data and all(len(row)==13 and all(math.isfinite(v) for v in row) for row in data)
    times=[row[0] for row in data]
    assert all(a<=b for a,b in zip(times,times[1:]))
    assert times[-1]>=1.02e-6*(1-1e-9)
    def at(t):
        index=bisect.bisect_left(times,t)
        assert 0<index<len(times)
        lo,hi=data[index-1],data[index]
        f=(t-lo[0])/(hi[0]-lo[0])
        return [u+f*(v-u) for u,v in zip(lo,hi)]
    def rises(col):
        return [lo[0]+(.6-lo[col])/(hi[col]-lo[col])*(hi[0]-lo[0])
                for lo,hi in zip(data,data[1:]) if lo[col]<.6<=hi[col]]
    actual={name:rises(col) for name,col in [('soft',1),('hard',8)]}
    counts={name:len(values) for name,values in actual.items()}
    result={'actual_clock_rising_crossings_s':actual,'rising_crossing_counts':counts,
            'sampling_status':'failed clock crossing count','comparators':{}}
    if counts!={'soft':5,'hard':5}:return result
    for name,outcol,daccol in [('soft',5,3),('hard',6,4)]:
        primary_times=[actual[name][i]+sampling['delay_after_measured_edge_s'] for i in [2,3,4]]
        legacy_times=sampling['legacy_phase_'+name+'_samples_s']
        primary=[at(t) for t in primary_times]
        legacy=[at(t) for t in legacy_times]
        primary_values=[row[outcol] for row in primary]
        legacy_values=[row[outcol] for row in legacy]
        main_decision=decision(primary_values);legacy_decision=decision(legacy_values)
        result['comparators'][name]={'measured_edge_sample_times_s':primary_times,
            'measured_edge_sample_output_V':primary_values,'measured_edge_decision':main_decision,
            'legacy_phase_sample_times_s':legacy_times,'legacy_phase_sample_output_V':legacy_values,
            'legacy_phase_decision':legacy_decision,
            'sampling_policies_agree':main_decision is not None and main_decision==legacy_decision,
            'measured_edge_sample_differentials_V':[row[2]-row[daccol] for row in primary]}
    result['hard_early_evaluation']=[]
    for index,edge in enumerate(actual['hard']):
        samples=[]
        for delay_ns in [-1,-.2,0,.05,.1,.2,.3,.5,.75,1,2,5,20]:
            row=at(edge+delay_ns*1e-9)
            samples.append({'delay_after_measured_edge_ns':delay_ns,'time_s':row[0],
                'actual_hard_clock_V':row[8],'hard_differential_V':row[2]-row[4],
                'hard_output_V':row[6],'hard_frontend_xp_xq_xn_yn_V':row[9:13]})
        result['hard_early_evaluation'].append({'edge_index':index,'actual_edge_s':edge,'samples':samples})
    result['sampling_status']='passed' if all(c['sampling_policies_agree'] for c in result['comparators'].values()) else 'failed mixed or disagreeing decision sampling'
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True)
    p.add_argument('--timeout-s',type=float,default=600)
    a=p.parse_args()
    assert '/' not in a.run_id and a.run_id not in ['.','..'] and 0<a.timeout_s<=600
    out=SIM/'qualification'/a.run_id
    prep=json.loads((out/'preparation.json').read_text())
    assert prep['run']==a.run_id and prep['status']=='prepared only; simulation not run'
    assert not (out/'summary.json').exists() and not (out/(prep['case']+'.log')).exists(),'Existing attempt is immutable'
    expected=prep['expected_runtime_identity']
    pd=Path('/foss/pdks/ihp-sg13g2')
    observed={'image_id_observed_by_host':a.image_id,'pdk_commit':(pd/'COMMIT').read_text().strip(),
              'ngspice_version':subprocess.check_output(['ngspice','--version'],text=True),
              'model_sha256':{str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},'solver':'sparse'}
    source_hashes={name:sha(out/name) for name in prep['source_hashes']}
    deck=out/(prep['case']+'.cir')
    source_nodes=validate_saved_nodes(deck.read_text(),(out/'trip.spice').read_text())
    checks={'prepared_deck_unchanged':sha(deck)==prep['prepared_deck_sha256'],
            'source_snapshots_unchanged':source_hashes==prep['source_hashes'],
            'runtime_pdk_models_exact':observed==expected,'saved_nodes_exist':source_nodes['status'].startswith('passed')}
    provenance={'arguments':sys.argv[1:],'preparation_sha256':sha(out/'preparation.json'),
                'reference_run':prep['reference_run'],'source_hashes':source_hashes,'runtime_identity':observed,
                'input_checks':checks,'saved_node_source_audit':source_nodes,'runner_sha256':sha(Path(__file__)),
                'prospective_sampling':prep['prospective_sampling'],'scope':prep['scope']}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (out/'runner.py').write_text(Path(__file__).read_text())
    assert all(checks.values()),'Input/runtime preflight failed; simulator not launched'
    with (out/(prep['case']+'.log')).open('x') as stream:
        state=run_bounded(['ngspice','-b',str(deck.relative_to(SIM))],stream,out/(prep['case']+'.json'),a.timeout_s,cwd=SIM,
            metadata={'seed':prep['seed'],'temperature_C':prep['temperature_C'],'deck_sha256':sha(deck),'clock_Hz':5000000},interval_s=1)
    log=(out/(prep['case']+'.log')).read_text()
    errors=[line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such vector|not available|cannot parse)',line)]
    fingerprints=re.findall(r'^(@[^=]+) = (\S+)',log,re.M)
    fingerprints=[list(pair) for pair in fingerprints]
    wave=out/(prep['case']+'.dat')
    complete=state['returncode']==0 and state['status']=='completed' and not errors and 'QUALIFICATION_END' in log and wave.exists()
    analysis={'sampling_status':'not run'}
    if complete:
        try:
            lines=wave.read_text().splitlines()
            assert len(lines[0].split())==13
            data=[list(map(float,line.split())) for line in lines[1:] if line.strip()]
            analysis=analyze_wave(data,prep['prospective_sampling'])
        except (AssertionError,ValueError,IndexError) as exc:
            complete=False;errors.append('Saved waveform contract failed: '+str(exc))
    fp_exact=len(fingerprints)==27 and fingerprints==prep['expected_observed27_parameters']
    decisions={name:record['measured_edge_decision'] for name,record in analysis.get('comparators',{}).items()}
    residual=('passed' if all(value is False for value in decisions.values()) else 'failed') if complete and fp_exact and analysis['sampling_status']=='passed' else 'not qualified'
    result={'seed':prep['seed'],'temperature_C':prep['temperature_C'],'shunt_V':prep['shunt_V'],
        'case':prep['case'],'solver_status':'passed' if complete else 'failed' if state['status']=='completed' else 'not run to completion',
        'watchdog_status':state['status'],'returncode':state['returncode'],'wall_s':state['wall_s'],
        'errors':errors,'fingerprints':fingerprints,'all27_parameters_exact':fp_exact,
        'nominal_clock_Hz':5000000,'fixed_soft_hard_codes':prep['fixed_soft_hard_codes'],
        'wave_analysis':analysis,'residual_lower_point_status':residual,
        'scope':'Exactly one5MHz lower-residual point with frozen10MHz-derived calibration codes. Original10MHz failure remains unchanged. Not full5MHz calibration/temperature/guard/statisticalqualification or isolated causality.'}
    (out/'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    if wave.exists():archive_new_wave(wave)
    print(json.dumps({key:result[key] for key in ['solver_status','wall_s','all27_parameters_exact','residual_lower_point_status','errors']},indent=2))
    raise SystemExit(0 if complete and fp_exact else 1)


if __name__=='__main__':main()
