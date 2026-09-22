#!/usr/bin/env python3
"""Repeat exact retained fixtures with additional external-device node export.
Literal model parameter comparisons are not a foundry reliability sign-off.
"""
import argparse, hashlib, json, math, re, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDK = Path('/foss/pdks/ihp-sg13g2')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--source-run', required=True)
    ap.add_argument('--image-id', required=True)
    ap.add_argument('--cases', help='Comma-separated retained case names; default all')
    ap.add_argument('--stop-file', type=Path)
    args = ap.parse_args()
    source = HERE/'runs'/args.source_run
    original = json.loads((source/'manifest.json').read_text())
    out = HERE/'runs'/args.run_id
    out.mkdir(exist_ok=False)
    shutil.copy(__file__, out/Path(__file__).name)
    for path in source.iterdir():
        if path.suffix == '.spice' or path.name == '.spiceinit':
            shutil.copy(path, out/path.name)
    netlist = (out/'pex_nominal.spice').read_text()
    pins = {'vdd':'vdd', 'vss':'0', 'r4':'r4', 'vref':'vref', 'iptat':'iptat',
            'pbias':'pbias', 'pcasc':'pcasc', 'vbe':'vbe', 'dvbe':'dvbe'}
    node = lambda n: pins.get(n, 'xbgr.'+n)
    devices = []
    all_nodes = set()
    for line in netlist.splitlines():
        p = line.split()
        if not p:
            continue
        if p[0].startswith('XM'):
            labels, pairs = 'dgsb', ['gs', 'gd', 'gb', 'ds', 'db', 'sb']
        elif p[0].startswith('XQ'):
            labels, pairs = 'cbes', ['ce', 'be', 'bc', 'cs', 'bs', 'es']
        elif p[0].startswith('XR'):
            labels, pairs = 'pns', ['pn', 'ps', 'ns']
        else:
            continue
        terminals = dict(zip(labels, map(node, p[1:1+len(labels)])))
        all_nodes.update(terminals.values())
        devices.append({'instance':p[0], 'model':p[1+len(labels)], 'terminals':terminals, 'pairs':pairs})
    nodes = sorted(all_nodes-{'0'})
    selected = [c for c in original['cases'] if not args.cases or c['name'] in args.cases.split(',')]
    assert selected and all(c['status']=='passed' for c in selected)
    model_paths = ['sg13g2_moshv_mod.lib', 'sg13g2_moshv_parm.lib', 'sg13g2_hbt_mod.lib']
    for name in model_paths:
        shutil.copy(PDK/'libs.tech/ngspice/models'/name, out/name)
    manifest = {'command':sys.argv, 'image_id':args.image_id,
                'pdk_commit':(PDK/'COMMIT').read_text().strip(),
                'ngspice':subprocess.check_output(['ngspice','--version'], text=True),
                'source_run':args.source_run, 'source_manifest_sha256':sha(source/'manifest.json'),
                'model_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},
                'model_parameter_screen':{'HV_MOS_absolute_V':{'gs':3.0,'gd':3.0,'gb':3.0,'ds':3.0,'db':1.6,'sb':1.6},
                                          'HBT_absolute_ce_V':1.6, 'model_default_SWSOA':0},
                'limitations':'External subcircuit terminal voltages only. Literal PSP MAX comparisons are a diagnostic, not an adopted foundry reliability limit; SWSOA defaults0. HBT VBE model-header range is not generalized to all temperatures. Internal intrinsic model nodes, model validity/current density, all chip loads and lifetime remain separate.',
                'node_order':nodes, 'devices':devices, 'cases':[]}
    save = lambda:(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    save()
    for old in selected:
        if args.stop_file and args.stop_file.exists():
            manifest['campaign_status']='paused at requested leaf boundary'
            break
        name=old['name']
        deck=(source/(name+'.cir')).read_text()
        assert deck.count('quit') == 1
        if 'set num_threads=1' not in deck:
            deck=deck.replace('.control\n','.control\nset num_threads=1\n')
        if '\nop\n' in deck:
            deck=deck.replace('\nop\n', '\nop\n'+f'wrdata {name}_initial_op.dat '+' '.join('v('+n+')' for n in nodes)+'\n', 1)
        deck=deck.replace('quit', f'wrdata {name}_terminals.dat '+' '.join('v('+n+')' for n in nodes)+'\nquit')
        (out/(name+'.cir')).write_text(deck)
        start=time.monotonic()
        with (out/(name+'.log')).open('w') as log, (out/(name+'.stderr.log')).open('w') as err:
            try:
                rc=subprocess.run(['ngspice','-b',name+'.cir'],cwd=out,stdout=log,stderr=err,timeout=old['watchdog_seconds']).returncode
                timed=False
            except subprocess.TimeoutExpired:
                rc=None;timed=True
        row={'name':name,'source_deck_sha256':sha(source/(name+'.cir')),'deck_sha256':sha(out/(name+'.cir')),
             'solver_exit':rc,'timed_out':timed,'wall_seconds':time.monotonic()-start,'status':'not run' if timed else 'failed'}
        try:
            with (out/(name+'_terminals.dat')).open() as f:
                next(f); data=[list(map(float,line.split())) for line in f if line.strip()]
            logs=(out/(name+'.log')).read_text()+'\n'+(out/(name+'.stderr.log')).read_text()
            original_match=sha(source/(name+'.dat'))==sha(out/(name+'.dat'))
            row['original_vectors_byte_identical']=original_match
            if rc==0 and data and all(len(r)==len(nodes)+1 and all(map(math.isfinite,r)) for r in data) and original_match and not re.search(r'(?im)^Error|analysis aborted|Timestep too small',logs):
                row['status']='passed'
                row['point_count']=len(data)
                row['external_terminal_extrema']=[]
                row['literal_model_parameter_exceedances']=[]
                for device in devices:
                    for pair in device['pairs']:
                        an,bn=[device['terminals'][x] for x in pair]
                        ai,bi=[nodes.index(n)+1 if n!='0' else None for n in [an,bn]]
                        values=[((r[ai] if ai else 0)-(r[bi] if bi else 0),r[0]) for r in data]
                        v,x=max(values,key=lambda v:abs(v[0]))
                        record={'instance':device['instance'],'model':device['model'],'pair':pair,
                                'minimum_V':min(v[0] for v in values),'maximum_V':max(v[0] for v in values),
                                'maximum_absolute_V':abs(v),'at_saved_axis':x}
                        limit=None
                        if device['instance'].startswith('XM'):limit=manifest['model_parameter_screen']['HV_MOS_absolute_V'][pair]
                        if device['instance'].startswith('XQ') and pair=='ce':limit=1.6
                        if limit is not None:
                            record['literal_model_parameter_V']=limit
                            record['exceeds_literal_model_parameter']=abs(v)>limit+1e-9
                            if record['exceeds_literal_model_parameter']:row['literal_model_parameter_exceedances'].append(record)
                        row['external_terminal_extrema'].append(record)
                row['hbt_vce_status']='failed' if any(r['instance'].startswith('XQ') for r in row['literal_model_parameter_exceedances']) else 'passed'
        except (OSError,ValueError,IndexError,StopIteration) as exc:
            row['analysis_error']=str(exc)
        manifest['cases'].append(row);save()
        print(json.dumps({k:v for k,v in row.items() if k not in ['external_terminal_extrema','literal_model_parameter_exceedances']}),flush=True)
    manifest['not_run_cases']=[c['name'] for c in selected if c['name'] not in [r['name'] for r in manifest['cases']]]
    save()


if __name__=='__main__':
    main()
