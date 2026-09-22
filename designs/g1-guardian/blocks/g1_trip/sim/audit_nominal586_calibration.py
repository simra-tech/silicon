#!/usr/bin/env python3
"""Audit all50 one-realization probes, exact tree and unchanged acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_bgr_calibration_tree import load_record, replay
from prepare_bgr_calibration_probe import transform
from run_bgr_substitution_transient import parameter_audit
from run_nominal_clock_probe import analyze_wave
from wave_archive import open_wave, wave_sha

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    prefix = 'joint-bgr586-recal-s71002-p'
    names = [prefix+'%02d-20260922-a' % i for i in range(50)]
    tree = replay([load_record(name) for name in names[:32]])
    assert tree['bracket_status'] == 'passed selected probes'
    previous = json.loads((SIM/'qualification/bgr586-calibration-tree-final-20260922.json').read_text())
    assert all(previous[key] == value for key, value in json.loads(json.dumps(tree)).items())
    guards = [(v, expected) for v, expected in [(.027, [False, False]), (.033, [True, False]),
              (.9*204*1.04/5300, [True, False]), (1.1*204*1.04/5300, [True, True])]]
    conditions = []
    for temp in [25, -40, 125]:
        conditions += [('guard', temp, shunt, expected, [158, 227]) for shunt, expected in guards]
    for temp in [25, -40, 125]:
        conditions += [('residual', temp, shunt, [expect, expect], [133, 151]) for shunt, expect in [(.0245, False), (.0255, True)]]
    assert tree['corrected_codes'] == {'soft': 158, 'hard': 227} and tree['fixed_residual_codes'] == {'soft': 133, 'hard': 151}
    records = []
    for index, name in enumerate(names):
        run = SIM/'qualification'/name
        prep = json.loads((run/'preparation.json').read_text())
        row, = json.loads((run/'summary.json').read_text())
        prov = json.loads((run/'provenance.json').read_text())
        assert row['probe_contract_status'] == row['solver_status'] == 'passed'
        assert prov['runtime_identity'] == prep['expected_runtime_identity'] and all(prov['input_checks'].values())
        assert all(sha(run/key) == value for key, value in prep['source_hashes'].items())
        template = SIM/'qualification'/prep['calibration_template_run']
        assert (run/'hard_+0mV.cir').read_text() == transform((template/'hard_+0mV.cir').read_text(), template.name, name, *row['codes'], row['shunt_V'], row['temperature_C'])
        assert sha(run/'hard_+0mV.cir') == prep['prepared_deck_sha256']
        baseline, = json.loads((SIM/'qualification'/prep['full_nonBGR_baseline_run']/'summary.json').read_text())
        inventory = json.loads((run/'non_bgr_inventory.json').read_text())
        params = parameter_audit((run/'run.log').read_text(), prep, inventory, baseline['ordered_parameter_groups']['NON_BGR_ALL'])
        assert params == row['parameter_audit'] and all(params['checks'].values())
        with open_wave(run/'hard_+0mV.dat') as stream:
            lines = stream.read().splitlines()
        assert len(lines[0].split()) == 18
        data = [list(map(float, line.split())) for line in lines[1:] if line.strip()]
        assert all(len(line) == 18 for line in data)
        observed = analyze_wave([line[:13] for line in data], prep['prospective_sampling'])
        assert observed == row['wave_analysis'] and observed['sampling_status'] == 'passed'
        record = {'run': name, 'seed': row['seed'], 'codes': row['codes'], 'temperature_C': row['temperature_C'],
                  'shunt_V': row['shunt_V'], 'decisions': row['decisions'], 'wall_s': row['wall_s'],
                  'numerical_parameter_wave_status': 'passed', 'summary_sha256': sha(run/'summary.json'),
                  'provenance_sha256': sha(run/'provenance.json'), 'deck_sha256': sha(run/'hard_+0mV.cir'),
                  'decoded_wave_sha256': wave_sha(run/'hard_+0mV.dat'), 'wave_rows': len(data)}
        if index >= 32:
            kind, temp, shunt, expected, codes = conditions[index-32]
            assert (row['temperature_C'], row['shunt_V'], row['codes']) == (temp, shunt, codes)
            record.update(kind=kind, expected_decisions=dict(zip(['soft', 'hard'], expected)),
                          electrical_status='passed' if row['decisions'] == dict(zip(['soft', 'hard'], expected)) else 'failed')
        else:
            record['kind'] = 'selected calibration' if name in tree['selected_path'] else 'off-path calibration'
        records.append(record)
    result = {'status': 'passed one-realization calibration/guards/residual' if all(r.get('electrical_status', 'passed') == 'passed' for r in records) else 'failed electrical check',
              'independent_physical_realizations': 1, 'attempted_probes': 50, 'numerical_parameter_wave_passes': 50,
              'calibration_selected_probes': 10, 'preserved_off_path_probes': 22, 'guards': 12, 'residual_points': 6,
              'guard_failures': sum(r.get('kind') == 'guard' and r['electrical_status'] != 'passed' for r in records),
              'residual_failures': sum(r.get('kind') == 'residual' and r['electrical_status'] != 'passed' for r in records),
              'tree': tree, 'records': records, 'total_core_seconds': sum(r['wall_s'] for r in records),
              'scope': 'Fixed oldnonBGR71002 realization, all8670 parameters retained, nominal586 reference2842nominal,5MHz/full1.02us. Independent per-channel originalbinarycalibration at25mV, frozen signedcorrection andDAC rounding/clipping; hardnominal204 inrange guards. Oldsource/fixedoldcodes/10MHz failures unchanged. Not newjointmismatch population, physicalgeometry/PEX qualification, statistical yield or adoption.'}
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['tree', 'records']}, indent=2))


if __name__ == '__main__':
    main()
