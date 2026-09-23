#!/usr/bin/env python3
"""Recompute fixed20 or combined100 saved evidence; no joint-chain inference."""
import argparse,collections,json,statistics
from pathlib import Path
from run_rz100_mc_control import parse,electrical,errors,sha,SIM
from prepare_rz100_dc_grid import SOURCE

def bound_inputs(packet,method):
    pc=json.loads((packet/'contract.json').read_text())
    assert sha(packet/'contract.json')=='e014fa892b04904419ec5fc7614281a96580283088f8514289170434966a6741'
    assert sha(packet/'candidate.spice')==SOURCE
    assert sha(method/'summary.json')=='f42e73611f99353d6cd401eeceadcb55c75213203b3c55fdc7017243a7efdc0a'
    assert sha(method/'provenance.json')=='18bf99c9c9cb611cc1decba72b596348fc1a26d86696821783de2ee1e3163d12'
    assert sha(packet/'candidate.cir')==pc['artifacts']['candidate']['deck_sha256']
    template=(packet/'candidate.cir').read_text()
    assert template.count('setseed 41039\n')==1
    return pc,template,json.loads((method/'provenance.json').read_text())

def validate_dispatch(dispatch,seeds,terminal_required):
    assert dispatch['seeds']==seeds, 'Missing, duplicated or reordered sample plan'
    assert set(dispatch['samples'])==set(map(str,seeds)), 'Claim set differs from fixed plan'
    assert all(r['status'] in ['not run','running','terminal'] for r in dispatch['samples'].values())
    if terminal_required:assert dispatch['no_future_launches'] is True

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--screen',type=Path,help='Remaining80 directory; include original20 exactly once')
    ap.add_argument('--packet',type=Path,required=True)
    ap.add_argument('--method',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--allow-incomplete',action='store_true')
    a=ap.parse_args();assert not a.output.exists()
    dispatch=json.loads((a.run/'dispatch.json').read_text())
    validate_dispatch(dispatch,list(range(41001,41021)),not a.allow_incomplete)
    locations={seed:(a.run,dispatch) for seed in dispatch['seeds']}
    if a.screen:
        extra=json.loads((a.screen/'dispatch.json').read_text())
        validate_dispatch(extra,list(range(41021,41101)),not a.allow_incomplete)
        assert extra['smoke_audit_sha256']==sha(a.run/'audit_final_r1.json')=='5c9330764380f8d27dd7f5bd8fd70497a1779d769f302aa2837c7425f7f18efe'
        assert not set(extra['seeds'])&set(locations)
        locations.update({seed:(a.screen,extra) for seed in extra['seeds']})
    expected=100 if a.screen else 20
    assert sorted(locations)==list(range(41001,41001+expected))
    pc,template,runtime=bound_inputs(a.packet,a.method)
    rows=[];parameters=[];calibration=[]
    for seed,(directory,owner) in sorted(locations.items()):
        folder=directory/f'seed{seed}'
        ownership=owner['samples'][str(seed)]
        row=dict(seed=seed,controls='not run',electrical='not run',reason=ownership['status'])
        rows.append(row)
        if ownership['status']!='terminal':continue
        row['controls']='failed'
        try:
            assert ownership['returncode']==0
            run=json.loads((folder/'run.json').read_text())
            contract=json.loads((folder/'contract.json').read_text())
            reported=json.loads((folder/'summary.json').read_text())
            assert run['status']=='completed' and run['returncode']==0 and run['timeout_s']==120
            assert contract['seed']==seed and contract['source_sha256']==SOURCE and contract['runtime']==runtime
            assert contract['deck_sha256']==sha(folder/'probe.cir')
            assert (folder/'probe.cir').read_text()==template.replace('setseed 41039\n',f'setseed {seed}\n')
            assert sha(folder/'runner.py')==owner['runner_sha256']
            log=(folder/'run.log').read_text()
            assert not errors(log) and 'QUALIFICATION_END' in log
            observed=parse(log,pc['queries']);e=electrical(observed['rows'])
            for key in ['rows','parameters','legacy']:assert observed[key]==reported[key]
            assert e==reported['electrical']
            phase='smoke20' if seed<=41020 else 'screen80'
            prior=list((SIM/'qualification').glob(f'mc-gm4-comp3-{phase}-b*-20260922-a/seed{seed}.log'))
            assert len(prior)==1 and sha(prior[0])==contract['original_log_sha256']
            old=parse(prior[0].read_text(),[])
            assert observed['legacy']==old['legacy']
            parameters.append(dict(observed['parameters']));calibration.append(e['calibration_V'])
            row.update(controls='passed',electrical='passed' if all(e[k]=='passed' for k in
                ['gain_status','supported_offset_status']) else 'failed',
                all27_diagnostic=e['all27_offset_status'],gain_min=e['gain_min'],gain_max=e['gain_max'],
                worst_supported_residual_V=max(abs(p['residual_V']) for p in e['points'] if -.1<=p['true_cm_V']<=.3),
                calibration_V=e['calibration_V'],wall_s=run['wall_s'],
                historical_source_printed_DC_rows_exact=observed['row_lines']==old['row_lines'],
                log_sha256=sha(folder/'run.log'),summary_sha256=sha(folder/'summary.json'))
        except (AssertionError,KeyError,ValueError,OSError) as exc:row['analysis_error']=repr(exc)
    varied=[];constant=[]
    if len(parameters)>1:
        for q in pc['queries']:
            (varied if len({float(p[q]) for p in parameters})>1 else constant).append(q)
    counts=collections.Counter(r['controls'] for r in rows)
    complete=counts['passed']==expected
    diversity=len(parameters)>1 and len({tuple(float(p[q]) for q in pc['queries']) for p in parameters})==len(parameters)
    mos_varied=any('.nsg13_' in q or '.psg13_' in q for q in varied)
    resistor_varied=any('[nsmm_' in q for q in varied)
    variability=diversity and mos_varied and resistor_varied and len(set(calibration))>1
    passed='passed complete standalone100 controls' if a.screen else 'passed complete smoke controls'
    result=dict(status=passed if complete and variability else 'not run to full completion' if counts['not run'] else 'failed',
        expected=expected,controls=dict(counts),electrical_passed=sum(r['electrical']=='passed' for r in rows),
        electrical_failed=sum(r['electrical']=='failed' for r in rows),
        rows=rows,source_sha256=SOURCE,nonzero_mismatch_variability='passed' if variability else 'not established',
        varied_parameters=varied,constant_parameters=constant,
        capacitor_mismatch='not applicable to unchanged cap_typ protocol; not qualified',
        calibration_sigma_V=statistics.pstdev(calibration) if calibration else None,
        scope=pc['scope'],full_PEX='not run',joint_chain='not run',hardware='not applicable',
        dispatcher_sha256=sha(a.run/'dispatch.json'))
    if a.screen:result['screen_dispatcher_sha256']=sha(a.screen/'dispatch.json')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['rows','varied_parameters','constant_parameters','scope']}))
    raise SystemExit(0 if result['status'].startswith('passed') or a.allow_incomplete else 1)

if __name__=='__main__':main()
