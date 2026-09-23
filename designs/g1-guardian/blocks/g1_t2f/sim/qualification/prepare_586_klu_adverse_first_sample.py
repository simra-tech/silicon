#!/usr/bin/env python3
"""Prospective solver-only first adverse sample; no simulation or adoption."""
import difflib
import hashlib
import json
from pathlib import Path
from run_586_adverse_calibration_sample import HERE, ROOT, CONDITIONS, reference_run, sample_deck, sha


def klu_deck(original):
    assert '.options klu' not in original and original.count('\n.control\n') == 1
    result = original.replace('\n.control\n', '\n.options klu\n.control\n')
    assert result.replace('\n.options klu\n.control\n', '\n.control\n') == original
    return result


def main():
    corner, seed = 'fast', 75201
    out = HERE/'t2f586-klu-fast-firstsample-contract-20260923-a'
    out.mkdir(exist_ok=False)
    audit = HERE/'t2f586-klu-fast-own6-qualification-20260923.json'
    control = json.loads(audit.read_text())
    assert control['status'] == 'passed six-control same-KLU qualification'
    assert all(control['comparisons']['full3180'].values())
    assert all(all(v.values()) for v in control['comparisons']['waveforms'].values())
    assert len(control['variation']) == 1129 and all(v['status'] == 'passed' for v in control['variation'])
    reference = reference_run(corner)
    prep = json.loads((reference/'preparation.json').read_text())
    body = (reference/'probe.cir').read_text()
    cases = []
    for label, temperature, vdda, vdd, role in CONDITIONS:
        sparse = sample_deck(body, corner, seed, label)
        klu = klu_deck(sparse)
        (out/(label+'.cir')).write_text(klu)
        diff = out/(label+'.diff')
        diff.write_text(''.join(difflib.unified_diff(sparse.splitlines(True), klu.splitlines(True),
            fromfile='originalDeclaredFast75201/'+label, tofile='separateKluFirstSample/'+label)))
        cases.append(dict(label=label, temperature_C=temperature, VDDA_V=vdda, VDD_V=vdd, role=role,
            sparse_generated_sha256=hashlib.sha256(sparse.encode()).hexdigest(),
            klu_deck_sha256=sha(out/(label+'.cir')), difference_sha256=sha(diff), exact_inverse=True))
    paths = [Path(__file__).resolve(), HERE/'test_586_klu_adverse_first_sample.py', audit,
        HERE/'run_586_adverse_calibration_sample.py', HERE/'prepare_586_adverse_controls.py',
        HERE/'analyze_586_adverse_controls.py', HERE/'audit_586_klu_population_qualification.py',
        HERE/'t2f586-klu-own6-implementation-20260923-a.json',
        HERE/'t2f586-adverse-calibration-contract-20260923-a/contract.json']
    paths += [reference/n for n in ['probe.cir', 'preparation.json', 'population_inventory.json', 'bgr.spice', 't2f.spice', '.spiceinit']]
    packet = dict(status='prepared only; no solver adoption or firstsample execution release',
        corner=corner, seed=seed, run_id='t2f586-klu-adverse-calibration-s75201-20260923-a', cases=cases,
        source_hashes=prep['source_hashes'], inventory_sha256=prep['inventory_sha256'],
        runtime_identity=prep['runtime'], qualification_sha256=sha(audit),
        live_bindings_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},
        changed_semantics='Only .options klu relative to six exact original declared75201 fixtures; no source/cards/reset/seed/temperature/rails/stimulus/tolerance/time change.',
        acceptance='Original samecorner25/100 linear coefficients frozen, allfour heldout low/highrail -40/125 endpoints within +/-2C. All3180 before/after and acrossconditions exact, 1129primitive inventory,13finite namedvectors/32us/HBTVCE<=1.6/positivefrequency; fatalerror scans even exit0. Six600s leaves, all failures retained. Firstsample independent audit before any next29.',
        scope='Required original fast30 seeds75201..75230, no replacement seed or new distribution. This preparation proposes KLU for yet-unrun firstsample; it does not alter existing typical SPARSE300, original failed SPARSE controls or slow75101 failed sample. Rail-extreme integrity and accuracy remain NOTRUN.',
        execution='not implemented/not run; requires source-bound runner and independent audit review plus explicit adoption disposition and CPU lease',
        forecast=dict(maximum_CPU_seconds=3600, expected_bulk_GiB=.18, single_thread=True))
    target = out/'contract.json'
    target.write_text(json.dumps(packet, indent=2)+'\n')
    print(target.relative_to(ROOT), sha(target))


if __name__ == '__main__':
    main()
