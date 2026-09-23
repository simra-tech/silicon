#!/usr/bin/env python3
"""Write a prospective sample contract and exact example transforms, never simulate."""
import difflib
import json
from pathlib import Path
from run_586_calibration_sample import HERE, ROOT, REFERENCE, TEMPERATURES, sample_deck, sha


def main():
    out = HERE/'t2f586-calibration-contract-20260922-a'
    assert not out.exists()
    out.mkdir()
    reference = (REFERENCE/'probe.cir').read_text()
    files = []
    for temperature in TEMPERATURES:
        deck = sample_deck(reference, 74101, temperature)
        name = 'seed74101-temp%d.diff' % temperature
        (out/name).write_text(''.join(difflib.unified_diff(reference.splitlines(True), deck.splitlines(True),
            fromfile='enabled74001-qualified-control', tofile='prospective74101-temp%d' % temperature)))
        files.append(dict(temperature_C=temperature, diff=name, diff_sha256=sha(out/name),
                          prospective_deck_sha256=__import__('hashlib').sha256(deck.encode()).hexdigest()))
    prep = json.loads((REFERENCE/'preparation.json').read_text())
    paths = [REFERENCE/n for n in ['probe.cir', 'preparation.json', 'population_inventory.json', 'bgr.spice', 't2f.spice', '.spiceinit']]
    paths += [HERE/n for n in ['run_586_calibration_sample.py', 'test_586_calibration_sample.py',
        'prepare_586_calibration_contract.py', 'run_586_population_control.py', 'analyze_586_population.py']]
    report = dict(status='not run; prospective contract awaiting six-control gate and coordinator review',
        seeds=list(range(74101, 74401)), population_size=300, parameter_count=3180, primitive_count=1129,
        source_hashes=prep['source_hashes'], runtime=prep['runtime'], examples=files,
        live_bindings_sha256={str(p.relative_to(ROOT)): sha(p) for p in paths},
        temperatures_C=TEMPERATURES, watchdog_per_leaf_s=600, maximum_attempted_leaves_per_sample=4,
        sample_policy='One independent parent per seed. Each leaf resets exactly once at same sample seed; full3180 before/after and across all four temperatures must be exact. No retry, rejection sampling or missing-sample replacement. Failed leaves retained while independent remaining conditions attempted; incomplete or failed samples remain in denominator.',
        calibration='Original25/100C linear calibration frozen before held-out−40/125C residual checks; bothabs≤2C. No newLUT/refit/threshold.',
        qualification='All six own T2F586 controls including same-instance25→125→−40→25 return must pass exact3180 parameters and original13-column wave gates. First3 complete samples independently audited beforefirst20; first20 independently audited before remaining280. Joint SENSE first20 is unrelated, not substituted.',
        unchanged='Source/model/card/options/32us/50fF/ideal1VIPTAT/3.3and1.2V/enable/frequencymeasurements unchanged. Only seed and declaredtemperature directives differ from enabled74001 single-phase deck. Inherited descriptive title remains stale; executable deck/provenance authoritative.',
        storage_forecast_GiB=36, first_three_growth_GiB=.36,
        throughput='Qualification singleleaf about370–550s;4leavesperparent about1480–2200s,300 about123–183CPUh before tails. Actual first3 measurements supersede forecast.',
        exclusions='Not old510xx identity, newphysicalCC adoption, actualpad-loading coverage, radiation/yield or all-temperature bound. Originalstatistical failures retained.')
    (out/'contract.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(contract=str((out/'contract.json').relative_to(ROOT)), sha256=sha(out/'contract.json')), indent=2))


if __name__ == '__main__':
    main()
