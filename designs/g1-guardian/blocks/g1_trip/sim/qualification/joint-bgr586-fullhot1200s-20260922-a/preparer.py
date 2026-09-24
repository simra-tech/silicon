#!/usr/bin/env python3
"""Prepare one fresh fullhot diagnostic with1200s cap and exact200ns prefix gate."""
import difflib
import hashlib
import json
from pathlib import Path
from result_directory import allocate_run
from prepare_bgr_prefix_probe import require_measurements_inside_prefix
from bgr_prefix_parity import select_prefix
from wave_archive import open_wave, wave_sha

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original = SIM / 'qualification/joint-bgr586-nominal-substitution-hot-20260922-a'
    prefix = SIM / 'qualification/joint-bgr586-hot-prefix219ns-20260922-a'
    observation = SIM.parent / 'reports/resume-server-20260922/joint-bgr586-prefix219ns-failed-fixture-observation-audit.json'
    old_result, = json.loads((original / 'summary.json').read_text())
    prefix_result, = json.loads((prefix / 'summary.json').read_text())
    observed = json.loads(observation.read_text())
    assert old_result['watchdog_status'] == 'timeout' and old_result['wall_s'] >= 600
    assert prefix_result['prefix_contract_status'] == 'failed'
    assert observed['original_fixture_status'] == 'failed; unchanged' and observed['limited_observation_status'].startswith('passed finite saved219ns')
    assert observed['summary_sha256'] == sha(prefix / 'summary.json')
    assert observed['decoded_wave_sha256'] == wave_sha(prefix / 'hard_+0mV.dat')
    assert all(observed['parameter_audit']['checks'].values())
    prep = json.loads((original / 'preparation.json').read_text())
    old_deck = (original / 'hard_+0mV.cir').read_text()
    measures = require_measurements_inside_prefix(old_deck, endpoint_s=1.02e-6)
    assert len(measures) == 8 and old_deck.count('tran 0.2n 1.02u 0 0.2n\n') == 1
    with open_wave(prefix / 'hard_+0mV.dat', 'rb') as stream:
        prefix_bytes = select_prefix(stream.read())
    out = allocate_run(SIM, 'joint-bgr586-fullhot1200s-20260922-a')
    for name in ['sense.spice', 'trip.spice', 'bgr.spice', 'non_bgr_inventory.json']:
        (out / name).write_bytes((original / name).read_bytes())
    deck = old_deck.replace(original.name, out.name)
    assert deck.replace(out.name, original.name) == old_deck
    (out / 'hard_+0mV.cir').write_text(deck)
    diff = ''.join(difflib.unified_diff(old_deck.replace(original.name, '@RUN@').splitlines(True),
                   deck.replace(out.name, '@RUN@').splitlines(True), fromfile='preservedFullHot600s', tofile='freshFullHot1200s'))
    assert diff == ''
    (out / 'declared_fullhot_difference.diff').write_text(diff)
    bindings = json.loads((prefix / 'prelaunch_reference_bindings.json').read_text())
    for name in ['summary.json', 'provenance.json', 'preparation.json', 'hard_+0mV.cir', 'run.json', 'run.log', 'hard_+0mV.dat.archive.json']:
        bindings['sha256'][str((prefix / name).relative_to(ROOT))] = sha(prefix / name)
    bindings['sha256'][str(observation.relative_to(ROOT))] = sha(observation)
    for name in ['bgr_prefix_parity.py', 'run_bgr_full_hot_probe.py']:
        bindings['sha256'][str((SIM / name).relative_to(ROOT))] = sha(SIM / name)
    assert all(sha(ROOT / path) == value for path, value in bindings['sha256'].items())
    (out / 'prelaunch_reference_bindings.json').write_text(json.dumps(bindings, indent=2) + '\n')
    prep.update(run=out.name, prepared_deck_sha256=sha(out / 'hard_+0mV.cir'),
                prepared_runner_sha256=sha(SIM / 'run_bgr_full_hot_probe.py'),
                fullhot_reference_run=original.name, prefix_reference_run=prefix.name,
                prefix_observation_audit=str(observation.relative_to(ROOT)), prefix_observation_audit_sha256=sha(observation),
                baseline_op_binding_status='Completed original hotOP required; exact bound8670inventory retained.')
    prep['strict_prefix_contract'] = {key: prefix_bytes[key] for key in ['sha256', 'byte_count', 'row_count', 'last_included_time_s']}
    prep['strict_prefix_contract'].update(window_s=[0, 200e-9], decoded_and_numeric_exact=True, columns=18,
                                         endpoint219ns='deliberately excluded; no resampling or tolerance')
    prep['planning'] = {'watchdog_s': 1200, 'home_total_budget_GiB': .15, 'proposed_cpu': 5, 'maximum_new_simulations': 1,
                        'forecast_full_s': [950, 1100], 'justification': 'Preserved600s job advanced620ns; separate219ns trace finite withfullinventory in249.454s. A fresh fullrun around1000s is plausible, not guaranteed. No originaljob extension/retryloop.',
                        'resource_gate': 'not run; fresh gate required after review'}
    prep['scope'] = 'One fresh nominalBGR586 hot full1.02us model-level diagnostic withdeclared1200s cap and exact0..200ns prefix gate. Preserve old600stimeout and219ns measurementfailure. No population/recalibration/physicalqualification or automaticretry.'
    prep['unchanged'] = 'Exact originalfullhot deck/source/model/runtime/stimulus/seed/codes/solver/tolerances/endpoint/measurements; only runpaths and externalwatchdog budget differ. All late3actual/legacy sampling unchanged.'
    (out / 'preparation.json').write_text(json.dumps(prep, indent=2) + '\n')
    (out / 'preparer.py').write_text(Path(__file__).read_text())
    runner_difference = ''.join(difflib.unified_diff((original / 'runner.py').read_text().splitlines(True),
                         (SIM / 'run_bgr_full_hot_probe.py').read_text().splitlines(True),
                         fromfile='archivedFullHot600sRunner', tofile='freshFullHot1200sPrefixGatedRunner'))
    (out / 'declared_runner_difference.diff').write_text(runner_difference)
    audit = {'status': 'passed prepare-only exact normalized fullhot deck/source transform', 'normalized_deck_diff_empty': True,
             'source_hashes_exact': all(sha(out / name) == value for name, value in prep['source_hashes'].items()),
             'prepared_deck_sha256': prep['prepared_deck_sha256'], 'valid_original_measurements': measures,
             'unchanged_original_late_sampling': prep['prospective_sampling'], 'strict_prefix_contract': prep['strict_prefix_contract'],
             'live_binding_count': len(bindings['sha256']), 'runner_difference_sha256': sha(out / 'declared_runner_difference.diff'),
             'prepared_runner_sha256': prep['prepared_runner_sha256'], 'simulator': 'not run'}
    (out / 'fullhot_structure_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
