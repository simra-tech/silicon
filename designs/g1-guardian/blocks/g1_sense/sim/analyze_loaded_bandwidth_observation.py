#!/usr/bin/env python3
"""Describe source-defined stage responses; no fitted poles or physical-RC claim."""
import argparse
import json
from pathlib import Path
import numpy as np
from run_loaded_noise_audit import sha, table


def decomposition(output, driver, error):
    assert np.isfinite(output).all() and np.isfinite(driver).all()
    assert np.isfinite(error).all() and np.all(driver != 0) and np.all(error != 0)
    stages = dict(output_over_out1=output/driver,
                  out1_over_input_error=driver/error, input_error=error)
    rebuilt = np.prod(list(stages.values()), axis=0)
    residual = abs(rebuilt-output)/np.maximum(abs(output), np.finfo(float).tiny)
    assert np.max(residual) < 1e-12
    return stages, float(np.max(residual))


def tests():
    f = np.geomspace(1, 1e7, 101)
    first = 20/(1+1j*f/1e5)
    second = -3/(1+1j*f/1e6)
    error = .01*(1+1j*f/1e4)
    stages, residual = decomposition(first*second*error, first*error, error)
    assert np.max(abs(stages['output_over_out1']/second-1)) < 1e-12
    assert np.max(abs(stages['out1_over_input_error']/first-1)) < 1e-12
    for bad in [np.zeros_like(error), np.full_like(error, complex('nan'))]:
        try:
            decomposition(first, second, bad)
        except AssertionError:
            pass
        else:
            raise AssertionError('Invalid denominator accepted')
    return dict(status='passed', analytic_stage_relative_residual=residual,
                zero_and_nonfinite_denominator_rejected=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observation', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--test-only', action='store_true')
    args = parser.parse_args()
    control = tests()
    if args.test_only:
        print(json.dumps(control)); return
    assert args.observation and args.output and not args.output.exists()
    contract = json.loads((args.observation/'contract.json').read_text())
    summary = json.loads((args.observation/'summary.json').read_text())
    assert summary['status'] == 'passed output-only source/parameter/OP/AC parity'
    assert summary['quiet_op_exact'] and summary['full11512_and27_exact']
    wave = table(args.observation/'bandwidth_nodes.dat', contract['columns'])
    vectors = {name:wave[:, 1+2*i]+1j*wave[:, 2+2*i]
               for i, name in enumerate(contract['vectors'])}
    output = vectors['v(isense)']
    error = vectors['v(xs.vp)']-vectors['v(xs.vn)']
    stages, residual = decomposition(output, vectors['v(xs.xota.out1)'], error)
    f = wave[:, 0]
    records = []
    for target in [1., 1e4, 1e5, 5e5, 1e6, 1.5662019484317887e6, 2e6, 5e6, 1e7]:
        index = int(np.argmin(abs(np.log(f/target))))
        row = dict(requested_frequency_Hz=target, actual_frequency_Hz=float(f[index]),
                   output_magnitude_V_per_differential_V=float(abs(output[index])))
        row['stages'] = {name:dict(magnitude=float(abs(value[index])),
            normalized_to_1Hz_magnitude=float(abs(value[index]/value[0])),
            phase_deg=float(np.degrees(np.angle(value[index])))) for name, value in stages.items()}
        row['node_magnitudes_V_per_differential_V'] = {
            name:float(abs(value[index])) for name, value in vectors.items()}
        records.append(row)
    result = dict(status='completed source-defined response characterization',
        case=summary['case'], controls=control, decomposition_relative_residual=residual,
        frequencies=records, model_observables=summary['model_observables'],
        bindings={name:sha(args.observation/name) for name in
            ['summary.json', 'contract.json', 'probe.cir', 'provenance.json',
             'run.log', 'ac.dat', 'bandwidth_nodes.dat']},
        scope='Ratios on the original closed-loop solution, not independently opened-loop stage transfer functions. Miller feedback and other coupling remain active. Algebraic factorization does not attribute a pole or prove a causal component. Signed compact-model Jacobian capacitances are not positive lumped capacitors. No source, compensation, current or area change.')
    args.output.mkdir(parents=True)
    (args.output/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='model_observables'}, indent=2))


if __name__ == '__main__':
    main()
