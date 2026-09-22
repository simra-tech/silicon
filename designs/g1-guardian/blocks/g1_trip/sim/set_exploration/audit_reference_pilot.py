#!/usr/bin/env python3
"""Independently audit reference charge runs and report timestep sensitivity."""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    records, comparisons, vectors = [], [], []
    for case in ('zero', 'inject', 'sink'):
        pair = []
        for step, prefix in ((2, 'bgr-set-'), (1, 'bgr-set-step1-')):
            name = prefix + case + '-20260922-r1'
            root = args.results_root / name
            contract = json.loads((root/'contract.json').read_text())
            result = json.loads((root/'analysis.json').read_text())
            run = json.loads((root/'run.json').read_text())
            assert run['status'] == 'completed' and run['returncode'] == 0
            assert result['status'] == 'passed characterization' and result['inputs_unchanged']
            assert sha(root/'source.spice') == contract['source_sha256']
            assert sha(root/'runner.py') == contract['script_sha256']
            assert sha(root/'fixture.cir') == result['deck_sha256']
            assert sha(root/'tool.log') == result['log_sha256']
            assert sha(root/'wave.tsv') == result['metrics']['wave_sha256']
            fp = result['fingerprints']
            assert len(fp['BEFORE']) == 2842 and fp['BEFORE'] == fp['AFTER']
            vectors.append(fp['BEFORE'])
            rows = [list(map(float, line.split())) for line in (root/'wave.tsv').read_text().splitlines()[1:] if line.strip()]
            assert len(rows) == result['metrics']['rows']
            assert all(len(row) == 13 and all(map(math.isfinite, row)) for row in rows)
            assert rows[0][0] == 0 and abs(rows[-1][0]-40e-6) < 1e-15
            assert all(b[0] > a[0] for a,b in zip(rows,rows[1:]))
            charge = sum((b[0]-a[0])*(a[12]+b[12])/2 for a,b in zip(rows,rows[1:]))
            assert charge == result['metrics']['delivered_charge_C']
            assert abs(charge-contract['polarity']*contract['charge_fC']*1e-15) < 1e-18
            before = [row for row in rows if 15e-6 <= row[0] <= 19e-6]
            pre = [sum(r[i] for r in before)/len(before) for i in (1,2)]
            residual = [max(abs(r[i]-pre[i-1]) for r in rows if r[0]>=35e-6) for i in (1,2)]
            assert pre == result['metrics']['pre_VREF_V_IPTAT_A']
            assert residual == result['metrics']['return_error_VREF_V_IPTAT_A']
            assert result['metrics']['diagnostic_return_passed'] == (residual[0]<=.001 and residual[1]/abs(pre[1])<=.001)
            records.append(dict(run=name,contract=contract,contract_sha256=sha(root/'contract.json'),
                                analysis_sha256=sha(root/'analysis.json'),deck_sha256=result['deck_sha256'],
                                log_sha256=result['log_sha256'],metrics=result['metrics'],simulation_wall_s=run['wall_s']))
            deck = (root/'fixture.cir').read_text().replace(str(root), 'RESULT_DIRECTORY')
            directive = 'tran 2n 40u 0 '+str(contract['maxstep_ns'])+'n'
            # Original argparse default is integer2; explicit refinement parses float1.0.
            assert deck.count(directive+'\n') == 1
            deck = deck.replace(directive+'\n', 'tran 2n 40u 0 MAXSTEP\n')
            pair.append((contract, rows, deck))
        old, new = pair
        assert old[2] == new[2], 'Only maxstep and results path may change'
        assert {k:v for k,v in old[0].items() if k!='maxstep_ns'} == {k:v for k,v in new[0].items() if k!='maxstep_ns'}
        times = [r[0] for r in new[1]]
        differences = []
        for row in old[1]:
            j = min(max(bisect.bisect_right(times,row[0]),1),len(times)-1)
            left,right = new[1][j-1],new[1][j]
            fraction = (row[0]-left[0])/(right[0]-left[0])
            differences.append([row[0]]+[abs(row[i]-(left[i]+fraction*(right[i]-left[i]))) for i in (1,2)])
        comparisons.append(dict(case=case,
                                only_maxstep_and_output_path_changed='passed',
                                fulltrace_interpolated_max_difference_VREF_V_IPTAT_A=[max(r[i] for r in differences) for i in (1,2)],
                                settled35us_interpolated_max_difference_VREF_V_IPTAT_A=[max(r[i] for r in differences if r[0]>=35e-6) for i in (1,2)],
                                numerical_convergence_acceptance='not allocated: descriptive sensitivity only, not an exact waveform parity claim'))
    assert all(fp==vectors[0] for fp in vectors)
    result = dict(status='passed six-run provenance and characterization audit',transients=6,
                  full2842_parameter_freeze='passed',source_and_models='passed unchanged',
                  source_scope='Original586 electrical source with329historicalCext; not replacement physical CPEX.',
                  model_reliability='not run',full_chain_recovery='not run',radiation_acceptance='not applicable',
                  cases=records,timestep_comparisons=comparisons)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))


if __name__=='__main__':
    main()
