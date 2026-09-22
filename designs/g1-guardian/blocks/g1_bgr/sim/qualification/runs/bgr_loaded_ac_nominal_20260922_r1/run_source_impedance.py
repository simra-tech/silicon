#!/usr/bin/env python3
"""Bounded loaded VREF/IPTAT AC, with explicit zero-DC probe equivalence."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
BLOCKS = HERE.parents[2]
PDK = Path('/foss/pdks/ihp-sg13g2')
ANCHOR = BLOCKS/'g1_trip/sim/qualification/dac-actualbgr-reset-klu-pilot-20260922-a'
TUPLES = {'nominal': ('tt', 'typ', 25, 3.3, 1.2),
          'slowcold': ('ss', 'wcs', -40, 3.0, 1.08),
          'fasthot': ('ff', 'bcs', 125, 3.6, 1.32)}
NODES = ['vref', 'iptat', 'vref_buf', 'isense', 'vped', 'pbias', 'pcasc',
         'xt.icmp', 'xt.vth_soft', 'xt.vth_hard']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--image-id', required=True)
    parser.add_argument('--tuple', choices=sorted(TUPLES), default='nominal')
    args = parser.parse_args()
    out = HERE/'runs'/args.run_id
    out.mkdir(exist_ok=False)
    sources = {'bgr.spice': HERE/'runs/bgr_noise_20260921_01/pex.spice',
               'sense.spice': ANCHOR/'sense.spice', 'trip.spice': ANCHOR/'trip.spice',
               '.spiceinit': HERE/'.spiceinit'}
    assert sha(sources['bgr.spice']) == '72417e072003d2ce28a108c47ef6ac86927ce6c6f89f3a614f360165a31c9d77'
    for name, path in sources.items():
        shutil.copy(path, out/name)
    shutil.copy(__file__, out/Path(__file__).name)
    shutil.copy(HERE/'SOURCE_IMPEDANCE_PLAN_20260922.md', out/'prospective_plan.md')
    mos, passive, temp, analog, digital = TUPLES[args.tuple]
    # Reuse the exact reset-held full chain executable topology. Changes are
    # enumerated: local frozen includes, nominal corners, rails/temp/codes,
    # baseline nominal BGR source, save/control and zero-DC instrumentation.
    template = (ANCHOR/'seed51001.cir').read_text().split('.control')[0]
    template = re.sub(r'(?m)^\.save .*\n', '', template)
    template = re.sub(r'(?m)^\.include .*?/(sense|trip|bgr)\.spice$', r'.include \1.spice', template)
    template = template.replace('_mismatch', '')
    template = template.replace('mos_tt', 'mos_'+mos).replace('res_typ', 'res_'+passive).replace('cap_typ', 'cap_'+passive)
    template = template.replace('hbt_typ', 'hbt_'+('typ' if mos == 'tt' else ('wcs' if mos == 'ss' else 'bcs')))
    template = template.replace('.temp 25', '.temp '+str(temp)).replace('.param VDDA=3.3 VDD=1.2 VREF=1.04', '.param VDDA=%s VDD=%s VREF=1.04'%(analog, digital))
    template = re.sub(r'(?m)^(V[sh][0-7] \S+ 0 dc )1\.2$', r'\g<1>'+str(digital), template)
    # Header comments are corrected rather than masquerading as a clocked test.
    template = '* Frozen loaded BGR stationary source-impedance fixture\n'+template[template.index('.param'):]
    manifest = {'command': sys.argv, 'image_id': args.image_id, 'tuple': args.tuple,
                'pdk_commit': (PDK/'COMMIT').read_text().strip(),
                'ngspice': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
                'source_sha256': {name: sha(out/name) for name in sources},
                'anchor_deck_sha256': sha(ANCHOR/'seed51001.cir'),
                'runner_sha256': sha(Path(__file__)), 'prospective_plan_sha256': sha(out/'prospective_plan.md'),
                'model_sha256': {str(p.relative_to(PDK)): sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},
                'osdi_sha256': {str(p.relative_to(PDK)): sha(p) for p in sorted((PDK/'libs.tech/ngspice/osdi').glob('*.osdi'))},
                'conditions': {'analog_V': analog, 'digital_V': digital, 'temperature_C': temp, 'shunt_V': .025, 'soft_code': 153, 'hard_code': 254, 'clock': 'both comparators held reset', 'models': 'nominal, not archived seed51001 mismatch replay'},
                'limitations': ['Loaded driving point, not unloaded source impedance', 'T2F/periodic oscillator load not run', 'SENSE/TRIP schematic, baseline BGR capacitance-only PEX', 'No new layout/coupling/adoption acceptance', 'Short-channel BGR HV model-scope issue remains'],
                'cases': [], 'status': 'not run'}
    save = lambda: (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    save()
    reference_op = None
    for case in ['control', 'vref', 'iptat']:
        body = template
        probes = case != 'control'
        if probes:
            body = body.replace('Xbgr vdda 0 r4 vref iptat ', 'Xbgr bgr_supply 0 r4 bgr_vref bgr_iptat ')
            body += '\nVsupply vdda bgr_supply 0\nVsref bgr_vref vref 0\nVsptat bgr_iptat iptat 0\nIprobe 0 %s dc 0 ac 1\n'%case
        op_vectors = ['v('+node+')' for node in NODES]+['i(vdda)']
        vectors = op_vectors+(['i(vsupply)', 'i(vsref)', 'i(vsptat)'] if probes else [])
        body += '.save '+' '.join(vectors)+'\n.control\nset num_threads=1\nset numdgt=15\nset wr_vecnames\nset wr_singlescale\nop\n'
        body += 'wrdata %s_op.dat %s\n'%(case, ' '.join(vectors))
        if probes:
            body += 'ac dec 50 .1 100Meg\n'
            # Real columns prevent ambiguous complex wrdata layout.
            expressions = []
            for index, vector in enumerate(vectors):
                body += 'let r%d = real(%s)\nlet j%d = imag(%s)\n'%(index, vector, index, vector)
                expressions += ['r%d'%index, 'j%d'%index]
            body += 'wrdata %s_ac.dat %s\n'%(case, ' '.join(expressions))
        body += 'quit\n.endc\n.end\n'
        (out/(case+'.cir')).write_text(body)
        timeout = 300 if probes else 120
        start = time.monotonic()
        with (out/(case+'.log')).open('w') as log, (out/(case+'.stderr')).open('w') as error:
            try:
                rc = subprocess.run(['ngspice', '-b', case+'.cir'], cwd=out, stdout=log, stderr=error, timeout=timeout).returncode
                timed = False
            except subprocess.TimeoutExpired:
                rc, timed = None, True
        row = {'name': case, 'status': 'failed', 'solver_exit': rc, 'timed_out': timed,
               'watchdog_seconds': timeout, 'wall_seconds': time.monotonic()-start,
               'deck_sha256': sha(out/(case+'.cir')), 'checks': {}, 'op_vectors': vectors}
        try:
            text = (out/(case+'.log')).read_text()+'\n'+(out/(case+'.stderr')).read_text()
            assert rc == 0 and not timed and not re.search(r'(?im)^Error|no such vector|no such parameter|analysis aborted|Timestep too small', text)
            op = np.atleast_2d(np.loadtxt(str(out/(case+'_op.dat')), skiprows=1))
            assert op.shape == (1, len(vectors)+1) and np.isfinite(op).all()
            values = op[0, 1:]
            row['op'] = dict(zip(vectors, map(float, values)))
            row['checks']['functional_op'] = bool(.9 < values[0] < 1.2 and 0 < values[1] < 1.5 and .9 < values[2] < 1.2 and values[10] < 0)
            if reference_op is None:
                reference_op = values
            else:
                delta = np.abs(values[:len(reference_op)]-reference_op)
                row['dc_equivalence'] = {'max_node_delta_V': float(delta[:10].max()), 'analog_current_delta_A': float(delta[10]), 'criteria_V': 1e-6, 'criteria_A': 1e-9}
                row['checks']['dc_equivalence'] = bool(delta[:10].max() <= 1e-6 and delta[10] <= 1e-9)
                row['checks']['source_current_positive'] = bool(row['op']['i(vsupply)'] > 0 and row['op']['i(vsptat)'] > 0)
                data = np.loadtxt(str(out/(case+'_ac.dat')), skiprows=1)
                assert data.shape == (451, 1+2*len(vectors)) and np.isfinite(data).all()
                assert np.allclose(data[:, 0], np.logspace(-1, 8, 451), rtol=1e-12, atol=1e-12)
                row['checks']['complete_finite_ac_grid'] = True
                nodeindex = NODES.index(case)
                z = data[:, 1+2*nodeindex]+1j*data[:, 2+2*nodeindex]
                row['loaded_impedance_ohm'] = {'max_magnitude': float(np.abs(z).max()), 'peak_frequency_Hz': float(data[np.argmax(np.abs(z)), 0]),
                                             'selected': [{'frequency_Hz': float(data[index, 0]), 'real': float(z[index].real), 'imag': float(z[index].imag), 'magnitude': float(abs(z[index])), 'phase_deg': float(np.angle(z[index], deg=True))} for index in [0, 50, 100, 150, 200, 250, 300, 350, 400, 450]]}
                row['ac_waveform_sha256'] = sha(out/(case+'_ac.dat'))
                row['ac_column_definition'] = ['frequency_Hz']+[part+'('+vector+')' for vector in vectors for part in ['real', 'imag']]
            row['op_waveform_sha256'] = sha(out/(case+'_op.dat'))
            row['status'] = 'passed' if all(row['checks'].values()) else 'failed'
        except (OSError, ValueError, AssertionError, IndexError) as error:
            row['analysis_error'] = str(error)
        manifest['cases'].append(row)
        manifest['not_run_cases'] = [name for name in ['control', 'vref', 'iptat'] if name not in [item['name'] for item in manifest['cases']]]
        manifest['status'] = 'passed' if len(manifest['cases']) == 3 and all(item['status'] == 'passed' for item in manifest['cases']) else 'failed'
        save()
        print(json.dumps(row), flush=True)
        if row['status'] != 'passed':
            raise SystemExit(1)


if __name__ == '__main__':
    main()
