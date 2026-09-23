#!/usr/bin/env python3
"""Recompute fixed20 smoke evidence from saved decks/logs; no yield inference."""
import argparse,collections,json,statistics
from pathlib import Path
from run_rz100_mc_control import parse,electrical,errors,sha
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

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--packet',type=Path,required=True)
    ap.add_argument('--method',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--allow-incomplete',action='store_true')
    a=ap.parse_args();assert not a.output.exists()
    dispatch=json.loads((a.run/'dispatch.json').read_text())
    assert dispatch['seeds']==list(range(41001,41021))
    if not a.allow_incomplete:assert dispatch['no_future_launches'] is True
    pc,template,runtime=bound_inputs(a.packet,a.method)
    rows=[];parameters=[];calibration=[]
    for seed in dispatch['seeds']:
        folder=a.run/f'seed{seed}'
        ownership=dispatch['samples'][str(seed)]
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
            assert sha(folder/'runner.py')==dispatch['runner_sha256']
            log=(folder/'run.log').read_text()
            assert not errors(log) and 'QUALIFICATION_END' in log
            observed=parse(log,pc['queries']);e=electrical(observed['rows'])
            for key in ['rows','parameters','legacy']:assert observed[key]==reported[key]
            assert e==reported['electrical']
            parameters.append(dict(observed['parameters']));calibration.append(e['calibration_V'])
            row.update(controls='passed',electrical='passed' if all(e[k]=='passed' for k in
                ['gain_status','supported_offset_status']) else 'failed',
                all27_diagnostic=e['all27_offset_status'],gain_min=e['gain_min'],gain_max=e['gain_max'],
                worst_supported_residual_V=max(abs(p['residual_V']) for p in e['points'] if -.1<=p['true_cm_V']<=.3),
                calibration_V=e['calibration_V'],wall_s=run['wall_s'],
                log_sha256=sha(folder/'run.log'),summary_sha256=sha(folder/'summary.json'))
        except (AssertionError,KeyError,ValueError,OSError) as exc:row['analysis_error']=repr(exc)
    varied=[];constant=[]
    if len(parameters)>1:
        for q in pc['queries']:
            (varied if len({float(p[q]) for p in parameters})>1 else constant).append(q)
    counts=collections.Counter(r['controls'] for r in rows)
    complete=counts['passed']==20
    diversity=len(parameters)>1 and len({tuple(float(p[q]) for q in pc['queries']) for p in parameters})==len(parameters)
    mos_varied=any('.nsg13_' in q or '.psg13_' in q for q in varied)
    resistor_varied=any('[nsmm_' in q for q in varied)
    variability=diversity and mos_varied and resistor_varied and len(set(calibration))>1
    result=dict(status='passed complete smoke controls' if complete and variability else 'not run to full completion' if counts['not run'] else 'failed',
        expected=20,controls=dict(counts),electrical_passed=sum(r['electrical']=='passed' for r in rows),
        electrical_failed=sum(r['electrical']=='failed' for r in rows),
        rows=rows,source_sha256=SOURCE,nonzero_mismatch_variability='passed' if variability else 'not established',
        varied_parameters=varied,constant_parameters=constant,
        capacitor_mismatch='not applicable to unchanged cap_typ protocol; not qualified',
        calibration_sigma_V=statistics.pstdev(calibration) if calibration else None,
        scope=pc['scope'],full_PEX='not run',joint_chain='not run',hardware='not applicable',
        dispatcher_sha256=sha(a.run/'dispatch.json'))
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['rows','varied_parameters','constant_parameters','scope']}))
    raise SystemExit(0 if result['status'].startswith('passed') or a.allow_incomplete else 1)

if __name__=='__main__':main()
