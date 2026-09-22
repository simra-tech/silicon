#!/usr/bin/env python3
"""Prepare an explicit5MHz diagnostic from immutable10MHz inputs; never simulate."""
import argparse
import difflib
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from result_directory import allocate_run

SIM=Path(__file__).resolve().parent


def digest(data):return hashlib.sha256(data).hexdigest()


def prepare(reference_id, run_id):
    reference=SIM/'qualification'/reference_id
    summary=json.loads((reference/'summary.json').read_text())[0]
    provenance=json.loads((reference/'provenance.json').read_text())
    args=provenance['runner_arguments']
    assert provenance['seed']==71002 and summary['solver_status']=='passed'
    assert summary['shunt_V']==.0245 and len(summary['fingerprints'])==27
    assert [int(args[args.index(k)+1]) for k in ['--soft-code','--hard-code']]==[136,154]
    temperature=float(args[args.index('--temperature')+1])
    assert temperature in [25,125] and provenance['solver']=='sparse'
    old=(reference/(summary['case']+'.cir')).read_text()
    deck=old.replace(reference_id,run_id)
    clock_old='Vclk clk 0 pulse(0 1.2 20n 0.2n 0.2n 50n 100n)'
    clock_new='Vclk clk 0 pulse(0 1.2 20n 0.2n 0.2n 100n 200n)'
    assert deck.count(clock_old)==1
    deck=deck.replace(clock_old,clock_new)
    assert deck.count('tran 0.2n 0.52u 0 0.2n')==1
    deck=deck.replace('tran 0.2n 0.52u 0 0.2n','tran 0.2n 1.02u 0 0.2n')
    old_times={'ds_pre':419.8e-9,'ds_kick':421e-9,'ds_sample':440e-9,'qs_sample':440e-9,
               'dh_pre':470e-9,'dh_kick':471.2e-9,'dh_sample':490.2e-9,'qh_sample':490.2e-9}
    new_times={'ds_pre':819.8e-9,'ds_kick':821e-9,'ds_sample':840e-9,'qs_sample':840e-9,
               'dh_pre':920e-9,'dh_kick':921.2e-9,'dh_sample':940.2e-9,'qh_sample':940.2e-9}
    seen=[]
    def update_measure(match):
        name=match[2]
        assert name in old_times and math.isclose(float(match[3]),old_times[name],rel_tol=1e-12)
        seen.append(name)
        return match[1]+format(new_times[name],'.12g')
    deck,count=re.subn(r'^(meas tran (\w+) find \S+ at=)(\S+)$',update_measure,deck,flags=re.M)
    assert count==8 and set(seen)==set(old_times)
    extra=' v(xt.cmp_clk_n) v(xt.xch.xp) v(xt.xch.xq) v(xt.xch.xn) v(xt.xch.yn)'
    deck,count=re.subn(r'^\.save .+$',lambda m:m[0]+extra,deck,flags=re.M)
    assert count==1
    deck,count=re.subn(r'^wrdata .+$',lambda m:m[0]+extra,deck,flags=re.M)
    assert count==1
    out=allocate_run(SIM,run_id)
    sources={}
    for filename in ['sense.spice','trip.spice','bgr.spice']:
        raw=(reference/filename).read_bytes()
        (out/filename).write_bytes(raw)
        sources[filename]=digest(raw)
    assert sources['sense.spice']=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    case=summary['case']
    (out/(case+'.cir')).write_text(deck)
    (out/'preparer.py').write_text(Path(__file__).read_text())
    diff=''.join(difflib.unified_diff(old.replace(reference_id,'@RUN@').splitlines(True),deck.replace(run_id,'@RUN@').splitlines(True),fromfile='preserved10MHz',tofile='prepared5MHz'))
    (out/'declared_clock_difference.diff').write_text(diff)
    preparation={'status':'prepared only; simulation not run','reference_run':reference_id,'run':run_id,
        'seed':71002,'temperature_C':temperature,'shunt_V':.0245,'fixed_soft_hard_codes':[136,154],
        'source_hashes':sources,'reference_summary_sha256':digest((reference/'summary.json').read_bytes()),
        'reference_provenance_sha256':digest((reference/'provenance.json').read_bytes()),
        'prepared_deck_sha256':digest(deck.encode()),'case':case,
        'expected_observed27_parameters':summary['fingerprints'],
        'expected_runtime_identity':{key:provenance[key] for key in ['image_id_observed_by_host','pdk_commit','ngspice_version','model_sha256','solver']},
        'clock_difference':{'old_line':clock_old,'new_line':clock_new,'rise_fall_s':.2e-9,'old_endpoint_s':.52e-6,'new_endpoint_s':1.02e-6},
        'prospective_sampling':{'cycles':[2,3,4],
            'soft_nominal_evaluation_starts_s':[420e-9,620e-9,820e-9],
            'hard_nominal_evaluation_starts_s':[520.2e-9,720.2e-9,920.2e-9],
            'legacy_phase_soft_samples_s':[440e-9,640e-9,840e-9],
            'legacy_phase_hard_samples_s':[540.2e-9,740.2e-9,940.2e-9],
            'primary_rule':'Sample20ns after each measured0.6V rising crossing of its actual clock: topclk for soft, savedxt.cmp_clk_n for hard. Require five rising crossings/channel and select indices2/3/4. Actual inverter delay is measured, not assumed.',
            'comparison_rule':'Also report the mapped legacy fixed-phase samples. Each set requires all3strictly on same side of0.6V; any mixed or disagreeing classifications are flagged, never majority-voted. Old10MHz internalclkn was not saved, so do not claim exact timing-policy equivalence.',
            'delay_after_measured_edge_s':20e-9,'logic_threshold_V':.6},
        'wave_columns':['time','clk','icmp','vth_soft','vth_hard','cmp_soft','cmp_hard','isense','cmp_clk_n','hard_xp','hard_xq','hard_xn','hard_yn'],
        'additional_observability':'Clock_n establishes actual hard evaluation timing; xp/xq/xn/yn expose front-end precharge/regeneration. These are saved vectors only; no circuit devices, loads or models are added.',
        'unchanged':'All circuit devices/connections, input, loads, rail values, temperature per reference, seed, observed-parameter print list, model libraries, solver/tolerances/integration/maxstep, calibration codes and0.2nsclock rise/fall remain literal unchanged. Diff records all changes.',
        'planning':{'per_leaf_watchdog_s':600,'reference_leaf_wall_s':summary['wall_s'],
            'endpoint_ratio_linear_time_estimate_s':summary['wall_s']*1.02/.52,
            'home_growth_budget_GiB_for_two':.1,'forecast_limit':'Linear time estimate is not a proven worst case; startup/OP cost and slowerclock behavior can differ.'},
        'scope':'Prepare-only dynamic timing versus thermal diagnostic. No simulator ran.5MHz results would not retroactively reclassify the preserved10MHz residual failure, establish statisticalqualification, or replace a separately declared5MHz calibration campaign.'}
    (out/'preparation.json').write_text(json.dumps(preparation,indent=2)+'\n')
    return preparation


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',required=True);p.add_argument('--run-id',required=True)
    a=p.parse_args()
    result=prepare(a.reference,a.run_id)
    print(json.dumps({k:v for k,v in result.items() if k not in ['expected_runtime_identity','expected_observed27_parameters']},indent=2))


if __name__=='__main__':main()
