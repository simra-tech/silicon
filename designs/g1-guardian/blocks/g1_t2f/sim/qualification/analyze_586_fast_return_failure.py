#!/usr/bin/env python3
"""Read-only partial-phase audit after a terminal failed fast return control."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from prepare_586_adverse_population import HERE, ROOT, BASE, make_deck, sha
from run_586_source_control import load_wave
from run_bgr_substitution_draw_audit import read_group


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    run = HERE/'runs/t2f586-fast-population-controls-20260923-a-return'
    enabled = HERE/'runs/t2f586-fast-population-controls-20260923-a-enabled'
    row, = json.loads((run/'summary.json').read_text())
    reference, = json.loads((enabled/'summary.json').read_text())
    prep = json.loads((run/'preparation.json').read_text())
    provenance = json.loads((run/'provenance.json').read_text())
    assert row['control_status'] == 'failed' and row['runtime']['status'] != 'running'
    assert prep['seed'] == 76001 and prep['temperatures_C'] == [25, 125, -40, 25]
    assert row['runtime']['timeout_s'] == 2400 and all(provenance['input_checks'].values())
    assert provenance['runtime_identity'] == prep['runtime']
    assert (run/'probe.cir').read_text() == make_deck((BASE/'ptat_T12.5.cir').read_text(), 'fast', 76001, [25, 125, -40, 25], prep['groups'])
    assert all(sha(run/name) == value for name,value in prep['source_hashes'].items())
    assert all(sha(ROOT/name) == value for name,value in prep['live_bindings_sha256'].items())
    vector = reference['phases'][0]['parameters_before']
    raw = (run/'run.log').read_bytes()
    log = raw.decode()
    progress = [json.loads(line) for line in (run/'run.progress.jsonl').read_text().splitlines()]
    records = []
    for index, temperature in enumerate(prep['temperatures_C']):
        record = dict(index=index, temperature_C=temperature, phase_status='not run',
            before3180_status='not run', after3180_status='not run', exported_wave_status='not run',
            warnings_before_initial_transient=None, warnings_after_initial_transient=None)
        records.append(record)
        begin = 'PHASE%d_BEGIN' % index
        if begin not in log:
            continue
        phase = log.split(begin, 1)[1].split('PHASE%d_BEGIN' % (index+1), 1)[0]
        record['phase_status'] = 'completed command block' if 'PHASE%d_END' % index in phase else 'incomplete command block'
        for which in ['BEFORE', 'AFTER']:
            markers = ['P%d_%s_%s_END' % (index, tag, which) for tag in prep['groups']]
            if not all(marker in phase for marker in markers):
                continue
            values = {tag: read_group(phase, 'P%d_%s_%s' % (index, tag, which), keys) for tag,keys in prep['groups'].items()}
            assert sum(map(len, values.values())) == 3180 and values == vector
            record[which.lower()+'3180_status'] = 'passed exact enabled reference vector'
            record['parameters_'+which.lower()] = values
        if 'Initial Transient Solution' in phase:
            init, transient = phase.split('Initial Transient Solution', 1)
            record['warnings_before_initial_transient'] = len(re.findall('warning', init, re.I))
            record['warnings_after_initial_transient'] = len(re.findall('warning', transient, re.I))
        else:
            record['warnings_before_initial_transient'] = len(re.findall('warning', phase, re.I))
        for marker, suffix in [(begin, 'phase_begin'), ('P%d_T2F_BEFORE_END' % index, 'before_queries_end')]:
            if marker not in log:
                continue
            offset = raw.index(marker.encode())+len(marker.encode())
            matches = [(i,p) for i,p in enumerate(progress) if p['log_bytes'] >= offset]
            if matches:
                i, point = matches[0]
                record[suffix+'_monitor_wall_bracket_s'] = [progress[max(i-1,0)]['wall_s'], point['wall_s']]
        wave = run/prep['outputs'][index]
        if wave.exists() or wave.with_name(wave.name+'.gz').exists() or wave.with_name(wave.name+'.xz').exists():
            blob, data = load_wave(wave)
            assert data.ndim == 2 and data.shape[1] == 13 and np.isfinite(data).all()
            assert abs(data[-1,0]-32e-6) < 1e-12 and np.all(np.diff(data[:,0]) > 0)
            vce = float(max(np.abs(data[:,i]-data[:,j]).max() for i,j in [(7,8),(9,8),(10,11),(12,11)]))
            record.update(exported_wave_status='passed finite full32us observation', wave_rows=len(data),
                waveform_sha256=hashlib.sha256(blob).hexdigest(), hbt_external_vce_max_V=vce,
                hbt_vce_status='passed' if vce <= 1.6 else 'failed')
            if index == 0:
                reference_blob, reference_data = load_wave(enabled/'phase0.dat')
                record['enabled_room_wave_comparison'] = dict(decoded_bytes=blob == reference_blob,
                    numeric_rows=bool(np.array_equal(data, reference_data)),
                    time_grid=data.shape == reference_data.shape and bool(np.array_equal(data[:,0],reference_data[:,0])))
    result = dict(status='passed read-only partial-phase audit; required full return remains FAILED',
        original_return_status=row['control_status'], original_runtime=row['runtime'], seed=76001,
        errors=row['errors'], records=records, source_runtime_deck_bindings='passed',
        completed_command_phases=sum(r['phase_status'] == 'completed command block' for r in records),
        full_four_phase_return_status='failed original control; no exact-return or full-temperature qualification claim',
        receipts_sha256={name: sha(run/name) for name in ['summary.json','preparation.json','provenance.json','probe.cir','run.log','run.progress.jsonl']},
        enabled_reference_summary_sha256=sha(enabled/'summary.json'), analyzer_sha256=sha(Path(__file__)),
        scope='Read-only audit of actually completed queries/exported phases only. Missing AFTER/fullwave/return phases remain notrun. Monitor brackets are host-log-byte sampling bounds, not exact simulator timestamps or accepted integration steps. OP/init warnings do not establish model validity. No timeout extension, source/model/solver change, replacementseed or fast30release.')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], phases=[{k:v for k,v in r.items() if not k.startswith('parameters_')} for r in records],
        output_sha256=sha(args.output)), indent=2))


if __name__ == '__main__':
    main()
