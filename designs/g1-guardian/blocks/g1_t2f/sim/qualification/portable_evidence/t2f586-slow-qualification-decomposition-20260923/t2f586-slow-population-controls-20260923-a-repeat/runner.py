#!/usr/bin/env python3
"""Run one prepared corner-specific T2F586 control; no ensemble or retries."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from prepare_586_population import BASE, HERE, ROOT, mismatch_source, sha
from prepare_586_adverse_population import make_deck
from run_586_source_control import load_wave
from run_nominal_clock_probe import run_bounded
from run_bgr_substitution_draw_audit import read_group
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave


def phase_text(log, index):
    pattern = r'(?ms)^PHASE%d_BEGIN\s*$\n(.*?)^PHASE%d_END\s*$' % (index, index)
    matches = re.findall(pattern, log)
    assert len(matches) == 1, 'Missing or duplicated complete phase%d' % index
    return matches[0]


def exact_wave(first, second):
    blob_a, a = load_wave(first)
    blob_b, b = load_wave(second)
    return dict(decoded_bytes=blob_a == blob_b, numeric_rows=bool(np.array_equal(a, b)),
                time_grid=a.shape == b.shape and bool(np.array_equal(a[:, 0], b[:, 0])))


def nominal_gate(path):
    analysis = json.loads(path.read_text())
    assert analysis['status'] == 'passed' and analysis['full3180_same_nominal_parameters_across_anchors'] == 'passed'
    assert len(analysis['receipts_sha256']) == 4
    for run, receipts in analysis['receipts_sha256'].items():
        assert all(sha(HERE/'runs'/run/name) == value for name, value in receipts.items())
    return analysis


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--image-id', required=True)
    args = parser.parse_args()
    packet_path = args.packet if args.packet.is_absolute() else HERE/args.packet
    packet = json.loads(packet_path.read_text())
    case, = [c for c in packet['cases'] if c['label'] == args.label]
    out = HERE/'runs'/case['run_id']
    prep = json.loads((out/'preparation.json').read_text())
    assert sha(out/'preparation.json') == case['preparation_sha256'] and not (out/'run.log').exists()
    analysis_path = ROOT/prep['required_nominal_analysis']
    analysis = nominal_gate(analysis_path)
    original = (BASE/'ptat_T12.5.cir').read_text()
    assert (out/'probe.cir').read_text() == make_deck(original, prep['corner'], prep['seed'], prep['temperatures_C'], prep['groups'])
    nominal_packet_path = ROOT/prep['nominal_packet']
    nominal_packet = json.loads(nominal_packet_path.read_text())
    nominal = ROOT/prep['nominal_reference']
    nominal_result, = json.loads((nominal/'summary.json').read_text())
    assert nominal_result['control_status'] == nominal_result['full3180_status'] == 'passed'
    assert nominal_result['parameters_before'] == prep['nominal_parameters']
    for name in ['bgr.spice', 't2f.spice']:
        assert sha(nominal/name) == prep['nominal_source_hashes'][name]
        assert (out/name).read_text() == mismatch_source((nominal/name).read_text(), prep['mismatch_enabled'])
    for filename, section in re.findall(r'(?m)^\.lib\s+(\S+)\s+(\S+)\s*$', (out/'probe.cir').read_text()):
        assert re.search(r'(?im)^\.lib\s+'+re.escape(section)+r'\s*$', Path(filename).read_text(encoding='latin1'))
    pdk = Path('/foss/pdks/ihp-sg13g2')
    runtime = dict(image_id=args.image_id, pdk_commit=(pdk/'COMMIT').read_text().strip(),
        ngspice=subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
        models_sha256={str(p.relative_to(pdk)): sha(p) for p in sorted((pdk/'libs.tech/ngspice/models').glob('*.lib'))},
        osdi_sha256={str(p.relative_to(pdk)): sha(p) for p in sorted((pdk/'libs.tech/ngspice/osdi').glob('*.osdi'))})
    checks = dict(runtime=runtime == prep['runtime'], sources=all(sha(out/n) == v for n, v in prep['source_hashes'].items()),
        deck=sha(out/'probe.cir') == prep['deck_sha256'] == case['deck_sha256'],
        inventory=sha(out/'population_inventory.json') == prep['inventory_sha256'] == packet['inventory_sha256'],
        live_bindings=all(sha(ROOT/n) == v for n, v in prep['live_bindings_sha256'].items()),
        nominal_packet=sha(nominal_packet_path) == packet['nominal_packet_sha256'])
    (out/'runner.py').write_text(Path(__file__).read_text())
    provenance = dict(arguments=sys.argv[1:], runner_sha256=sha(Path(__file__)), packet_sha256=sha(packet_path),
        preparation_sha256=sha(out/'preparation.json'), runtime_identity=runtime, input_checks=checks,
        source_hashes=prep['source_hashes'], nominal_analysis_sha256=sha(analysis_path),
        nominal_analysis_receipts=analysis['receipts_sha256'], scope=prep['scope'])
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    assert all(checks.values()), 'Input binding failure; simulation not launched'
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', 'probe.cir'], stream, out/'run.json', prep['watchdog_s'], cwd=out, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [s for s in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', s, re.I)]
    result = dict(control_status='failed', runtime=state, errors=errors, warnings=warning_inventory(log),
        label=args.label, seed=prep['seed'], mismatch_enabled=prep['mismatch_enabled'], phases=[],
        full3180_status='not run', scope=prep['scope'], cross_run_qualification='not run; separate six-control audit required')
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        first_parameters = None
        for index, temperature in enumerate(prep['temperatures_C']):
            phase = phase_text(log, index)
            before = {tag: read_group(phase, 'P%d_%s_BEFORE' % (index, tag), keys) for tag, keys in prep['groups'].items()}
            after = {tag: read_group(phase, 'P%d_%s_AFTER' % (index, tag), keys) for tag, keys in prep['groups'].items()}
            assert sum(map(len, before.values())) == 3180 and before == after
            if first_parameters is None:
                first_parameters = before
            assert before == first_parameters
            if not prep['mismatch_enabled']:
                assert before == prep['nominal_parameters'], 'Disabled fullvector differs from qualified nominal'
            wave = out/prep['outputs'][index]
            blob, data = load_wave(wave)
            assert data.ndim == 2 and data.shape[1] == 13 and np.isfinite(data).all() and abs(data[-1, 0]-32e-6) < 1e-12
            values = {k: float(v) for k, v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)', phase)}
            assert all(k in values and math.isfinite(values[k]) for k in ['freq', 't_a', 't_b', 't_half_a', 'fout_hi', 'fout_lo'])
            assert values['freq'] > 0 and values['t_b'] > values['t_a']
            vce = float(max(np.abs(data[:, i]-data[:, j]).max() for i, j in [(7, 8), (9, 8), (10, 11), (12, 11)]))
            row = dict(index=index, temperature_C=temperature, parameters_before=before, parameters_after=after,
                wave_rows=len(data), waveform_sha256=hashlib.sha256(blob).hexdigest(), measurements=values,
                t2f_hbt_external_vce_max_V=vce, t2f_hbt_vce_status='passed' if vce <= 1.6 else 'failed')
            result['phases'].append(row)
            assert vce <= 1.6
        result['full3180_status'] = 'passed'
        if not prep['mismatch_enabled']:
            exact = exact_wave(out/'phase0.dat', nominal/'ptat_T12.5.dat')
            result['disabled_nominal_wave_checks'] = exact
            result['disabled_nominal_wave_status'] = 'passed' if all(exact.values()) else 'failed'
            assert all(exact.values()), 'Disabled versus nominal exact waveform comparison failed'
        if len(prep['temperatures_C']) > 1:
            exact = exact_wave(out/'phase0.dat', out/'phase3.dat')
            result['returned25_wave_checks'] = exact
            result['returned25_wave_status'] = 'passed' if all(exact.values()) else 'failed'
            assert all(exact.values()), 'Return waveform exact comparison failed; no numerical-bound substitution'
        result['control_status'] = 'passed'
    except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    for name in prep['outputs']:
        if (out/name).exists():
            archive_new_wave(out/name)
    print(json.dumps({k: v for k, v in result.items() if k not in ['phases', 'warnings']}, indent=2))
    raise SystemExit(0 if result['control_status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
