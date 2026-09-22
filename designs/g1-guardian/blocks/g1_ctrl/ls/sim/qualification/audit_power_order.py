#!/usr/bin/env python3
"""Bind nine power-order results to their qualified draw and exact bulk artifacts."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    original=a.results_root/'ls-mismatch-qualify-20260922-r1/repeat_a/analysis.json'
    fp=json.loads(original.read_text())['fingerprints']['t0_before']
    records=[]
    for order in 'ads':
        paths=[a.results_root/f'ls-powerorder-{order}-20260922-r1']
        paths += [a.results_root/f'ls-poweradverse-{order}-20260922-r1'/rail for rail in ('weak_core','strong_core')]
        for root in paths:
            analysis=json.loads((root/'analysis.json').read_text())
            contract=json.loads((root/'contract.json').read_text())
            assert analysis['numerical_status']==analysis['binding_status']==analysis['electrical_acceptance']=='passed'
            assert len(analysis['fingerprints'])==8 and all(v==fp for v in analysis['fingerprints'].values())
            assert sha(root/'fixture.cir')==analysis['deck_sha256']
            assert sha(root/'tool.log')==analysis['log_sha256']
            assert contract['source_sha256']=='087bdf16283f0aad73d940ef5c5a8d577764622ab243580bb77766d35a9da293'
            assert contract['script_sha256']==sha(Path(__file__).with_name('run_power_order.py'))
            assert [w['temperature_C'] for w in analysis['waves']]==[27,125,-40,27]
            for index,wave in enumerate(analysis['waves']):
                assert sha(root/f't{index}.tsv')==wave['sha256']
                assert len(wave['checks'])==5 and all(wave['checks'].values())
            assert analysis['waves'][0]['sha256']==analysis['waves'][3]['sha256']
            records.append(dict(run=str(root.relative_to(a.results_root)),
                                analysis_sha256=sha(root/'analysis.json'),contract_sha256=sha(root/'contract.json'),
                                contract=contract,analysis=analysis))
    metrics=[w['metrics'] for r in records for w in r['analysis']['waves']]
    result=dict(status='passed scoped extracted fixed-load power-order screen',completed_transients=36,
                settled_logic_checks_passed=180,qualified_draw_and_temperature_return='passed',
                retained_waveform_hashes='passed',nominal_and_opposite_rail_combinations=[[1.2,3.3],[1.08,3.6],[1.32,3.0]],
                source_reference_control_sha256=sha(original),
                worst_missing_core_output_V=max(m['core_absent']['out_max_V'] for m in metrics),
                worst_missing_core_injection_A=max(m['core_absent']['core_injection_peak_A'] for m in metrics),
                worst_missing_core_analog_draw_A=max(m['core_absent']['analog_draw_peak_A'] for m in metrics),
                current_limit_acceptance='not run',floating_absent_rail='not run',actual_receiver_mismatch='not run',
                physical_measurement='not applicable',
                scope='One qualified mismatch draw, TT mismatch models,20fF,three supply orders and four temperature visits. Ideal-clamped absent rail; no fullbackpowering/reliability/wholeV16 acceptance.',
                cases=records)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))


if __name__=='__main__':
    main()
