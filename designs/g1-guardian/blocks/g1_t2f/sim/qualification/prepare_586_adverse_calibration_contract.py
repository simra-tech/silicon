#!/usr/bin/env python3
"""Freeze prospective thirty-sample-per-corner contract; no simulation release."""
import argparse
import difflib
import json
from pathlib import Path
from run_586_adverse_calibration_sample import HERE, ROOT, SEED_START, CONDITIONS, reference_run, sample_deck, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract-id', required=True)
    args = parser.parse_args()
    import re
    assert re.fullmatch('[a-z0-9-]+', args.contract_id)
    out = HERE/args.contract_id
    out.mkdir(exist_ok=False)
    paths = [HERE/n for n in ['run_586_adverse_calibration_sample.py', 'audit_586_adverse_calibration_samples.py',
        'test_586_adverse_calibration_sample.py', 'prepare_586_adverse_population.py',
        'run_586_adverse_population_control.py', 'analyze_586_population.py', 'analyze_586_adverse_controls.py',
        'prepare_586_adverse_controls.py']]
    cases = []
    for corner, first_seed in SEED_START.items():
        reference = reference_run(corner)
        prep = json.loads((reference/'preparation.json').read_text())
        original = (reference/'probe.cir').read_text()
        paths += [HERE/('t2f586-'+corner+'-population-controls-20260923-a.json')]
        paths += [reference/n for n in ['preparation.json', 'probe.cir', 'population_inventory.json', 'bgr.spice', 't2f.spice', '.spiceinit']]
        for label, temperature, vdda, vdd, role in CONDITIONS:
            deck = sample_deck(original, corner, first_seed, label)
            diff = out/(corner+'-'+label+'.diff')
            diff.write_text(''.join(difflib.unified_diff(original.splitlines(True), deck.splitlines(True),
                fromfile=corner+'QualifiedReference', tofile=corner+'FirstSample/'+label)))
            cases.append(dict(corner=corner, seed=first_seed, label=label, temperature_C=temperature, VDDA_V=vdda, VDD_V=vdd,
                role=role, example_deck_sha256=__import__('hashlib').sha256(deck.encode()).hexdigest(),
                difference=str(diff.relative_to(ROOT)), difference_sha256=sha(diff), source_hashes=prep['source_hashes']))
    payload = dict(status='not run; prospective contract, no ensemble release', populations={
        c: dict(seeds=list(range(start, start+30)), samples=30, leaves_per_sample=6,
                required_qualification_audit='t2f586-'+c+'-population-qualification-20260923.json')
        for c, start in SEED_START.items()}, cases=cases,
        inventory=dict(parameters_per_leaf=3180, primitives=1129, BGR_primitives=1036, T2F_primitives=93),
        acceptance='Original same-corner25/100C at3.3/1.2V freezes linear calibration; allfour−40/125C endpointsat3.0/1.08and3.6/1.32V mustwithin±2C. No LUT, reciprocal or refit. Full3180beforeafter/crossconditions exact. Allattemptedseeds, numericalfailuresandmissingconditions retained.',
        gates=['Owncorner enabled/repeat/changed/disabled/disabledchanged/temperature-return exact qualification.',
               'Firstindependentsample full6leaf/source/deck/runtime/parameter/wave/calibration audit before next29.',
               'Numerically valid electricalfailures remain failures; completing predeclared characterization must not select survivors.'],
        source_scope='Immutable final586mm7de0fc andT2F7770, no canonicalcards/sourcechanges or newphysicalPEX/adoption.',
        resource_forecast=dict(watchdog_per_leaf_s=600, maximum_both_populations_CPU_hours=60,
            deterministic_based_slow30_CPU_hours=17.050424342323094, deterministic_based_fast30_CPU_hours=22.69492186017645,
            estimated_bulk_GiB=10.8, forecast_scope='Planning only, mismatchruntime may differ; freshgate each batch, no unconditional reservation or retry.'),
        live_bindings_sha256={str(p.relative_to(ROOT)): sha(p) for p in paths})
    output = out/'contract.json'
    output.write_text(json.dumps(payload, indent=2)+'\n')
    print(json.dumps(dict(contract=str(output.relative_to(ROOT)), sha256=sha(output), cases=len(cases)), indent=2))


if __name__ == '__main__':
    main()
