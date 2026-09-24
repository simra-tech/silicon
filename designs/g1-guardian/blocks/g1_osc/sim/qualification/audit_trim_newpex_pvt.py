#!/usr/bin/env python3
"""Saved-only exact 80-leaf new-CPEX five-tuple trim audit; no solver."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import run_trim_newpex_pvt as protocol

HERE = Path(__file__).resolve().parent
RUN_PREFIX = 'osc_r095_newpex_pvt80_20260924_r1_shard'
QUAL = HERE/'runs/osc_r095_newpex_qual_20260924_r1/manifest.json'
QUAL_ANALYSIS = HERE/'runs/osc_r095_newpex_qual_20260924_r1/analysis.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def log_measurements(path):
    text = Path(path).read_text(errors='replace')
    values = {key:float(value) for key,value in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)',text)}
    return values, not re.search(r'(?im)^Error|Timestep too small|analysis aborted',text)


def audit_case(folder, row, index, code, template):
    name, expected_deck = protocol.deck_for(template, 'osc.spice', protocol.TUPLES[index], code)
    deck, wave, log = folder/(name+'.cir'), folder/(name+'.dat'), folder/(name+'.log')
    checks = {
        'case_identity': row['name'] == name and row['tuple_index'] == index and row['code'] == code,
        'tuple_identity': tuple(row[k] for k in ('mos','res','cap','vdd','temp')) == protocol.TUPLES[index],
        'source_deck_exact': deck.is_file() and deck.read_text() == expected_deck and sha(deck) == row['deck_sha256'],
        'watchdog_original': row['watchdog_seconds'] == 300 and row['tstop_us'] == 6,
        'numerical': row['status'] == 'passed' and row['solver_exit'] == 0 and row['timed_out'] is False,
        'wave_complete_finite': protocol.wave_valid(wave),
        'wave_hash': wave.is_file() and sha(wave) == row['waveform_sha256'],
    }
    if log.is_file():
        measures, clean = log_measurements(log)
    else:
        measures, clean = {}, False
    checks['log_clean'] = bool(clean)
    checks['measurements_exact'] = (measures == row['measurements'] and
                                    all(k in measures and math.isfinite(measures[k])
                                        for k in ('fmhz','duty','t1','t2','th1')))
    if checks['measurements_exact']:
        checks['widths_exact'] = (row.get('high_width_s') == measures['th1']-measures['t1'] and
                                  row.get('low_width_s') == (measures['t2']-measures['t1'])/10-
                                  (measures['th1']-measures['t1']))
    else:
        checks['widths_exact'] = False
    return {'tuple_index':index,'code':code,'name':name,'status':'passed' if all(checks.values()) else 'failed',
            'checks':checks,'frequency_MHz':measures.get('fmhz'),
            'duty_percent':measures.get('duty'), 'deck_sha256':sha(deck) if deck.is_file() else None,
            'waveform_sha256':sha(wave) if wave.is_file() else None,
            'wall_seconds':row['wall_seconds']}


def derive():
    qualification = read(QUAL)
    qualified = read(QUAL_ANALYSIS)
    assert qualified['status'] == 'passed' and qualified['completed_cases'] == 9
    assert qualified['timeout_cases'] == 0 and all(qualified['qualification_checks'].values())
    assert qualification['source_sha256']['baseline.spice'] == protocol.PEX_SHA
    assert qualification['source_kind'].startswith('new physical OSC R0.95 CPEX')
    assert qualification['pdk_commit'] == protocol.PDK_COMMIT
    assert qualification['image_id'] == protocol.IMAGE_ID
    template_path = HERE.parent/'postlayout/tb_osc_pex.cir'
    template = template_path.read_text()
    manifests, cases = {}, {}
    for shard in range(4):
        folder = HERE/'runs'/(RUN_PREFIX+str(shard))
        manifest_path = folder/'manifest.json'
        manifest = read(manifest_path)
        manifests[str(shard)] = sha(manifest_path)
        assert manifest['source_kind'] == 'new physical OSC R0.95 CPEX; no additional resistor scaling'
        assert manifest['pex_sha256'] == protocol.PEX_SHA and sha(folder/'osc.spice') == protocol.PEX_SHA
        assert manifest['runner_sha256'] == sha(HERE/'run_trim_newpex_pvt.py') == sha(folder/'run_trim_newpex_pvt.py')
        assert manifest['template_sha256'] == sha(template_path)
        assert manifest['spiceinit_sha256'] == sha(folder/'.spiceinit') == sha(HERE.parent/'.spiceinit')
        assert manifest['image_id'] == protocol.IMAGE_ID and manifest['pdk_commit'] == protocol.PDK_COMMIT
        assert manifest['models_sha256'] == qualification['model_sha256']
        assert manifest['shards'] == 4 and manifest['shard_index'] == shard
        assert manifest['expected_cases'] == [{'tuple_index':i,'code':c} for i,c in protocol.positions(shard)]
        assert len(manifest['cases']) <= 20
        for row in manifest['cases']:
            key = (row['tuple_index'],row['code'])
            assert key in protocol.positions(shard) and key not in cases
            cases[key] = audit_case(folder, row, key[0], key[1], template)
    tuples = []
    for index, condition in enumerate(protocol.TUPLES):
        rows = [cases.get((index, code), {'tuple_index':index,'code':code,'status':'not run'}) for code in range(16)]
        complete = all(row['status'] == 'passed' for row in rows)
        frequencies = [row['frequency_MHz'] for row in rows] if complete else []
        tuples.append({'condition':condition,'cases':rows,
                       'numerical_status':'passed' if complete else 'failed or not run',
                       'strictly_decreasing_all16':all(a > b for a,b in zip(frequencies,frequencies[1:])) if complete else None,
                       'brackets_10MHz':min(frequencies) <= 10 <= max(frequencies) if complete else None,
                       'nearest_code_error_percent':min((100*(f/10-1) for f in frequencies),key=abs) if complete else None})
    result = {'status':'passed' if len(cases) == 80 and all(row['numerical_status'] == 'passed' and
              row['strictly_decreasing_all16'] and row['brackets_10MHz'] for row in tuples) else 'failed or not run',
              'expected_leaves':80,'attempted_leaves':len(cases),
              'passed_numerical_leaves':sum(row['status'] == 'passed' for row in cases.values()),
              'not_run_leaves':80-len(cases),'manifest_sha256':manifests,
              'physical_cpex_sha256':protocol.PEX_SHA,
              'qualified_newpex_manifest_sha256':sha(QUAL),
              'qualified_newpex_analysis_sha256':sha(QUAL_ANALYSIS),
              'runner_sha256':sha(HERE/'run_trim_newpex_pvt.py'),
              'auditor_sha256':sha(__file__), 'tuples':tuples,
              'scope':'Only five selected PVT tuples/all16 codes, mismatch disabled, 50fF stand-in on exact new physical CPEX. Not full Cartesian PVT, actual receiver/fullchip route, physical jitter or measured yield.'}
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists()
    result = derive()
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'tuples'}, indent=2))


if __name__ == '__main__':
    main()
