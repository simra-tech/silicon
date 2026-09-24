#!/usr/bin/env python3
"""Bounded, source-frozen focused interface context study; no broad chip PEX."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import atomic_json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--image-id', required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = [HERE/name for name in ['prepare_interface_clip.py', 'run_fill_clip_pex.py',
               'analyze_fill_clip.py', 'check_fill_clip_ac.py', 'export_clip_lvsdb.lvs']]
    sources += [Path(__file__), ROOT/'designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds']
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in sources}
    for path in sources[:-1]:
        shutil.copyfile(path, args.output/path.name)
    tasks = [(pair, width) for pair in ['isense_clock', 'vref_dac', 'vrefbuf_dac', 'iptat_isense']
             for width in [12, 24, 48] if (pair, width) != ('isense_clock', 12)]
    record = dict(status='not run', image_id=args.image_id, source_sha256=frozen, cases=[],
                  clip_length_um=20, relative_context_tolerance=0.01,
                  prior_pilot='interface-isense-clock-w12-20260922-r1',
                  scope='Focused delivered-GDS capacitor clips only. Context24to48 comparison uses prospectively declared1percent relative limit for all2x2 matrix entries. No longitudinal/full-route convergence or actual-source electrical acceptance implied.')
    atomic_json(args.output/'manifest.json', record)
    for pair, width in tasks:
        assert all(sha(ROOT/name) == value for name, value in frozen.items()), 'source changed during batch'
        leaf = args.output/('%s_w%d' % (pair, width))
        leaf.mkdir()
        commands = [
            [sys.executable, str(HERE/'prepare_interface_clip.py'), '--pair', pair, '--context-um', str(width),
             '--expected-sha256', frozen['designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds'], '--output', str(leaf/'clip')],
            [sys.executable, str(HERE/'run_fill_clip_pex.py'), '--clip', str(leaf/'clip'), '--output', str(leaf/'pex')],
            [sys.executable, str(HERE/'analyze_fill_clip.py'), '--input', str(leaf/'pex'), '--output', str(leaf/'analysis')],
            [sys.executable, str(HERE/'check_fill_clip_ac.py'), str(leaf/'analysis')],
        ]
        item = dict(pair=pair, context_um=width, status='not run', steps=[])
        record['cases'].append(item)
        for index, command in enumerate(commands):
            with (leaf/('step%d.log' % index)).open('x') as log:
                try:
                    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=540)
                    code = result.returncode
                except subprocess.TimeoutExpired:
                    code = 124
            item['steps'].append(dict(command=[s.replace(str(ROOT)+'/', '') for s in command], returncode=code))
            if code != 0:
                item['status'] = record['status'] = 'failed'
                atomic_json(args.output/'manifest.json', record)
                raise SystemExit(1)
            if index == 1:
                extract = json.loads((leaf/'pex/manifest.json').read_text())
                assert len(extract) == 2 and all(r.get('extract_returncode') == 0 and r.get('kpex_returncode') == 0
                                                and r.get('extract_status') == 'completed' and r.get('kpex_status') == 'completed'
                                                for r in extract), 'child completion failed despite wrapper exit'
            atomic_json(args.output/'manifest.json', record)
        item['status'] = 'passed'
        item['analysis_sha256'] = sha(leaf/'analysis/summary.json')
        atomic_json(args.output/'manifest.json', record)
        print(json.dumps(item), flush=True)
    record['context_checks'] = []
    for pair in ['isense_clock', 'vref_dac', 'vrefbuf_dac', 'iptat_isense']:
        data = [json.loads((args.output/('%s_w%d' % (pair, width))/'analysis/summary.json').read_text())
                for width in [24, 48]]
        errors = {}
        for variant in ['no_fill', 'actual_fill']:
            for mode in ['grounded', 'floating']:
                matrices = [d['results'][variant]['modes'][mode]['matrix_fF'] for d in data]
                errors[variant+'_'+mode] = max(abs(matrices[0][i][j]-matrices[1][i][j])/abs(matrices[1][i][j])
                                              for i in range(2) for j in range(2))
        record['context_checks'].append(dict(pair=pair, relative_matrix_errors=errors,
                                            status='passed' if max(errors.values()) <= 0.01 else 'failed'))
    record['status'] = 'passed' if all(r['status'] == 'passed' for r in record['context_checks']) else 'failed'
    atomic_json(args.output/'manifest.json', record)
    if record['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
