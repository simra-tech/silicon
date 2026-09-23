#!/usr/bin/env python3
"""Bind firstsample implementation only; no execution/adoption authority."""
import json
from pathlib import Path
from prepare_586_klu_adverse_first_sample import HERE,ROOT,sha


def main():
    contract=HERE/'t2f586-klu-fast-firstsample-contract-20260923-a/contract.json'
    output=HERE/'t2f586-klu-fast-firstsample-implementation-20260923-a.json'
    assert not output.exists()
    files=[HERE/n for n in ['run_586_klu_adverse_first_sample.py','audit_586_klu_adverse_first_sample.py',
        'test_586_klu_adverse_implementation.py','qualify_586_klu_adverse_implementation.py',
        'run_586_adverse_calibration_sample.py','prepare_586_klu_adverse_first_sample.py',
        'analyze_586_adverse_controls.py','audit_586_adverse_calibration_samples.py',
        'run_586_population_control.py','run_586_source_control.py','run_586_nearendpoint_recovery.py',
        't2f586-klu-own6-preparation-20260923-a.json','t2f586-klu-nominal-references-20260923-b.json']]
    joint=ROOT/'designs/g1-guardian/blocks/g1_trip/sim'
    files += [joint/n for n in ['run_nominal_clock_probe.py','run_bgr_substitution_draw_audit.py',
        'analyze_bgr_substitution_outcomes.py','wave_archive.py','result_directory.py']]
    payload=dict(status='prepared implementation; no launch or adoption release',contract=str(contract.relative_to(ROOT)),
        contract_sha256=sha(contract),bindings_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},
        scope='Exactly six75201 KLU leaves, original600s/32us/full3180/13vectors/VCE1.6/frozenlinear2C. No next29, source/criterion/typicalpopulation change.',
        tests='2sixconditioninverse plus6failure/header tests PASS',forecast=dict(maximum_CPU_seconds=3600,external_growth_GiB=.18))
    output.write_text(json.dumps(payload,indent=2)+'\n')
    print(output.relative_to(ROOT),sha(output))


if __name__=='__main__':
    main()
