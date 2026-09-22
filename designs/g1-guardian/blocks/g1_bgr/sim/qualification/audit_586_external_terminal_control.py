#!/usr/bin/env python3
"""Independent saved-data audit after original runner JSON serialization failure."""
import argparse
import json
from pathlib import Path
import re
import numpy as np
from run_586_pvt import sha
from audit_586_raw_terminal_mapping import candidate_mos
from probe_586_external_terminals import instrument

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run = HERE/'runs/bgr586-external22port-control-20260922-a'
    base = HERE/'runs/bgr_one_draw_20260922_r1'
    ref = base/'disabled'
    prov = json.loads((run/'provenance.json').read_text())
    state = json.loads((run/'run.json').read_text())
    assert state['status'] == 'completed' and state['returncode'] == 0
    assert sha(run/'runner.py') == prov['runner_sha256']
    source, records = instrument((ref/'pex_nominal.spice').read_text())
    assert source == (run/'pex_nominal.spice').read_text() and records == prov['source_changes']
    assert sha(run/'pex_nominal.spice') == prov['source_sha256'] and sha(run/'nominal.cir') == prov['deck_sha256']
    qm = json.loads((base/'manifest.json').read_text())
    assert sha(base/'manifest.json') == prov['reference_manifest_sha256'] and qm['runtime'] == prov['runtime']
    assert qm['source_sha256'] == prov['canonical_source_sha256'] == sha(ref/'pex_nominal.spice')
    assert (run/'.spiceinit').read_bytes() == (ref/'.spiceinit').read_bytes()
    # Explicitly preserve the observed failed analysis, not a replacement PASS.
    failure = run/'summary.json'
    if not failure.exists():
        failure.write_text(json.dumps([{'status': 'failed original runner analysis serialization', 'numerical_status': state['status'], 'runtime': state,
                                      'error': 'TypeError: Object of type bool is not JSON serializable (NumPy bool orientation field).',
                                      'scope': 'Original completed simulation retained without rerun; separate read-only analysis.json does not rename this failed runner result.'}], indent=2)+'\n')
    failed, = json.loads(failure.read_text())
    assert failed['status'] == 'failed original runner analysis serialization'
    log = (run/'run.log').read_text()
    assert not re.search(r'^Error|no such vector|no such parameter|analysis aborted|Timestep too small', log, re.M)
    section, = re.findall(r'^EXTERNAL_PORT_QUERY_BEGIN\n(.*?)^EXTERNAL_PORT_QUERY_END$', log, re.M | re.S)
    fields = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', section, re.M)
    assert [k for k, v in fields] == sum([r['queries'] for r in records], [])
    assert all(np.isfinite(float(v)) for k, v in fields)
    params = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', log.replace(section, ''), re.M)
    oldparams = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', (ref/'run.log').read_text(), re.M)
    assert params == oldparams and [k for k, v in params] == qm['parameters']*2 and params[:2842] == params[2842:]
    data = np.loadtxt(str(run/'external_ports.dat'), skiprows=1, ndmin=2)
    assert data.shape == (1, 45) and np.isfinite(data).all()
    values = {k: float(v) for k, v in fields}
    observed, voltages = data[0, 1:23], data[0, 23:]
    result, offset = [], 0
    for row in records:
        n = len(row['branches'])
        measured, volts = observed[offset:offset+n], voltages[offset:offset+n]
        q = [values[k] for k in row['queries']]
        if row['source_name'].startswith('XM'):
            predicted, swapped = candidate_mos(q, volts[0], volts[2])
            swapped = bool(swapped)
        elif row['source_name'].startswith('XQ'):
            predicted, swapped = q[:3]+[-q[4]-q[5]], None
        else:
            predicted, swapped = [-q[0], q[0], 0.0], None
        delta = measured-np.array(predicted)
        result.append(dict(source_name=row['source_name'], model=row['model'], terminals=row['terminals'],
                           measured_external_current_A=dict(zip(row['terminals'], measured.tolist())), monitor_voltage_V=dict(zip(row['terminals'], volts.tolist())),
                           model_field_prediction_A=dict(zip(row['terminals'], predicted)), maximum_abs_mapping_delta_A=float(np.abs(delta).max()),
                           signed_measured_port_current_sum_A=float(measured.sum()), internal_drain_source_swapped=swapped))
        offset += n
    assert all(r['maximum_abs_mapping_delta_A'] <= prov['prospective_mapping_maximum_abs_delta_A'] for r in result)
    oldwave, newwave = [np.loadtxt(str(p/'nominal.dat'), skiprows=1) for p in [ref, run]]
    assert oldwave.shape == newwave.shape == (34, 12) and np.isfinite(newwave).all()
    audit = {'status': 'passed independent nominal22port mapping audit; original runner failure retained',
             'original_failure_sha256': sha(failure), 'runtime': state, 'full2842_before_after_original_exact': True,
             'canonical_source_restoration_exact': True, 'model_runtime_identity_exact': True,
             'original_dc_bytes_exact': (run/'nominal.dat').read_bytes() == (ref/'nominal.dat').read_bytes(),
             'original_dc_numeric_rows_exact': bool(np.array_equal(oldwave, newwave)), 'original_dc_maximum_abs_column_deltas': np.abs(newwave-oldwave).max(axis=0).tolist(),
             'prospective_per_port_bound_A': prov['prospective_mapping_maximum_abs_delta_A'], 'maximum_abs_mapping_delta_A': max(r['maximum_abs_mapping_delta_A'] for r in result),
             'representative_device_mappings': result,
             'rshunt_basis': prov['effective_settings_basis'],
             'receipts_sha256': {name: sha(run/name) for name in ['provenance.json', 'nominal.cir', 'pex_nominal.spice', '.spiceinit', 'runner.py', 'run.log', 'run.json', 'external_ports.dat', 'nominal.dat']},
             'scope': 'Saved-data analysis only, no simulator rerun. Forward/reverseNMOS, PMOSpolarity, rhigh/rppd end+measuredsubstrate and HBTexternalBN branch mapping checked at nominal27C/oneOP. Original waveform exact failures separate; no alltemperature/transient physicalIR or lifetime qualification. Full1036field-ledger application is inference from common model wrappers, not1036 individually instrumented ports.'}
    with args.output.open('x') as stream:
        json.dump(audit, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in audit.items() if k not in ['representative_device_mappings', 'receipts_sha256']}, indent=2))


if __name__ == '__main__':
    main()
