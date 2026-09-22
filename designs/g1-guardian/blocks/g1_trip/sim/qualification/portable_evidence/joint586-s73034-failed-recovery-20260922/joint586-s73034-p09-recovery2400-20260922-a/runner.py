#!/usr/bin/env python3
"""Run exactly one prepared frozen-input 2400 s recovery; never modifies original."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from prepare_joint586_leaf_recovery import transform, ORIGINAL
from run_joint586_calibration import sha
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import run_bounded, analyze_wave, validate_saved_nodes
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    args = p.parse_args()
    out = SIM/'qualification'/args.run_id
    prep = json.loads((out/'preparation.json').read_text())
    old = SIM/'qualification'/ORIGINAL
    assert not (out/'run.log').exists() and prep['watchdog_s'] == 2400
    assert (out/'probe.cir').read_text() == transform((old/'p09/probe.cir').read_text(), out.name)
    validate_saved_nodes((out/'probe.cir').read_text(), (old/'trip.spice').read_text())
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = dict(image_id_observed_by_host=args.image_id, pdk_commit=(pd/'COMMIT').read_text().strip(),
                   ngspice_version=subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
                   model_sha256={str(f.relative_to(pd)): sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()}, solver='sparse')
    checks = dict(runtime=runtime == prep['runtime_identity'], deck=sha(out/'probe.cir') == prep['deck_sha256'],
                  sources=all(sha(old/n) == v for n, v in prep['source_hashes'].items()), bindings=all(sha(ROOT/n) == v for n, v in prep['bindings_sha256'].items()))
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:], input_checks=checks, runtime_identity=runtime,
                                                   source_hashes=prep['source_hashes'], runner_sha256=sha(Path(__file__)), scope=prep['scope']), indent=2)+'\n')
    assert all(checks.values()), 'Input check failed before simulation'
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str((out/'probe.cir').relative_to(SIM))], stream, out/'run.json', 2400, cwd=SIM, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', line)]
    result = dict(status='failed recovery', runtime=state, errors=errors, warnings=warning_inventory(log), original_failure_preserved=True,
                  original_wave_prefix_status='not run; original timeout exported no waveform', scope=prep['scope'])
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        section, = re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$', log, re.M | re.S)
        result['parameter_audit'] = phase_parameters(section, prep['groups'], prep['expected11512'])
        data = [list(map(float, s.split())) for s in (out/'phase0.dat').read_text().splitlines()[1:] if s.strip()]
        assert data and all(len(row) == 18 and all(math.isfinite(v) for v in row) for row in data)
        assert abs(data[-1][0]-1.02e-6) < 1e-18
        result['wave_analysis'] = analyze_wave([row[:13] for row in data], prep['prospective_sampling'])
        assert result['wave_analysis']['sampling_status'] == 'passed'
        result['decisions'] = {k: row['measured_edge_decision'] for k, row in result['wave_analysis']['comparators'].items()}
        result.update(status='passed distinct recovered leaf contract; original sample remains separately failed', wave_rows=len(data), decoded_wave_sha256=sha(out/'phase0.dat'))
    except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    if (out/'phase0.dat').exists():
        archive_new_wave(out/'phase0.dat')
    print(json.dumps({k: v for k, v in result.items() if k not in ['parameter_audit', 'wave_analysis', 'warnings']}, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
