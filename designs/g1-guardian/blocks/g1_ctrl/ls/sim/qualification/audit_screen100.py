#!/usr/bin/env python3
"""Independently audit all fixed-load samples and characterize saved edge timing."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crossings(rows, column, threshold, rising):
    result = []
    for a, b in zip(rows, rows[1:]):
        crosses = a[column] < threshold <= b[column] if rising else a[column] > threshold >= b[column]
        if crosses:
            result.append(a[0] + (threshold-a[column])*(b[0]-a[0])/(b[column]-a[column]))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    qroot = a.results_root/'ls-mismatch-qualify-20260922-r1'
    q = json.loads((qroot/'qualification.json').read_text())
    assert q['status'] == 'passed' and all(q['checks'].values())
    samples, fingerprints, receipts = [], set(), []
    for size in (20, 100):
        for shard in range(3):
            root = a.results_root/f'ls-screen{size}-shard{shard}-20260922-r1'
            assessment = json.loads((root/'assessment.json').read_text())
            contract = json.loads((root/'contract.json').read_text())
            assert assessment['status'] == 'passed' and all(assessment['checks'].values())
            assert assessment['electrical_failed'] == 0
            assert contract['qualification_sha256'] == sha(qroot/'qualification.json')
            assert contract['source_sha256'] == q['source_sha256']
            assert contract['script_sha256'] == q['script_sha256']
            assert contract['temperature_order_C'] == [27,125,-40,27]
            receipts.append(dict(run=root.name, assessment_sha256=sha(root/'assessment.json'),
                                 manifest_sha256=sha(root/'manifest.json'), contract_sha256=sha(root/'contract.json')))
            for entry in json.loads((root/'manifest.json').read_text())['cases']:
                leaf = root/entry['name']
                assert json.loads((leaf/'analysis.json').read_text()) == entry
                assert entry['status'] == entry['electrical_acceptance'] == 'passed'
                fp = entry['fingerprints']['t0_before']
                assert len(fp) == 32 and all(v == fp for v in entry['fingerprints'].values())
                fingerprints.add(json.dumps(fp, sort_keys=True))
                assert sha(leaf/'fixture.cir') == entry['deck_sha256']
                assert sha(leaf/'tool.log') == entry['log_sha256']
                metrics = []
                for index, temp in enumerate((27,125,-40,27)):
                    path = leaf/f't{index}.tsv'
                    assert sha(path) == entry['waves'][str(index)]['sha256']
                    rows = [list(map(float,line.split())) for line in path.read_text().splitlines()[1:] if line.strip()]
                    assert len(rows) == entry['waves'][str(index)]['rows']
                    assert all(len(r)==8 and all(map(math.isfinite,r)) for r in rows)
                    assert rows[0][0] == 0 and abs(rows[-1][0]-900e-9)<1e-15
                    assert all(b[0]>c[0] for c,b in zip(rows,rows[1:]))
                    ir, of = crossings(rows,1,.6,True), crossings(rows,2,1.65,False)
                    iff, outr = crossings(rows,1,.6,False), crossings(rows,2,1.65,True)
                    assert all(len(v)==1 for v in (ir,of,iff,outr))
                    low = [r for r in rows if 100e-9<=r[0]<=290e-9 or 700e-9<=r[0]<=890e-9]
                    high = [r for r in rows if 400e-9<=r[0]<=590e-9]
                    low_max, high_min = max(r[2] for r in low), min(r[2] for r in high)
                    assert low_max<=.33 and high_min>=2.97
                    metrics.append(dict(temperature_C=temp, low_max_V=low_max, high_min_V=high_min,
                                        rise_delay_s=outr[0]-ir[0], fall_delay_s=of[0]-iff[0],
                                        input_width_s=iff[0]-ir[0], output_width_s=of[0]-outr[0],
                                        VDDA_peak_draw_A=max(-r[4] for r in rows),
                                        VDD_peak_draw_A=max(-r[3] for r in rows),
                                        VDDA_settled_peak_draw_A=max(-r[4] for r in low+high),
                                        VDD_settled_peak_draw_A=max(-r[3] for r in low+high)))
                assert entry['waves']['0']['sha256']==entry['waves']['3']['sha256']
                samples.append(dict(seed=entry['seed'], run=root.name, analysis_sha256=sha(leaf/'analysis.json'),
                                    simulation_wall_s=entry['wall_s'], metrics=metrics))
    assert sorted(s['seed'] for s in samples) == list(range(56101,56201))
    assert len(fingerprints) == 100
    flat = [m for s in samples for m in s['metrics']]
    names = ('low_max_V','high_min_V','rise_delay_s','fall_delay_s','input_width_s','output_width_s',
             'VDDA_peak_draw_A','VDD_peak_draw_A','VDDA_settled_peak_draw_A','VDD_settled_peak_draw_A')
    result = dict(status='passed', samples=100, completed_temperature_transients=400,
                  independent_mismatch_vectors=100, waveform_and_receipt_hashes='passed',
                  frozen_parameters_and_temperature_return='passed', fixed_load_logic='passed',
                  exactly_one_rising_and_falling_edge='passed',
                  timing_current_limit_acceptance='not run', actual_receiver_and_adverse_power_order='not run',
                  physical_measurement='not applicable', qualification_sha256=sha(qroot/'qualification.json'),
                  source_sha256=q['source_sha256'], simulation_script_sha256=q['script_sha256'],
                  audit_script_sha256=sha(Path(__file__)),
                  aggregate_simulation_wall_s=sum(s['simulation_wall_s'] for s in samples),
                  extrema={name:dict(min=min(m[name] for m in flat),max=max(m[name] for m in flat)) for name in names},
                  limitations='Simulated fixed 20 fF load and nominal 1.2/3.3 V rails; timing and currents descriptive, not allocated limits or full V16 closure.',
                  receipts=receipts, cases=samples)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('receipts','cases')},indent=2))


if __name__ == '__main__':
    main()
