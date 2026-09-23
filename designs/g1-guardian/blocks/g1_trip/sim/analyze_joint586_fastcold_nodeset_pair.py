#!/usr/bin/env python3
"""Independent pair audit; exact failures remain separate from completion."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import numpy as np
from prepare_joint586_fastcold_nodeset_transients import SIM, ROOT, ORIGINAL, sha, transform
from run_joint586_fastcold_nodeset_transients import numerical_gate, validate_header
from run_joint586_fastcold_nodeset_transients_r2 import error_lines
from run_joint586_transients import phase_parameters
from audit_joint586_adverse_transients import wave_check
from wave_archive import open_wave


def compare_waves(first, second):
    headers = [b.splitlines()[0].decode().split() for b in [first, second]]
    assert headers[0] == headers[1] and len(headers[0]) == 19
    x, y = [np.array([list(map(float, l.split())) for l in b.splitlines()[1:] if l.strip()]) for b in [first, second]]
    assert all(a.shape[1] == 19 and np.isfinite(a).all() and np.all(np.diff(a[:, 0]) >= 0) for a in [x, y])
    result = dict(decoded_bytes_exact=first == second, numeric_rows_exact=bool(np.array_equal(x, y)),
        time_grid_exact=bool(np.array_equal(x[:, 0], y[:, 0])),
        scope='Exact failures remain failed comparisons. Union-grid interpolation is descriptive, not a numerical acceptance bound or rejected-step inference.')
    # Do not silently choose one of unequal duplicate-time values.
    if any(np.any(np.diff(a[:, 0]) == 0) for a in [x, y]):
        result['uniongrid_voltage_comparison'] = 'not run: duplicate saved time requires explicit discontinuity treatment'
    else:
        grid = np.unique(np.concatenate([x[:, 0], y[:, 0]]))
        assert x[0, 0] == y[0, 0] and x[-1, 0] == y[-1, 0]
        result['uniongrid_voltage_comparison'] = {
            name: dict(max_abs_V=float(np.max(np.abs(delta))), rms_V=float(np.sqrt(np.mean(delta**2))))
            for i, name in enumerate(headers[0][1:], 1)
            for delta in [np.interp(grid, y[:, 0], y[:, i])-np.interp(grid, x[:, 0], x[:, i])]}
        result['rms_scope'] = 'Unweighted union-output-grid RMS, not time-weighted RMS.'
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract', type=Path, required=True)
    p.add_argument('--contract-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and sha(a.contract) == a.contract_sha256
    packet = json.loads(a.contract.read_text())
    assert all(sha(ROOT/n) == v for n, v in packet['bindings_sha256'].items())
    prep = packet['original_preparation']
    results, blobs, analyses = {}, {}, {}
    for case in packet['cases']:
        solver = case['solver']
        out = SIM/'qualification'/case['run']
        result = dict(status='not run', run=case['run'])
        results[solver] = result
        if not (out/'summary.json').exists():
            continue
        try:
            row, = json.loads((out/'summary.json').read_text())
            state = json.loads((out/'run.json').read_text())
            log = (out/'run.log').read_text()
            result.update(original_summary_status=row['status'], runtime=state)
            assert row['runtime'] == state
            numerical_gate(state, error_lines(log), log, solver)
            provenance = json.loads((out/'provenance.json').read_text())
            assert provenance['contract_sha256'] == a.contract_sha256
            assert provenance['runtime_identity'] == dict(prep['expected_runtime_identity'], solver=solver)
            assert all(provenance['input_checks'].values())
            assert sha(out/'error_inventory_adapter.py') == packet['adapter_sha256']
            assert sha(out/'runner.py') == sha(SIM/'run_joint586_fastcold_nodeset_transients.py')
            assert all(sha(out/n) == sha(ORIGINAL/n) == v for n, v in packet['source_hashes'].items())
            deck = (out/'population_transient.cir').read_text()
            expected, _ = transform((ORIGINAL/'population_transient.cir').read_text(), case['run'], solver, packet['guesses_original_printed_strings'])
            assert deck == expected and sha(out/'population_transient.cir') == case['deck_sha256']
            section, = re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$', log, re.M|re.S)
            parameters = phase_parameters(section, prep['groups'], prep['expected_vector'])
            with open_wave(out/'phase0.dat', 'rb') as stream:
                blob = stream.read()
            validate_header(blob, deck)
            data, analysis = wave_check(blob, 19, prep['prospective_sampling'])
            assert parameters == row['parameters'] and analysis == row['wave_analysis']
            assert hashlib.sha256(blob).hexdigest() == row['decoded_wave_sha256']
            assert max(abs((r[17]+r[18])/2-prep['condition'][4]) for r in data) < 1e-12
            assert max(abs(r[17]-r[18]-.025) for r in data) < 1e-12
            result.update(status='passed independently verified finite fullparameter diagnostic',
                parameter_count=11512, legacy_count=27, wave_rows=len(data),
                sampling_status=analysis['sampling_status'], decisions=row['decisions'],
                receipts_sha256={n:sha(out/n) for n in ['summary.json', 'run.json', 'run.log', 'provenance.json', 'runner.py', 'error_inventory_adapter.py']})
            blobs[solver], analyses[solver] = blob, analysis
        except (AssertionError, ValueError, KeyError, IndexError, OSError) as error:
            result.update(status='failed independent finite/fullparameter diagnostic', analysis_error=repr(error))
    pair = 'not run: both finite fully audited completed waves required'
    if set(blobs) == {'sparse', 'klu'}:
        pair = compare_waves(blobs['sparse'], blobs['klu'])
        pair['decisions_exact'] = results['sparse']['decisions'] == results['klu']['decisions']
        pair['actual_clock_events'] = {
            name: dict(sparse_s=x, klu_s=analyses['klu']['actual_clock_rising_crossings_s'][name],
                count_exact=len(x) == len(analyses['klu']['actual_clock_rising_crossings_s'][name]),
                index_paired_delta_s=[v-u for u,v in zip(x, analyses['klu']['actual_clock_rising_crossings_s'][name])])
            for name,x in analyses['sparse']['actual_clock_rising_crossings_s'].items()}
    output = dict(status='independent pair observations; no fixture/solver/population adoption',
        contract_sha256=a.contract_sha256, results=results, pair_comparison=pair,
        analyzer_sha256=sha(Path(__file__)), original_failures='retained; no completed original fullwave comparison',
        scope=packet['scope'])
    a.output.write_text(json.dumps(output, indent=2)+'\n')
    print(a.output, sha(a.output))


if __name__ == '__main__':
    main()
