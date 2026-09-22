#!/usr/bin/env python3
"""Prepare output-only observation replays of two frozen5MHz diagnostics; never simulate."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
from result_directory import allocate_run
from wave_archive import open_wave, wave_sha

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(reference_id, run_id):
    original = SIM / 'qualification' / reference_id
    result, = json.loads((original / 'summary.json').read_text())
    prep = json.loads((original / 'preparation.json').read_text())
    prov = json.loads((original / 'provenance.json').read_text())
    assert result['seed'] == 71002 and result['temperature_C'] in [25., 125.]
    assert result['solver_status'] == 'passed' and result['all27_parameters_exact']
    assert result['nominal_clock_Hz'] == 5000000 and len(result['fingerprints']) == 27
    assert result['fixed_soft_hard_codes'] == [136, 154] and result['shunt_V'] == .0245
    assert all(prov['input_checks'].values())
    case = prep['case']
    old = (original / (case + '.cir')).read_text()
    assert sha(original / (case + '.cir')) == prep['prepared_deck_sha256']
    assert 'XS shp 0 vref iptat isense vped vref_buf vdda 0 g1_sense' in old
    assert 'Xbgr vdda 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr' in old
    deck = old.replace(reference_id, run_id)
    deck, n = re.subn(r'^\.save .+$', lambda m: m[0] + ' v(vped) v(shp)', deck, flags=re.M)
    assert n == 1
    extra = ' v(vref) v(iptat) v(vref_buf) v(vped) v(shp)'
    deck, n = re.subn(r'^wrdata .+$', lambda m: m[0] + extra, deck, flags=re.M)
    assert n == 1
    op = 'echo BIAS_OBSERVATION_OP\nprint v(vref) v(iptat) v(vref_buf) v(vped) v(shp) v(isense) v(xt.icmp) v(xt.vth_soft) v(xt.vth_hard)\necho BIAS_OBSERVATION_OP_END\n'
    deck, n = re.subn(r'^(tran .+)$', lambda m: op + m[0], deck, flags=re.M)
    assert n == 1
    assert deck.count('Vclk clk 0 pulse(0 1.2 20n 0.2n 0.2n 100n 200n)') == 1
    assert deck.count('tran 0.2n 1.02u 0 0.2n') == 1
    with open_wave(original / (case + '.dat')) as stream:
        lines = stream.readlines()
    assert lines and all(len(line.split()) == 13 for line in lines)
    out = allocate_run(SIM, run_id)
    sources = {}
    for name, expected in prep['source_hashes'].items():
        raw = (original / name).read_bytes()
        sources[name] = hashlib.sha256(raw).hexdigest()
        assert sources[name] == expected
        (out / name).write_bytes(raw)
    (out / (case + '.cir')).write_text(deck)
    (out / 'preparer.py').write_text(Path(__file__).read_text())
    diff = ''.join(difflib.unified_diff(old.replace(reference_id, '@RUN@').splitlines(True),
        deck.replace(run_id, '@RUN@').splitlines(True), fromfile='preserved5MHz', tofile='outputOnlyObservation'))
    (out / 'declared_output_difference.diff').write_text(diff)
    preparation = {
        'status': 'prepared only; simulation not run', 'run': run_id, 'reference_run': reference_id,
        'case': case, 'seed': result['seed'], 'temperature_C': result['temperature_C'],
        'shunt_V': result['shunt_V'], 'fixed_soft_hard_codes': result['fixed_soft_hard_codes'],
        'source_hashes': sources, 'prepared_deck_sha256': sha(out / (case + '.cir')),
        'reference_summary_sha256': sha(original / 'summary.json'),
        'reference_provenance_sha256': sha(original / 'provenance.json'),
        'reference_decoded_wave_sha256': wave_sha(original / (case + '.dat')),
        'reference_wave_row_count_including_header': len(lines),
        'expected_runtime_identity': prep['expected_runtime_identity'],
        'expected_observed27_parameters': result['fingerprints'],
        'prospective_sampling': prep['prospective_sampling'],
        'wave_columns': prep['wave_columns'] + ['vref', 'iptat', 'vref_buf', 'vped', 'shp'],
        'prospective_parity': 'Require18finite columns. For every original line including header, extract exactly its prior byte-length prefix from the new line and append the original newline; entire reconstructed13column bytes must equal verified original decoded wave. Additionally require row count and all first13numeric values exactly equal, all27parameters exact, and unchanged runtime/source/deck except declaredoutput changes. Any mismatch fails output-only qualification; no tolerance or alias.',
        'prospective_observations': 'Explicit quiet OP print, initial transient row, each actual clock edge-1ns and edge+20ns; retain original last3cycles/legacy decision policies. Report temperature deltas at like phases forVREF,IPTAT voltage,VREF_BUF,VPED,SHP,ISENSE,ICMP andbothDAC outputs. IPTAT pin voltage is not output current. Algebraic node differences are descriptive, not isolated causal attribution.',
        'unchanged': 'All circuit devices/body connections/models/rail/load/input/temperature per reference/seed/codes/solver/tolerances/integration/maxstep/clock/tstop andparameterprints remain literal unchanged. Onlysave/wrdata and taggedOPprint additions appear in reviewed diff.',
        'planning': {'watchdog_s': 600, 'home_total_growth_budget_GiB': .1,
                     'reference_wall_s': result['wall_s'], 'authorized_candidate_cpu': 5 if result['temperature_C'] == 25 else 10},
        'scope': 'Prepare only pending root source/outputdiff review. No simulator launched. No BGR replacement, no statistical300, no acceptance waiver or isolated causal claim.',
    }
    (out / 'preparation.json').write_text(json.dumps(preparation, indent=2) + '\n')
    return {'run': run_id, 'deck_sha256': preparation['prepared_deck_sha256'],
            'reference_rows': len(lines), 'reference_wall_s': result['wall_s'], 'diff': diff}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.reference, args.run_id), indent=2))
