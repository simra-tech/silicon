#!/usr/bin/env python3
"""One frozen rail-factorial diagnostic; no calibration refit or population."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from prepare_586_adverse_controls import HERE, ROOT, ANALYSIS, sha
from prepare_586_rail_factorial import make_deck
from run_586_source_control import load_wave
from run_586_population_control import nominal_gate
from run_nominal_clock_probe import run_bounded
from run_bgr_substitution_draw_audit import read_group
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--corner', choices=['slow', 'fast'], required=True)
    parser.add_argument('--label', choices=['analoghigh', 'digitalhigh'], required=True)
    parser.add_argument('--image-id', required=True)
    args = parser.parse_args()
    packet_path = args.packet if args.packet.is_absolute() else HERE/args.packet
    packet = json.loads(packet_path.read_text())
    case, = [r for r in packet['cases'] if (r['corner'], r['label']) == (args.corner, args.label)]
    out = HERE/'runs'/case['run_id']
    prep = json.loads((out/'preparation.json').read_text())
    assert not (out/'run.log').exists() and sha(out/'preparation.json') == case['preparation_sha256']
    deck = (out/'probe.cir').read_text()
    assert deck == make_deck((ROOT/prep['factorial_reference']/'probe.cir').read_text(), prep['label'])
    assert prep['temperature_C'] == -40 and prep['watchdog_s'] == packet['watchdog_per_leaf_s'] == 600
    nominal_gate(ANALYSIS)
    pdk = Path('/foss/pdks/ihp-sg13g2')
    for filename, section in re.findall(r'(?m)^\.lib\s+(\S+)\s+(\S+)\s*$', deck):
        assert re.search(r'(?im)^\.lib\s+'+re.escape(section)+r'\s*$', Path(filename).read_text(encoding='latin1'))
    runtime = dict(image_id=args.image_id, pdk_commit=(pdk/'COMMIT').read_text().strip(),
        ngspice=subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
        models_sha256={str(p.relative_to(pdk)): sha(p) for p in sorted((pdk/'libs.tech/ngspice/models').glob('*.lib'))},
        osdi_sha256={str(p.relative_to(pdk)): sha(p) for p in sorted((pdk/'libs.tech/ngspice/osdi').glob('*.osdi'))})
    checks = dict(runtime=runtime == prep['runtime'], sources=all(sha(out/n) == v for n, v in prep['source_hashes'].items()),
        deck=sha(out/'probe.cir') == prep['deck_sha256'] == case['deck_sha256'],
        live_bindings=all(sha(ROOT/n) == v for n, v in prep['live_bindings_sha256'].items()),
        nominal_analysis=sha(ANALYSIS) == prep['nominal_analysis_sha256'])
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:], packet_sha256=sha(packet_path),
        preparation_sha256=sha(out/'preparation.json'), runner_sha256=sha(Path(__file__)), runtime_identity=runtime,
        input_checks=checks, source_hashes=prep['source_hashes'], scope=prep['contract']), indent=2)+'\n')
    assert all(checks.values()), 'Input failure; no simulation launched'
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', 'probe.cir'], stream, out/'run.json', 600, cwd=out, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', line, re.I)]
    result = dict(control_status='failed', runtime=state, errors=errors, warnings=warning_inventory(log), corner=prep['corner'],
        label=prep['label'], temperature_C=-40, VDDA_V=prep['VDDA_V'], VDD_V=prep['VDD_V'], enable_high_V=prep['enable_high_V'],
        full3180_status='not run', calibration_status='not run; separate frozen-coefficient factorial analysis required', scope=prep['contract'])
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        before = {tag: read_group(log, tag+'_BEFORE', keys) for tag, keys in prep['groups'].items()}
        after = {tag: read_group(log, tag+'_AFTER', keys) for tag, keys in prep['groups'].items()}
        assert sum(map(len, before.values())) == 3180 and before == after == prep['samecorner_reference3180']
        result.update(full3180_status='passed', parameters_before=before, parameters_after=after)
        blob, data = load_wave(out/prep['output_wave'])
        assert data.ndim == 2 and data.shape[1] == 13 and np.isfinite(data).all()
        assert abs(data[-1, 0]-32e-6) < 1e-12 and np.all(np.diff(data[:, 0]) > 0)
        values = {k: float(v) for k, v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)', log)}
        assert all(k in values and math.isfinite(values[k]) for k in ['freq', 't_a', 't_b', 't_half_a', 'fout_hi', 'fout_lo'])
        assert values['freq'] > 0 and values['t_b'] > values['t_a']
        vce = float(max(np.abs(data[:, i]-data[:, j]).max() for i, j in [(7, 8), (9, 8), (10, 11), (12, 11)]))
        result.update(wave_rows=len(data), waveform_sha256=__import__('hashlib').sha256(blob).hexdigest(), measurements=values,
                      t2f_hbt_external_vce_max_V=vce, t2f_hbt_vce_status='passed' if vce <= 1.6 else 'failed')
        assert vce <= 1.6
        result['control_status'] = 'passed'
    except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    if (out/prep['output_wave']).exists():
        archive_new_wave(out/prep['output_wave'])
    print(json.dumps({k: v for k, v in result.items() if k not in ['parameters_before', 'parameters_after', 'warnings']}, indent=2))
    raise SystemExit(0 if result['control_status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
