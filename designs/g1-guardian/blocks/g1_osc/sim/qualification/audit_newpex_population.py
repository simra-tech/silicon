#!/usr/bin/env python3
"""Saved-only audit of fixed, newly extracted OSC population campaigns."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_NAMES = ('baseline.spice', 'mismatch.spice', 'disabled.spice', '.spiceinit')
CAMPAIGNS = {
    'nominal100': (63101, 63200, (0, 15), 'nominal', 'osc_r095_newpex_qual_20260924_r1'),
    'all16': (63301, 63320, tuple(range(16)), 'nominal', 'osc_r095_newpex_qual_20260924_r1'),
    'adverse100': (62001, 62100, (0, 15), 'slowhot', 'osc_r095_newpex_slowhot_qual_20260924_r1'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wave_complete(path):
    if not path.is_file():
        return False
    count, previous, last = 0, None, None
    try:
        with path.open() as stream:
            if stream.readline().split() != ['time', 'v(osc_clk)', 'i(vdd)', 'v(x1.va)', 'v(x1.vb)']:
                return False
            for line in stream:
                parts = line.split()
                if len(parts) != 5:
                    return False
                values = [float(value) for value in parts]
                if not all(math.isfinite(value) for value in values):
                    return False
                time = values[0]
                if previous is not None and time <= previous:
                    return False
                if previous is None and abs(time) > 1e-15:
                    return False
                previous, last = time, values
                count += 1
    except (OSError, ValueError, OverflowError):
        return False
    return count >= 1000 and last is not None and abs(last[0]-6e-6) < 1e-12


def log_matches(path, stderr_path, row):
    if not path.is_file() or not stderr_path.is_file():
        return False
    log = path.read_text(errors='replace')
    stderr = stderr_path.read_text(errors='replace')
    if re.search(r'(?im)^Error|no such parameter|Timestep too small|analysis aborted', log+'\n'+stderr):
        return False
    fingerprints = re.findall(r'@[^\s]+\s*=\s*([-+0-9.eE]+)', log)
    measurements = {key: float(value) for key, value in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)', log)}
    return fingerprints == row['fingerprints'] and measurements == row['measurements'] and all(math.isfinite(value) for value in measurements.values())


def expected_deck(row, parameters):
    template = (HERE.parent/'postlayout/tb_osc_pex.cir').read_text()
    values = {'MOS': 'mos_'+row['mos']+'_mismatch', 'RES': 'res_'+row['res']+'_mismatch',
              'CAP': 'cap_'+row['cap']+'_mismatch', 'VDD': row['vdd'], 'TEMP': row['temperature_C']}
    values.update({'B'+str(i): (row['code'] >> i) & 1 for i in range(4)})
    for key, value in values.items():
        template = template.replace('@@'+key+'@@', str(value))
    template = template.replace('.include postlayout/g1_osc_pex.spice', '.include mismatch.spice')
    template = template.replace('.option rshunt=1e12', '.option seed=%d rshunt=1e12' % row['seed'])
    prints = ''.join('print '+parameter+'\n' for parameter in parameters)
    control = 'set num_threads=1\nset filetype=ascii\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\nop\n'+prints
    template = template.replace('set filetype=ascii\n', control)
    template = template.replace('tran 0.2n 3.3u', 'tran 0.2n 6u\n'+prints)
    template = template.replace('.endc', 'print fmhz duty iua\nwrdata %s.dat v(osc_clk) i(vdd) v(x1.va) v(x1.vb)\nquit\n.endc' % row['name'])
    return template


def audit(campaign):
    first, last, codes, corner, qualification_id = CAMPAIGNS[campaign]
    qdir = HERE/'runs'/qualification_id
    qpath = qdir/'manifest.json'
    qanalysis = qdir/'analysis.json'
    if not qpath.is_file() or not qanalysis.is_file():
        raise ValueError('Exact-corner nine-case qualification is not run')
    q, qa = json.loads(qpath.read_text()), json.loads(qanalysis.read_text())
    assert qa['status'] == 'passed' and qa['manifest_sha256'] == sha(qpath)
    assert qa['completed_cases'] == qa['expected_cases'] == 9 and qa['timeout_cases'] == 0
    assert all(qa['qualification_checks'].values()) and len(qa['qualification_checks']) >= 12
    assert len(q['fingerprint_parameters']) == 269
    assert all(sha(qdir/name) == q['source_sha256'][name] for name in SOURCE_NAMES)
    expected_tuple = ('tt', 'typ', 'typ', 1.2, 27) if corner == 'nominal' else ('ss', 'wcs', 'wcs', 1.08, 125)
    results, fingerprints = [], []
    for seed in range(first, last+1):
        run_id = 'osc_r095_newpex_%s_20260924_r1_s%d' % (campaign, seed)
        folder = HERE/'runs'/run_id
        path = folder/'manifest.json'
        if not path.is_file():
            results.append({'seed': seed, 'status': 'not run'})
            continue
        m = json.loads(path.read_text())
        rows = m['cases']
        checks = {
            'source': all(m['source_sha256'].get(name) == q['source_sha256'][name] and sha(folder/name) == q['source_sha256'][name] for name in SOURCE_NAMES),
            'runner': m['source_sha256'].get('run_mc_newpex_population.py') == sha(HERE/'run_mc_newpex_population.py') == sha(folder/'run_mc_newpex_population.py'),
            'environment': all(m[key] == q[key] for key in ('image_id', 'ngspice', 'pdk_commit', 'model_sha256', 'fingerprint_parameters')),
            'cases': m['expected_cases'] == ['s%d_c%d' % (seed, code) for code in codes] and len(rows) == len(codes) and [r['code'] for r in rows] == list(codes),
            'numeric': len(rows) == len(codes) and all(r['status'] == 'passed' and r['solver_exit'] == 0 and not r['timed_out'] for r in rows),
            'conditions': all((r['mos'], r['res'], r['cap'], r['vdd'], r['temperature_C']) == expected_tuple and r['seed'] == seed and r['mm'] is True and r['op_only'] is False for r in rows),
            'decks': all((folder/(r['name']+'.cir')).is_file() and sha(folder/(r['name']+'.cir')) == r['deck_sha256'] and (folder/(r['name']+'.cir')).read_text() == expected_deck(r, m['fingerprint_parameters']) for r in rows),
            'waves': all(wave_complete(folder/(r['name']+'.dat')) for r in rows),
            'logs': all(log_matches(folder/(r['name']+'.log'), folder/(r['name']+'.stderr'), r) for r in rows),
        }
        fp = [r['fingerprints'] for r in rows]
        checks['frozen_parameters'] = bool(fp) and all(len(f) == 538 and f[:269] == fp[0][:269] == f[269:] and all(math.isfinite(float(v)) for v in f) for f in fp)
        complete = all(checks.values())
        frequencies = [r['measurements'].get('fmhz') for r in rows]
        checks['finite_frequency'] = complete and all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in frequencies)
        complete = all(checks.values())
        if complete:
            fingerprints.append(tuple(fp[0][:269]))
        results.append({'seed': seed, 'status': 'passed' if complete else 'failed', 'checks': checks, 'manifest_sha256': sha(path),
                        'frequency_MHz': frequencies if complete else None,
                        'brackets_10MHz': min(frequencies) <= 10 <= max(frequencies) if complete else None,
                        'strict_monotonic_all16': all(a > b for a, b in zip(frequencies, frequencies[1:])) if complete and len(codes) == 16 else None,
                        'numerical_failures': sum(r['status'] != 'passed' for r in rows),
                        'timeouts': sum(r['timed_out'] for r in rows),
                        'waveform_sha256': {r['name']: sha(folder/(r['name']+'.dat')) for r in rows if (folder/(r['name']+'.dat')).is_file()}})
    return {'campaign': campaign, 'qualification_id': qualification_id, 'qualification_manifest_sha256': sha(qpath),
            'expected_seeds': [first, last], 'codes': codes, 'expected_samples': last-first+1,
            'completed_samples': sum(r['status'] == 'passed' for r in results),
            'failed_samples': sum(r['status'] == 'failed' for r in results),
            'not_run_samples': sum(r['status'] == 'not run' for r in results),
            'distinct_fingerprints': len(set(fingerprints)),
            'bracket_failures': sum(r.get('brackets_10MHz') is False for r in results),
            'monotonicity_failures': sum(r.get('strict_monotonic_all16') is False for r in results),
            'monotonicity_not_run': sum(r.get('strict_monotonic_all16') is None for r in results),
            'samples': results,
            'scope': 'New physical CPEX source only, 50 fF ideal load. No old-source population credit, actual receiver/integration claim, or silicon yield claim.'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--campaign', choices=CAMPAIGNS, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise ValueError('Refusing to overwrite an audit')
    result = audit(args.campaign)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'samples'}, indent=2))


if __name__ == '__main__':
    main()
