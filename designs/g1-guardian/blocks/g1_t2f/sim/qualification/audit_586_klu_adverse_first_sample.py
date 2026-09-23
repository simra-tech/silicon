#!/usr/bin/env python3
"""Independent source/receipt/fullwave audit of exactly75201; no next29 release."""
import argparse
import hashlib
import json
from pathlib import Path
from run_586_klu_adverse_first_sample import HERE, ROOT, CONDITIONS, sha, bound_inputs, numerical_gate, parameter_values, header_for, calibrate
from run_586_source_control import load_wave
from run_586_nearendpoint_recovery import validate_wave
from audit_586_adverse_calibration_samples import rounded_measurement_consistency
from run_586_population_control import phase_text


def receipt_gate(state, row, entry):
    assert row['runtime'] == state and row['status'] == entry['status']
    if row['status'] == 'passed':
        assert state['status'] == 'completed' and state['returncode'] == 0 and not row['errors']
        assert not row.get('analysis_error')


def audit(implementation_path, digest):
    _, contract_path, contract, _, prep = bound_inputs(implementation_path, digest)
    run = HERE/'runs'/contract['run_id']
    result = dict(status='not run', seed=75201, corner='fast', leaves=[], numerical_completed_leaves=0,
        calibration_status='not run', implementation_sha256=digest, contract_sha256=sha(contract_path),
        next29='not run; this audit grants no population/solver release')
    if not (run/'summary.json').exists():
        return result
    parent, = json.loads((run/'summary.json').read_text())
    provenance = json.loads((run/'provenance.json').read_text())
    assert provenance['implementation_sha256'] == digest and provenance['contract_sha256'] == sha(contract_path)
    assert provenance['runtime_identity'] == contract['runtime_identity'] and provenance['solver'] == 'klu'
    assert parent['seed'] == provenance['seed'] == 75201 and parent['corner'] == provenance['corner'] == 'fast'
    assert sha(run/'runner.py') == provenance['runner_sha256'] == sha(HERE/'run_586_klu_adverse_first_sample.py')
    assert provenance['source_hashes'] == contract['source_hashes']
    assert all(sha(run/n) == v for n,v in contract['source_hashes'].items())
    assert sha(run/'population_inventory.json') == contract['inventory_sha256'] == provenance['inventory_sha256']
    assert len(parent['leaves']) <= 6
    vectors, frequencies = [], {}
    for expected_index, entry in enumerate(parent['leaves']):
        assert entry['index'] == expected_index
        label, temp, vdda, vdd, role = CONDITIONS[expected_index]
        leaf = run/('p%02d'%expected_index)
        row, = json.loads((leaf/'summary.json').read_text())
        state = json.loads((leaf/'run.json').read_text())
        assert sha(leaf/'summary.json') == entry['summary_sha256']
        assert all(row[k] == entry[k] == v for k,v in dict(index=expected_index,label=label,
            temperature_C=temp,VDDA_V=vdda,VDD_V=vdd,role=role).items())
        assert state['timeout_s'] == 600
        receipt_gate(state, row, entry)
        assert (leaf/'probe.cir').read_bytes() == (contract_path.parent/(label+'.cir')).read_bytes()
        assert sha(leaf/'probe.cir') == row['deck_sha256'] == entry['deck_sha256']
        assert all(sha(leaf/n) == v for n,v in contract['source_hashes'].items())
        record = dict(index=expected_index,label=label,status=row['status'],full_reaudit='not run; failed leaf retained',
            receipts_sha256={n:sha(leaf/n) for n in ['probe.cir','summary.json','run.json','run.log']})
        if row['status'] == 'passed':
            log = (leaf/'run.log').read_text()
            numerical_gate(state, log)
            before, after, values = parameter_values(log, prep['groups'])
            assert before == after == row['parameters_before'] == row['parameters_after']
            assert values == row['measurements'] and row['full3180_status'] == 'passed'
            blob, data = load_wave(leaf/'phase0.dat')
            vce = validate_wave(blob, data, header_for((leaf/'probe.cir').read_text()))
            assert vce == row['t2f_hbt_external_vce_max_V']
            assert len(data) == row['wave_rows'] and hashlib.sha256(blob).hexdigest() == row['waveform_sha256']
            record.update(full_reaudit='passed', frequency_printed_time_consistency=rounded_measurement_consistency(phase_text(log,0)))
            vectors.append(before)
            frequencies[label] = values['freq']
        result['leaves'].append(record)
    assert not vectors or all(v == vectors[0] for v in vectors)
    if vectors:
        assert parent['parameters_first_completed_leaf'] == vectors[0]
    complete = len(result['leaves']) == 6 and parent['status'] != 'running'
    result.update(status='passed independent evidence audit', complete=complete, original_outcome=parent['status'],
        numerical_completed_leaves=len(vectors), parameter_vector_sha256=hashlib.sha256(json.dumps(vectors[0],sort_keys=True).encode()).hexdigest() if vectors else None,
        parent_receipts_sha256={n:sha(run/n) for n in ['summary.json','provenance.json','runner.py','population_inventory.json']})
    if len(vectors) == 6:
        calibration = calibrate(frequencies)
        assert parent['full3180_across_conditions'] == 'passed'
        assert parent['calibration'] == calibration and parent['calibration_status'] == calibration['status']
        assert parent['status'] == ('passed' if calibration['status']=='passed' else 'failed original linear calibration')
        result.update(calibration_status=calibration['status'],calibration=calibration)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--implementation',type=Path,required=True)
    p.add_argument('--implementation-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args()
    assert not a.output.exists()
    try:
        result = audit(a.implementation,a.implementation_sha256)
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as error:
        result = dict(status='failed independent evidence audit',analysis_error=repr(error),seed=75201,
            scope='No omitted/replaced attempt; no solver/population release')
    result['auditor_sha256'] = sha(Path(__file__))
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(a.output,sha(a.output))
    raise SystemExit(0 if result['status']=='passed independent evidence audit' else 1)


if __name__ == '__main__':
    main()
