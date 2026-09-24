"""Read-only, receipt-bound early-decision comparison; no new electrical gate."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean

SIM = Path(__file__).resolve().parent
Q = SIM / 'qualification'
DELAYS = [-1, -.2, 0, .05, .1, .2, .3, .5, .75, 1, 2, 5, 20]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(wave):
    assert wave['sampling_status'] == 'passed'
    edges = wave['hard_early_evaluation']
    assert len(edges) == 5
    assert all([s['delay_after_measured_edge_ns'] for s in e['samples']] == DELAYS for e in edges)
    result = []
    for i, delay in enumerate(DELAYS):
        samples = [e['samples'][i] for e in edges[-3:]]
        row = dict(delay_ns=delay)
        for key in ['actual_hard_clock_V', 'hard_differential_V', 'hard_output_V']:
            values = [s[key] for s in samples]
            row[key] = dict(mean=mean(values), min=min(values), max=max(values), cycles=values)
        nodes = [s['hard_frontend_xp_xq_xn_yn_V'] for s in samples]
        row['frontend_mean_V'] = {name: mean(n[j] for n in nodes) for j, name in enumerate(['xp', 'xq', 'xn', 'yn'])}
        row['frontend_cycles_V'] = nodes
        result.append(row)
    hard = wave['comparators']['hard']
    assert hard['sampling_policies_agree']
    return dict(hard=hard, soft=wave['comparators']['soft'], early_last_three=result,
                first_two_cycles=edges[:2], actual_edges_s=wave['actual_clock_rising_crossings_s'])


def original(parent, index):
    p = Q / parent
    result = json.loads((p / 'summary.json').read_text())
    result = result[0] if isinstance(result, list) else result
    entry = result['probes'][index]
    leaf = Q / entry['run']
    assert entry['status'] == 'passed'
    assert sha(leaf / 'summary.json') == entry['summary_sha256']
    assert sha(leaf / 'probe.cir') == entry['deck_sha256']
    state = json.loads((leaf / 'run.json').read_text())
    assert state['status'] == 'completed' and state['returncode'] == 0
    full = json.loads((leaf / 'summary.json').read_text())
    return dict(run=entry['run'], role='original', codes=entry['codes'], shunt_V=entry['shunt_V'],
                temperature_C=entry['temperature_C'], condition=entry.get('condition'),
                expected_decisions=entry.get('expected_decisions'), decisions=entry['decisions'],
                source_hashes=result['source_hashes'], observation=extract(full['wave_analysis']),
                hashes={n:sha(leaf/n) for n in ['summary.json', 'probe.cir', 'run.json']},
                decoded_wave_sha256=entry['decoded_wave_sha256'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    selected={73023:list(range(10))+[22,23,26,27], 73073:list(range(10))+[22,23,26,27],
              78101:list(range(10))+list(range(50,64))}
    rows=[]
    for seed, indexes in selected.items():
        parent=('joint586-fast-nodeset-calibration-s%d-20260923-a' if seed==78101 else 'joint586-calibration-s%d-20260922-a')%seed
        rows.extend(original(parent,index) for index in indexes)
    execution=Q/'joint586-c45rz62-knownfailures-execution-20260923-a.json'
    packet=json.loads(execution.read_text())
    for case in packet['controls']:
        leaf=Q/case['run_id']; prep=json.loads((leaf/'preparation.json').read_text())
        assert sha(leaf/'preparation.json')==case['preparation_sha256']
        full=json.loads((leaf/'summary.json').read_text()); state=json.loads((leaf/'run.json').read_text())
        assert full['numerical_status']=='passed' and state['status']=='completed' and state['returncode']==0
        rows.append(dict(run=case['run_id'], role='candidate', original_run=prep['original_run'],
            codes=prep['codes'], shunt_V=prep['shunt_V'], condition=prep.get('condition'),
            decisions=full['observed_decisions'], residual_status=full['original_frozen_code_residual_status'],
            observation=extract(full['wave_analysis']), hashes={n:sha(leaf/n) for n in ['summary.json','run.json','probe.cir','sense.spice']},
            exact_old_wave_bytes=full['exact_old_wave_bytes']))
    paired=[]
    for row in rows:
        if row['role']!='candidate':continue
        old,=[r for r in rows if r['run']==row['original_run']]
        paired.append(dict(candidate=row['run'], original=old['run'], same_decisions=row['decisions']==old['decisions'],
            delta_early_mean=[dict(delay_ns=a['delay_ns'], **{k:a[k]['mean']-b[k]['mean'] for k in ['hard_differential_V','hard_output_V','actual_hard_clock_V']})
                for a,b in zip(row['observation']['early_last_three'],old['observation']['early_last_three'])]))
    result=dict(status='completed saved-observation diagnostic, not causal isolation', records=rows, paired=paired,
        execution_sha256=sha(execution), analyzer_sha256=sha(Path(__file__)),
        comparator_source_sha256=sha(SIM/'netlist/g1_cmp.spice'),
        scope='Original summary observations are receipt-bound; no raw-wave reanalysis or simulation. Last three actual edges and original20ns/0.6V sampling unchanged. Early values are interpolated observations, not a universal input offset or metastability criterion. No population/source adoption or threshold relaxation.',
        isolated_reset_clock_or_device_remedy='not run')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(args.output.name,sha(args.output))


if __name__=='__main__':main()
