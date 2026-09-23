#!/usr/bin/env python3
"""Exactly six original75201 conditions with separately qualified KLU; no next29."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from prepare_586_klu_adverse_first_sample import HERE, ROOT, CONDITIONS, reference_run, sample_deck, klu_deck, sha
from analyze_586_adverse_controls import calibrate
from run_586_population_control import phase_text, nominal_gate
from run_586_source_control import load_wave
from run_586_nearendpoint_recovery import validate_wave
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory
from result_directory import allocate_run
from wave_archive import archive_new_wave


def errors_in(log):
    return [l for l in log.splitlines() if re.search(
        r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', l, re.I)]


def numerical_gate(state, log):
    assert state['status'] == 'completed' and state['returncode'] == 0 and not errors_in(log)
    assert 'Using KLU as Direct Linear Solver' in log and 'Using SPARSE 1.3 as Direct Linear Solver' not in log
    assert 'PHASE0_END' in log


def parameter_values(log, groups):
    phase = phase_text(log, 0)
    before = {tag:read_group(phase, 'P0_'+tag+'_BEFORE', keys) for tag,keys in groups.items()}
    after = {tag:read_group(phase, 'P0_'+tag+'_AFTER', keys) for tag,keys in groups.items()}
    assert sum(map(len, before.values())) == 3180 and before == after
    values = {k:float(v) for k,v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)', phase)}
    assert all(k in values and math.isfinite(values[k]) for k in ['freq','t_a','t_b','t_half_a','fout_hi','fout_lo'])
    assert values['freq'] > 0 and values['t_b'] > values['t_a']
    return before, after, values


def header_for(deck):
    line, = [l for l in deck.splitlines() if l.startswith('wrdata ')]
    header = ['time']+line.split()[2:]
    assert len(header) == 13
    return header


def bound_inputs(path, digest):
    assert sha(path) == digest
    implementation = json.loads(path.read_text())
    assert all(sha(ROOT/n) == v for n,v in implementation['bindings_sha256'].items())
    contract_path = ROOT/implementation['contract']
    assert sha(contract_path) == implementation['contract_sha256']
    contract = json.loads(contract_path.read_text())
    assert contract['corner'] == 'fast' and contract['seed'] == 75201 and len(contract['cases']) == 6
    assert all(sha(ROOT/n) == v for n,v in contract['live_bindings_sha256'].items())
    audit = json.loads((HERE/'t2f586-klu-fast-own6-qualification-20260923.json').read_text())
    assert audit['status'] == 'passed six-control same-KLU qualification'
    assert all(audit['comparisons']['full3180'].values())
    assert all(all(v.values()) for v in audit['comparisons']['waveforms'].values())
    assert len(audit['variation']) == 1129 and all(v['status'] == 'passed' for v in audit['variation'])
    own = json.loads((HERE/'t2f586-klu-own6-preparation-20260923-a.json').read_text())
    for case in [c for c in own['cases'] if c['corner'] == 'fast']:
        row = audit['controls'][case['label']]
        assert row['status'] == 'passed independent finite/input/full3180 evidence'
        assert all(sha(HERE/'runs'/case['run_id']/n) == v for n,v in row['receipts_sha256'].items())
    nom = json.loads((HERE/'t2f586-klu-nominal-references-20260923-b.json').read_text())
    case, = [c for c in nom['cases'] if c['corner'] == 'fast']
    assert all(sha(HERE/'runs'/case['run_id']/n) == v for n,v in audit['nominal_reference']['receipts_sha256'].items())
    reference = reference_run('fast')
    prep = json.loads((reference/'preparation.json').read_text())
    assert all(sha(reference/n) == v for n,v in contract['source_hashes'].items())
    inventory = json.loads((reference/'population_inventory.json').read_text())
    assert sha(reference/'population_inventory.json') == contract['inventory_sha256']
    assert inventory['parameter_count'] == 3180 and inventory['primitive_count'] == 1129
    for case in contract['cases']:
        sparse = sample_deck((reference/'probe.cir').read_text(), 'fast', 75201, case['label'])
        expected = klu_deck(sparse)
        assert hashlib.sha256(sparse.encode()).hexdigest() == case['sparse_generated_sha256']
        assert (contract_path.parent/(case['label']+'.cir')).read_text() == expected
        assert sha(contract_path.parent/(case['label']+'.cir')) == case['klu_deck_sha256']
    return implementation, contract_path, contract, reference, prep


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--implementation', type=Path, required=True)
    p.add_argument('--implementation-sha256', required=True)
    p.add_argument('--image-id', required=True)
    a = p.parse_args()
    _, contract_path, contract, reference, prep = bound_inputs(a.implementation, a.implementation_sha256)
    nominal_gate(ROOT/prep['required_nominal_analysis'])
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = dict(image_id=a.image_id, pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice=subprocess.check_output(['ngspice','--version'], universal_newlines=True),
        models_sha256={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice/models').glob('*.lib'))},
        osdi_sha256={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice/osdi').glob('*.osdi'))})
    assert runtime == contract['runtime_identity']
    out = allocate_run(HERE.parent, contract['run_id'], relative_parent='qualification/runs')
    for name in ['bgr.spice','t2f.spice','.spiceinit','population_inventory.json']:
        (out/name).write_bytes((reference/name).read_bytes())
    (out/'runner.py').write_text(Path(__file__).read_text())
    provenance = dict(arguments=sys.argv[1:], implementation_sha256=a.implementation_sha256,
        contract_sha256=sha(contract_path), runtime_identity=runtime, solver='klu', seed=75201, corner='fast',
        source_hashes=contract['source_hashes'], inventory_sha256=contract['inventory_sha256'],
        runner_sha256=sha(Path(__file__)), conditions=CONDITIONS, watchdog_per_leaf_s=600,
        scope='ONE original75201 six-condition KLU diagnostic. No next29, no replacement/overwrite of original SPARSE evidence or active typical population.')
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    result = dict(seed=75201, corner='fast', status='running', leaves=[], full3180_across_conditions='not run', calibration_status='not run')
    first = None
    for index, condition in enumerate(CONDITIONS):
        label, temp, vdda, vdd, role = condition
        leaf = out/('p%02d'%index)
        leaf.mkdir()
        for name in ['bgr.spice','t2f.spice','.spiceinit']:
            (leaf/name).write_bytes((out/name).read_bytes())
        deck = (contract_path.parent/(label+'.cir')).read_text()
        (leaf/'probe.cir').write_text(deck)
        with (leaf/'run.log').open('x') as stream:
            state = run_bounded(['ngspice','-b','probe.cir'], stream, leaf/'run.json', 600, cwd=leaf, interval_s=1)
        log = (leaf/'run.log').read_text()
        row = dict(index=index, label=label, temperature_C=temp, VDDA_V=vdda, VDD_V=vdd, role=role,
            status='failed', runtime=state, errors=errors_in(log), full3180_status='not run',
            warnings=warning_inventory(log), deck_sha256=sha(leaf/'probe.cir'))
        try:
            numerical_gate(state, log)
            before, after, values = parameter_values(log, prep['groups'])
            row.update(parameters_before=before, parameters_after=after)
            if first is None:
                first = before
            assert before == first
            row['full3180_status'] = 'passed'
            blob, data = load_wave(leaf/'phase0.dat')
            vce = validate_wave(blob, data, header_for(deck))
            row.update(status='passed', waveform_sha256=hashlib.sha256(blob).hexdigest(), wave_rows=len(data),
                measurements=values, t2f_hbt_external_vce_max_V=vce)
        except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
            row['analysis_error'] = repr(error)
        (leaf/'summary.json').write_text(json.dumps([row], indent=2)+'\n')
        if (leaf/'phase0.dat').exists():
            archive_new_wave(leaf/'phase0.dat')
        result['leaves'].append({k:v for k,v in row.items() if k not in ['parameters_before','parameters_after','warnings']})
        result['leaves'][-1]['summary_sha256'] = sha(leaf/'summary.json')
        result['parameters_first_completed_leaf'] = first
        (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    result['status'] = 'failed; complete attempted six-condition coverage'
    if all(r['status'] == r['full3180_status'] == 'passed' for r in result['leaves']):
        result['full3180_across_conditions'] = 'passed'
        try:
            result['calibration'] = calibrate({r['label']:r['measurements']['freq'] for r in result['leaves']})
            result['calibration_status'] = result['calibration']['status']
            result['status'] = 'passed' if result['calibration_status'] == 'passed' else 'failed original linear calibration'
        except (AssertionError, ValueError, KeyError) as error:
            result['calibration_analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['leaves','parameters_first_completed_leaf']}, indent=2))
    raise SystemExit(0 if result['status']=='passed' else 1)


if __name__ == '__main__':
    main()
