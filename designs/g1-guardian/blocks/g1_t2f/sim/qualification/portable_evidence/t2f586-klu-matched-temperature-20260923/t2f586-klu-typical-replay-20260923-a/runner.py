#!/usr/bin/env python3
"""Run one matched completed32us solver-selector-only control; no solver adoption."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from prepare_586_klu_controls import HERE, ROOT, make_full as make_prefix, sha
from run_586_population_control import nominal_gate, phase_text
from run_586_source_control import load_wave
from run_nominal_clock_probe import run_bounded
from run_bgr_substitution_draw_audit import read_group
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--image-id', required=True)
    args = parser.parse_args()
    packet_path = args.packet if args.packet.is_absolute() else HERE/args.packet
    packet = json.loads(packet_path.read_text())
    out = HERE/'runs'/packet['run_id']
    assert not (out/'run.log').exists()
    prep = json.loads((out/'preparation.json').read_text())
    ORIGINAL = HERE/'runs'/prep['original_run']
    assert sha(out/'preparation.json') == packet['preparation_sha256']
    assert (out/'probe.cir').read_text() == make_prefix((ORIGINAL/'probe.cir').read_text())
    nominal_gate(ROOT/prep['required_nominal_analysis'])
    pdk = Path('/foss/pdks/ihp-sg13g2')
    runtime = dict(image_id=args.image_id, pdk_commit=(pdk/'COMMIT').read_text().strip(),
        ngspice=subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
        models_sha256={str(p.relative_to(pdk)): sha(p) for p in sorted((pdk/'libs.tech/ngspice/models').glob('*.lib'))},
        osdi_sha256={str(p.relative_to(pdk)): sha(p) for p in sorted((pdk/'libs.tech/ngspice/osdi').glob('*.osdi'))})
    checks = dict(runtime=runtime == prep['runtime'], sources=all(sha(out/n) == v for n,v in prep['source_hashes'].items()),
        deck=sha(out/'probe.cir') == packet['deck_sha256'] == prep['deck_sha256'],
        original_deck=sha(ORIGINAL/'probe.cir') == prep['original_deck_sha256'],
        inventory=sha(out/'population_inventory.json') == prep['inventory_sha256'],
        live_bindings=all(sha(ROOT/n) == v for n,v in prep['live_bindings_sha256'].items()))
    (out/'runner.py').write_text(Path(__file__).read_text())
    provenance = dict(arguments=sys.argv[1:], runner_sha256=sha(Path(__file__)), packet_sha256=sha(packet_path),
        preparation_sha256=sha(out/'preparation.json'), input_checks=checks, runtime_identity=runtime,
        source_hashes=prep['source_hashes'], scope=prep['scope'])
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    assert all(checks.values()), 'Input failure, simulation not launched'
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', 'probe.cir'], stream, out/'run.json', 600, cwd=out, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', line, re.I)]
    result = dict(control_status='failed', runtime=state, errors=errors, warnings=warning_inventory(log),
        full3180_status='not run', original_full_run_status='completed SPARSE control retained unchanged',
        original_wave_prefix_comparison='not run by runner; separate full-wave matched audit required',
        frequency_accuracy_fullqualification='frequency observations only; no calibration or population qualification', scope=prep['scope'])
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        assert 'Using KLU as Direct Linear Solver' in log and 'Using SPARSE 1.3 as Direct Linear Solver' not in log
        phase = phase_text(log, 0)
        before = {tag: read_group(phase, 'P0_'+tag+'_BEFORE', keys) for tag,keys in prep['groups'].items()}
        after = {tag: read_group(phase, 'P0_'+tag+'_AFTER', keys) for tag,keys in prep['groups'].items()}
        assert sum(map(len, before.values())) == 3180 and before == after == prep['required_before3180']
        blob, data = load_wave(out/'phase0.dat')
        assert data.ndim == 2 and data.shape[1] == 13 and np.isfinite(data).all()
        assert abs(data[-1,0]-32e-6) < 1e-12 and np.all(np.diff(data[:,0]) > 0)
        vce = float(max(np.abs(data[:,i]-data[:,j]).max() for i,j in [(7,8),(9,8),(10,11),(12,11)]))
        result.update(parameters_before=before, parameters_after=after, full3180_status='passed', wave_rows=len(data),
            waveform_sha256=hashlib.sha256(blob).hexdigest(), t2f_hbt_external_vce_max_V=vce,
            t2f_hbt_vce_status='passed' if vce <= 1.6 else 'failed')
        values = {k: float(v) for k, v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)', phase)}
        assert all(k in values and np.isfinite(values[k]) for k in ['freq', 't_a', 't_b', 't_half_a', 'fout_hi', 'fout_lo'])
        assert values['freq'] > 0 and values['t_b'] > values['t_a']
        result['measurements'] = values
        assert vce <= 1.6
        result['control_status'] = 'passed full32us solver diagnostic'
    except (AssertionError, OSError, ValueError, KeyError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    if (out/'phase0.dat').exists():
        archive_new_wave(out/'phase0.dat')
    print(json.dumps({k:v for k,v in result.items() if k not in ['parameters_before','parameters_after','warnings']}, indent=2))
    raise SystemExit(0 if result['control_status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()



