#!/usr/bin/env python3
"""Frozen calibration rail-factorial identity, not device-level attribution."""
import argparse
import json
from pathlib import Path
from prepare_586_rail_factorial import HERE, sha


def factorial(f25, f100, nominal, analog, digital, both):
    slope = (f100-f25)/75
    assert slope > 0
    nominal_error = 25+(nominal-f25)/slope+40
    analog_delta = (analog-nominal)/slope
    digital_delta = (digital-nominal)/slope
    interaction = (both-analog-digital+nominal)/slope
    observed_error = 25+(both-f25)/slope+40
    residual = nominal_error+analog_delta+digital_delta+interaction-observed_error
    assert abs(residual) < 1e-10
    return dict(nominal_error_C=nominal_error, analog_plus_enable_delta_C=analog_delta,
        digital_rail_delta_C=digital_delta, interaction_C=interaction, observed_allhigh_error_C=observed_error,
        reconstruction_residual_C=residual, original_accuracy_status='passed' if abs(observed_error) <= 2 else 'failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    packet_path = args.packet if args.packet.is_absolute() else HERE/args.packet
    packet = json.loads(packet_path.read_text())
    assert not args.output.exists()
    result = dict(status='not run to completion', records=[], packet_sha256=sha(packet_path), receipts_sha256={},
        scope='Each process corner uses frozen25/100nominal calibration and exactsamecorner3180. Finite difference interaction explicitly retained. Analog factor includes bothVDDA and its HV-enable amplitude; not their separate causal attribution. No source/model/acceptance change or statistical/adoption claim.')

    def load(run_id):
        run = HERE/'runs'/run_id
        row, = json.loads((run/'summary.json').read_text())
        prep = json.loads((run/'preparation.json').read_text())
        provenance = json.loads((run/'provenance.json').read_text())
        assert row['control_status'] == row['full3180_status'] == 'passed'
        assert all(provenance['input_checks'].values())
        assert row['parameters_before'] == row['parameters_after']
        assert sha(run/'probe.cir') == prep['deck_sha256']
        result['receipts_sha256'][run_id] = {n: sha(run/n) for n in ['summary.json', 'preparation.json', 'provenance.json', 'probe.cir']}
        return row

    for corner in ['slow', 'fast']:
        record = dict(corner=corner, temperature_C=-40, status='not run')
        result['records'].append(record)
        cases = {r['label']: r for r in packet['cases'] if r['corner'] == corner}
        if not all((HERE/'runs'/r['run_id']/'summary.json').exists() for r in cases.values()):
            continue
        try:
            for case in cases.values():
                run = HERE/'runs'/case['run_id']
                assert sha(run/'preparation.json') == case['preparation_sha256']
                assert sha(run/'probe.cir') == case['deck_sha256']
            prefix = 't2f586-adverse-controls-20260922-a-'+corner+'-'
            rows = dict(cal25=load(prefix+'cal25'), cal100=load(prefix+'cal100'), both=load(prefix+'highcold'),
                nominal=load('t2f586-supply-decomposition-20260923-a-'+corner+'-nomcold'),
                analog=load(cases['analoghigh']['run_id']), digital=load(cases['digitalhigh']['run_id']))
            vector = rows['nominal']['parameters_before']
            assert all(r['parameters_before'] == vector for r in rows.values())
            terms = factorial(**{k: r['measurements']['freq'] for k,r in rows.items() if k not in ['cal25','cal100']},
                f25=rows['cal25']['measurements']['freq'], f100=rows['cal100']['measurements']['freq'])
            record.update(status='passed conditional factorial analysis', full3180_samecorner_status='passed',
                terms=terms, measured_scalars={k: r['measurements'] for k,r in rows.items()})
        except (AssertionError, OSError, ValueError, KeyError) as error:
            record.update(status='failed diagnostic input/evidence check', error=repr(error))
    if all(r['status'].startswith('passed') for r in result['records']):
        result['status'] = 'passed conditional factorial analysis; original electrical outcomes unchanged'
    elif any(r['status'].startswith('failed') for r in result['records']):
        result['status'] = 'failed diagnostic input/evidence check; other completed records retained'
    result['analyzer_sha256'] = sha(Path(__file__))
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['records'], indent=2))


if __name__ == '__main__':
    main()
