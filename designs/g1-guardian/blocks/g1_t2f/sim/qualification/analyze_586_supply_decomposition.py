#!/usr/bin/env python3
"""Frozen-calibration algebraic decomposition; not causal block attribution."""
import argparse
import json
from pathlib import Path
from prepare_586_supply_decomposition import HERE, sha


def decompose(f25, f100, nominal, adverse, temperature):
    slope = (f100-f25)/75
    assert slope > 0
    nominal_error = 25+(nominal-f25)/slope-temperature
    supply_delta = (adverse-nominal)/slope
    total_error = 25+(adverse-f25)/slope-temperature
    residual = nominal_error+supply_delta-total_error
    assert abs(residual) < 1e-10
    return dict(nominal_rail_error_C=nominal_error, supply_induced_difference_C=supply_delta,
        total_adverse_error_C=total_error, frequency_difference_Hz=adverse-nominal,
        algebraic_reconstruction_residual_C=residual,
        original_adverse_accuracy_status='passed' if abs(total_error) <= 2 else 'failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    packet_path = HERE/'t2f586-supply-decomposition-20260923-a.json'
    packet = json.loads(packet_path.read_text())
    result = dict(status='not run to completion', records=[], packet_sha256=sha(packet_path), receipts_sha256={},
        scope='Conditional no-mm fixed-corner diagnostic. Frozen samecorner25/100nominal-rail calibration unchanged. Separates nominal-rail endpoint residual from simultaneous VDDA/VDD12/enable-amplitude change. Neither term identifies a causal circuitblock; nominal residual includes all temperature-dependent mechanisms.1e-10C reconstruction bound is numerical algebra checking, not altered2C electrical acceptance.')

    def load(run_id, case=None):
        run = HERE/'runs'/run_id
        row, = json.loads((run/'summary.json').read_text())
        prep = json.loads((run/'preparation.json').read_text())
        provenance = json.loads((run/'provenance.json').read_text())
        assert row['control_status'] == row['full3180_status'] == 'passed'
        assert all(provenance['input_checks'].values())
        assert row['parameters_before'] == row['parameters_after']
        assert sha(run/'probe.cir') == prep['deck_sha256']
        if case:
            assert sha(run/'preparation.json') == case['preparation_sha256']
            assert sha(run/'probe.cir') == case['deck_sha256']
        result['receipts_sha256'][run_id] = {n: sha(run/n) for n in ['summary.json', 'provenance.json', 'preparation.json', 'probe.cir']}
        return row

    for case in packet['cases']:
        record = dict(corner=case['corner'], label=case['label'], temperature_C=case['temperature_C'], status='not run')
        result['records'].append(record)
        if not (HERE/'runs'/case['run_id']/'summary.json').exists():
            continue
        try:
            nominal = load(case['run_id'], case)
            prefix = 't2f586-adverse-controls-20260922-a-'+case['corner']+'-'
            cal25, cal100 = load(prefix+'cal25'), load(prefix+'cal100')
            vector = nominal['parameters_before']
            assert cal25['parameters_before'] == cal100['parameters_before'] == vector
            temperature = case['temperature_C']
            endpoints = []
            for rail in ['low', 'high']:
                label = rail+('cold' if temperature == -40 else 'hot')
                run_id = ('t2f586-fast-highhot-recovery900-20260923-a'
                    if (case['corner'], label) == ('fast', 'highhot') else prefix+label)
                adverse = load(run_id)
                assert adverse['parameters_before'] == vector
                term = decompose(cal25['measurements']['freq'], cal100['measurements']['freq'],
                    nominal['measurements']['freq'], adverse['measurements']['freq'], temperature)
                term.update(rail=rail, adverse_run=run_id,
                    adverse_measurements=adverse['measurements'],
                    vref_printed_mean_difference_V=adverse['measurements']['vref_avg']-nominal['measurements']['vref_avg'],
                    vref_difference_scope='Difference of rounded printed average scalars, not exact waveform or isolated causal contribution')
                endpoints.append(term)
            record.update(status='passed algebraic diagnostic; original electrical outcomes separate',
                full3180_samecorner_status='passed', nominal_run=case['run_id'], terms=endpoints,
                nominal_measurements=nominal['measurements'])
        except (AssertionError, OSError, ValueError, KeyError) as error:
            record.update(status='failed diagnostic input/evidence check', error=repr(error))
    if all(r['status'].startswith('passed') for r in result['records']):
        result['status'] = 'passed conditional algebraic diagnostic; electrical failures retained'
    elif any(r['status'].startswith('failed') for r in result['records']):
        result['status'] = 'failed diagnostic input/evidence check; other completed records retained'
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], output_sha256=sha(args.output), records=result['records']), indent=2))


if __name__ == '__main__':
    main()
