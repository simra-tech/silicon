#!/usr/bin/env python3
"""Read-only failed-draw inventory and reported progress; no waveform inference."""
import argparse
import json
from pathlib import Path
import re
from prepare_586_adverse_population import HERE, ROOT, BASE, make_deck, sha
from run_bgr_substitution_draw_audit import read_group
from analyze_586_population import changed_primitives


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    run = HERE/'runs/t2f586-fast-population-controls-20260923-a-changed'
    enabled = HERE/'runs/t2f586-fast-population-controls-20260923-a-enabled'
    row, = json.loads((run/'summary.json').read_text())
    reference, = json.loads((enabled/'summary.json').read_text())
    prep = json.loads((run/'preparation.json').read_text())
    provenance = json.loads((run/'provenance.json').read_text())
    assert row['control_status'] == 'failed' and row['runtime']['status'] == 'timeout'
    assert row['runtime']['timeout_s'] == 600 and not row['errors']
    assert all(provenance['input_checks'].values())
    assert (run/'probe.cir').read_text() == make_deck((BASE/'ptat_T12.5.cir').read_text(), 'fast', 76002, [25], prep['groups'])
    assert all(sha(run/name) == value for name, value in prep['source_hashes'].items())
    assert all(sha(ROOT/name) == value for name, value in prep['live_bindings_sha256'].items())
    log = (run/'run.log').read_text()
    before = {tag: read_group(log, 'P0_'+tag+'_BEFORE', keys) for tag, keys in prep['groups'].items()}
    assert sum(map(len, before.values())) == 3180
    inventory = json.loads((run/'population_inventory.json').read_text())
    variation = changed_primitives(inventory, reference['phases'][0]['parameters_before'], before)
    assert len(variation) == 1129
    initial, transient = log.split('Initial Transient Solution', 1)
    progress = [json.loads(line) for line in (run/'run.progress.jsonl').read_text().splitlines()]
    raw = (run/'run.log').read_bytes()
    command_timing = []
    for marker in ['P0_BGR_BEFORE_BEGIN', 'P0_BGR_BEFORE_END', 'P0_T2F_BEFORE_END', 'Initial Transient Solution']:
        offset = raw.index(marker.encode())+len(marker.encode())
        index = next(i for i, r in enumerate(progress) if r['log_bytes'] >= offset)
        command_timing.append(dict(marker=marker, raw_log_byte_offset=offset,
            monitor_wall_bracket_s=[progress[max(index-1, 0)]['wall_s'], progress[index]['wall_s']],
            scope='First monitor whose cumulative raw log bytes include marker; sampling bracket, not exact simulator timestamp'))
    milestones = []
    for time_s in [1e-6, 1.01e-6, 1.5e-6, 2e-6, 2.1e-6, 2.2e-6, 2.25e-6, 2.27e-6, 2.275e-6]:
        reached = [r for r in progress if r.get('last_reported_sim_time_s', -1) >= time_s]
        first = reached[0] if reached else None
        milestones.append(dict(target_simulation_time_s=time_s, status='reported reached' if first else 'not reached',
            first_monitor_wall_s=first['wall_s'] if first else None,
            first_reported_simulation_time_s=first.get('last_reported_sim_time_s') if first else None))
    warnings = dict(before_initial_transient=len(re.findall(r'warning', initial, re.I)),
                    after_initial_transient=len(re.findall(r'warning', transient, re.I)))
    nodes = {}
    for node in ['vdd', 'vdd12', 'en', 'vref', 'fout', 'xt2f.cap1', 'xt2f.cap2',
                 'xt2f.tail1', 'xt2f.tail2', 'xt2f.ca1', 'xt2f.ca2', 'xt2f.cb1', 'xt2f.cb2']:
        matches = re.findall(r'(?m)^'+re.escape(node)+r'\s+([-+0-9.eE]+)\s*$', transient)
        assert len(matches) == 1
        nodes[node] = float(matches[0])
    result = dict(status='passed read-only input/BEFORE audit; original numerical qualification FAILED',
        run=run.name, seed=76002, original_status=row['control_status'], original_runtime=row['runtime'],
        full3180_before_status='passed complete declared query inventory', full3180_before=before,
        full3180_after_status='not run to completion', waveform_status='not run; no exported wave',
        frequency_and_accuracy_status='not run to completion', warnings=warnings, errors=row['errors'],
        changed_seed_variation=dict(status='passed' if all(r['status'] == 'passed' for r in variation) else 'failed',
            primitives=1129, changed=sum(r['status'] == 'passed' for r in variation),
            groups={g: dict(total=sum(r['group'] == g for r in variation),
                changed=sum(r['group'] == g and r['status'] == 'passed' for r in variation)) for g in ['BGR', 'T2F']}),
        initial_transient_printed_nodes=nodes, progress_milestones=milestones, command_progress_timing=command_timing,
        analyzer_sha256=sha(Path(__file__)),
        receipts_sha256={n: sha(run/n) for n in ['summary.json', 'preparation.json', 'provenance.json', 'probe.cir', 'run.log', 'run.progress.jsonl', 'population_inventory.json']},
        enabled_reference_summary_sha256=sha(enabled/'summary.json'),
        interpretation='Reported progress is sampled host telemetry, NOT a sequence of accepted integration timesteps or a waveform. All warnings occurred in OP/init if after_initial_transient=0; this does not prove model validity or identify cause. Enable ramp ends1.01us, but slowdown nearlateroscillatoryoperation cannot be assigned to a particular node without a separately qualified waveform. No timeout extension, replacementseed, tolerancechange or fast30release.')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['full3180_before','receipts_sha256']}, indent=2))


if __name__ == '__main__':
    main()
