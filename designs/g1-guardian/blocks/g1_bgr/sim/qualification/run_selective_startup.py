#!/usr/bin/env python3
"""Frozen baseline startup stimuli with selective-loop candidate and terminal exports."""
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDK = Path('/foss/pdks/ihp-sg13g2')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    with path.open() as stream:
        next(stream)
        return [list(map(float, line.split())) for line in stream if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--image-id', required=True)
    args = parser.parse_args()
    source = HERE/'runs/bgr_startup6_20260921_01'
    original = json.loads((source/'manifest.json').read_text())
    candidate = HERE/'candidates/bgr_selective_loop16/bgr_selective_loop16.spice'
    assert sha(candidate) == 'b6810892a4e258bb206af3b6a87c3a046bff4b2b1c4d304e385eacb2765edbed'
    models = {str(path.relative_to(PDK)): sha(path) for path in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))}
    assert models == original['model_sha256'] and (PDK/'COMMIT').read_text().strip() == original['pdk_commit']
    output = HERE/'runs'/args.run_id
    output.mkdir(exist_ok=False)
    shutil.copy(__file__, output/Path(__file__).name)
    shutil.copy(source/'.spiceinit', output/'.spiceinit')
    shutil.copy(candidate, output/'pex_nominal.spice')
    pins = {name: name for name in ['vdd', 'r4', 'vref', 'iptat', 'pbias', 'pcasc', 'vbe', 'dvbe']}
    pins['vss'] = '0'
    node = lambda name: pins.get(name, 'xbgr.'+name)
    devices, all_nodes = [], set()
    for line in candidate.read_text().splitlines():
        fields = line.split()
        if not fields or not fields[0].startswith(('XM', 'XQ')):
            continue
        terminals = dict(zip('dgsb' if fields[0].startswith('XM') else 'cbes', map(node, fields[1:5])))
        devices.append({'instance': fields[0], 'model': fields[5], 'terminals': terminals})
        all_nodes.update(terminals.values())
    nodes = sorted(all_nodes-{'0'})
    manifest = {'command': sys.argv, 'image_id': args.image_id, 'pdk_commit': original['pdk_commit'],
                'ngspice': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
                'model_sha256': models, 'candidate_sha256': sha(candidate),
                'original_manifest_sha256': sha(source/'manifest.json'), 'cases': [],
                'scope': 'Simulation-only candidate with exact original six3.0V startup stimuli and numerical settings. Added terminal exports, no cards modified. Current density/header interpretation and shortHVNMOS3.3/3.6V reliability remain unresolved;3.0V startup cannot clear them.',
                'terminal_nodes': nodes, 'devices': devices}
    save = lambda: (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    save()
    for old in original['cases']:
        assert old['status'] == 'passed' and old['startup'] and old['vdd'] == 3.0
        name = old['name']
        deckpath = source/(name+'.cir')
        assert sha(deckpath) == old['deck_sha256']
        deck = deckpath.read_text()
        assert deck.count('quit') == 1 and deck.count('.control') == 1
        deck = deck.replace('.control\n', '.control\nset num_threads=1\n')
        deck = deck.replace('quit', 'wrdata '+name+'_terminals.dat '+' '.join('v('+value+')' for value in nodes)+'\nquit')
        (output/(name+'.cir')).write_text(deck)
        start = time.monotonic()
        with (output/(name+'.log')).open('w') as log, (output/(name+'.stderr')).open('w') as error:
            try:
                rc = subprocess.run(['ngspice', '-b', name+'.cir'], cwd=output, stdout=log, stderr=error, timeout=300).returncode
                timed = False
            except subprocess.TimeoutExpired:
                rc, timed = None, True
        row = {'name': name, 'original_deck_sha256': sha(deckpath), 'deck_sha256': sha(output/(name+'.cir')),
               'startup': old['startup'], 'vdd': old['vdd'], 'solver_exit': rc, 'timed_out': timed,
               'wall_seconds': time.monotonic()-start, 'status': 'not run' if timed else 'failed',
               'watchdog_seconds': 300}
        try:
            data = read_rows(output/(name+'.dat'))
            terminal_data = read_rows(output/(name+'_terminals.dat'))
            logs = (output/(name+'.log')).read_text()+'\n'+(output/(name+'.stderr')).read_text()
            assert rc == 0 and not timed and len(data) == len(terminal_data) and len(data) > 0
            assert all(len(values) == 12 and all(map(math.isfinite, values)) for values in data)
            assert all(len(values) == len(nodes)+1 and all(map(math.isfinite, values)) for values in terminal_data)
            assert abs(data[-1][0]-3*old['startup'][1]) < 1e-9
            assert not re.search(r'(?im)^Error|Timestep too small|analysis aborted', logs)
            indices = {value: i+1 for i, value in enumerate(nodes)}
            extrema = []
            for device in devices:
                for pair in (['gs', 'gd', 'gb', 'ds', 'db', 'sb'] if device['instance'].startswith('XM') else ['ce', 'be', 'bc']):
                    terminals = [device['terminals'][letter] for letter in pair]
                    differences = [(values[indices[terminals[0]]] if terminals[0] != '0' else 0)-(values[indices[terminals[1]]] if terminals[1] != '0' else 0) for values in terminal_data]
                    extrema.append({'instance': device['instance'], 'model': device['model'], 'pair': pair, 'maximum_absolute_V': max(map(abs, differences)), 'minimum_V': min(differences), 'maximum_V': max(differences)})
            row.update(status='passed', saved_rows=len(data), last_saved_time_s=data[-1][0],
                       vref_end_V=data[-1][1], iptat_end_A=data[-1][2], current_peak_A=max(-values[3] for values in data),
                       startup_level_status='passed' if .9 < data[-1][1] < 1.2 and data[-1][2] > 1e-6 else 'failed',
                       hbt_external_vce_status='passed' if all(values['maximum_absolute_V'] <= 1.6 for values in extrema if values['pair'] == 'ce') else 'failed',
                       external_terminal_extrema=extrema, waveform_sha256=sha(output/(name+'.dat')))
            limits = {'gs': 3.0, 'gd': 3.0, 'gb': 3.0, 'ds': 3.0, 'db': 1.6, 'sb': 1.6}
            row['HV_literal_model_parameter_exceedances'] = [values for values in extrema if values['instance'].startswith('XM') and values['maximum_absolute_V'] > limits[values['pair']]+1e-9]
            row['short_HV_NMOS_VGS_max_V'] = {values['instance']: values['maximum_absolute_V'] for values in extrema if values['instance'] in ['XM29', 'XM31', 'XM32', 'XM33'] and values['pair'] == 'gs'}
            row['HV_model_scope'] = 'Literal PSP defaults only, not foundry reliability sign-off. Original L0.5um NMOS concerns at3.3/3.6V remain; this3.0V fixture cannot resolve them.'
        except (OSError, ValueError, AssertionError, IndexError) as error:
            row['analysis_error'] = str(error)
        manifest['cases'].append(row)
        save()
        print(json.dumps({key: value for key, value in row.items() if key not in ['external_terminal_extrema', 'HV_literal_model_parameter_exceedances']}), flush=True)


if __name__ == '__main__':
    main()
