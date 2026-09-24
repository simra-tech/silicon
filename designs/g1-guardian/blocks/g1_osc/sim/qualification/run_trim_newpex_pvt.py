#!/usr/bin/env python3
"""Five selected PVT tuples x all16 codes on the pinned new physical CPEX.

This is the unchanged 6 us/300 s/50 fF trim protocol with a source binding,
not a new mismatch population, full Cartesian PVT, or receiver-load test.
"""
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

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'g1_trip/sim'))
from result_directory import allocate_run

HERE = Path(__file__).resolve().parent
PDK = Path('/foss/pdks/ihp-sg13g2')
PDK_COMMIT = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
IMAGE_ID = 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
PEX_SHA = '8efd7a09faf173da8604a219f73fd3ea5ec2508618d8361a050770c099d8b1c5'
TUPLES = [('tt','typ','typ',1.2,27), ('ss','wcs','wcs',1.08,-40),
          ('ss','wcs','wcs',1.08,125), ('ff','bcs','bcs',1.32,-40),
          ('ff','bcs','bcs',1.32,125)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def positions(shard):
    assert shard in range(4)
    return [(index, code) for index in range(5) for code in range(16)
            if (index*16+code) % 4 == shard]


def source_valid(path):
    if not Path(path).is_file() or sha(path) != PEX_SHA:
        return False
    lines = Path(path).read_text().splitlines()
    return (sum(line.startswith('XR') and 'l=55.575u' in line for line in lines) == 4
            and not any(line.startswith('XR') and 'l=58.5u' in line for line in lines))


def deck_for(template, source_name, condition, code):
    mos, res, cap, vdd, temp = condition
    deck = template.replace('tran 0.2n 3.3u', 'tran 0.2n 6.0u')
    values = {'MOS':'mos_'+mos, 'RES':'res_'+res, 'CAP':'cap_'+cap,
              'VDD':vdd, 'TEMP':temp}
    values.update({'B'+str(i):(code>>i)&1 for i in range(4)})
    for key, value in values.items():
        deck = deck.replace('@@'+key+'@@', str(value))
    assert '.include postlayout/g1_osc_pex.spice' in deck
    assert 'set filetype=ascii' in deck and '.endc' in deck
    deck = deck.replace('.include postlayout/g1_osc_pex.spice', '.include '+source_name)
    deck = deck.replace('.control\n', '.control\nset num_threads=1\n')
    deck = deck.replace('set filetype=ascii', 'set filetype=ascii\nset numdgt=15\nset wr_singlescale\nset wr_vecnames')
    name = '%s_%s_%s_%s_%s_c%d' % (mos,res,cap,vdd,temp,code)
    deck = deck.replace('.endc', 'print fmhz duty iua\nwrdata '+name+'.dat v(osc_clk) i(vdd) v(x1.va) v(x1.vb)\nquit\n.endc')
    assert not re.search(r'@@[A-Z0-9]+@@', deck)
    return name, deck


def wave_valid(path):
    try:
        with Path(path).open() as stream:
            next(stream)
            previous, final, rows = -1.0, None, 0
            for line in stream:
                if not line.strip():
                    continue
                values = [float(x) for x in line.split()]
                if len(values) != 5 or not all(math.isfinite(v) for v in values):
                    return False
                if values[0] <= previous:
                    return False
                previous, final, rows = values[0], values[0], rows+1
        return rows > 1 and abs(final-6e-6) < 1e-12
    except (OSError, ValueError, StopIteration):
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--image-id', required=True)
    ap.add_argument('--pex-source', type=Path, required=True)
    ap.add_argument('--pex-sha256', required=True)
    ap.add_argument('--shard-index', type=int, choices=range(4), required=True)
    args = ap.parse_args()
    assert args.image_id == IMAGE_ID and args.pex_sha256 == PEX_SHA
    assert (PDK/'COMMIT').read_text().strip() == PDK_COMMIT
    assert source_valid(args.pex_source)
    assert args.run_id == 'osc_r095_newpex_pvt80_20260924_r1_shard%d' % args.shard_index
    out = allocate_run(HERE.parent, args.run_id, relative_parent='qualification/runs')
    shutil.copy(__file__, out/'run_trim_newpex_pvt.py')
    shutil.copy(HERE.parent/'.spiceinit', out/'.spiceinit')
    shutil.copy(args.pex_source, out/'osc.spice')
    assert sha(out/'osc.spice') == PEX_SHA
    template = (HERE.parent/'postlayout/tb_osc_pex.cir').read_text()
    public_command = ['<bound-pex-source>' if value == str(args.pex_source) else value for value in sys.argv]
    manifest = {'command':public_command, 'source_kind':'new physical OSC R0.95 CPEX; no additional resistor scaling',
                'image_id':args.image_id, 'pdk_commit':PDK_COMMIT,
                'ngspice':subprocess.check_output(['ngspice','--version'], universal_newlines=True),
                'runner_sha256':sha(__file__), 'pex_sha256':PEX_SHA,
                'template_sha256':sha(HERE.parent/'postlayout/tb_osc_pex.cir'),
                'spiceinit_sha256':sha(out/'.spiceinit'),
                'models_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},
                'shard_index':args.shard_index, 'shards':4,
                'expected_cases':[{'tuple_index':i,'code':c} for i,c in positions(args.shard_index)],
                'limitations':'Five selected PVT tuples only; mismatch disabled; 50fF stand-in; capacitance-only PEX with reinserted MIM; no actual receiver or full Cartesian PVT.',
                'cases':[]}
    def save():
        (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    save()
    for index, code in positions(args.shard_index):
        name, deck = deck_for(template, 'osc.spice', TUPLES[index], code)
        (out/(name+'.cir')).write_text(deck)
        started = time.monotonic()
        timed = False
        with (out/(name+'.log')).open('w') as stream:
            try:
                rc = subprocess.run(['ngspice','-b',name+'.cir'], cwd=out, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=300).returncode
            except subprocess.TimeoutExpired:
                timed, rc = True, None
        log = (out/(name+'.log')).read_text(errors='replace')
        measurements = {key:float(value) for key,value in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)',log)}
        good = (rc == 0 and not timed and wave_valid(out/(name+'.dat'))
                and all(key in measurements and math.isfinite(measurements[key]) for key in ('fmhz','duty','t1','t2','th1'))
                and not re.search(r'(?im)^Error|Timestep too small|analysis aborted',log))
        row = {'name':name,'tuple_index':index,'code':code,'mos':TUPLES[index][0],
               'res':TUPLES[index][1],'cap':TUPLES[index][2],'vdd':TUPLES[index][3],
               'temp':TUPLES[index][4],'tstop_us':6,'watchdog_seconds':300,
               'timed_out':timed,'solver_exit':rc,'wall_seconds':time.monotonic()-started,
               'status':'passed' if good else 'failed','measurements':measurements,
               'deck_sha256':sha(out/(name+'.cir')),
               'waveform_sha256':sha(out/(name+'.dat')) if (out/(name+'.dat')).exists() else None}
        if good:
            row['high_width_s'] = measurements['th1']-measurements['t1']
            row['low_width_s'] = (measurements['t2']-measurements['t1'])/10-row['high_width_s']
        manifest['cases'].append(row)
        save()
        print(json.dumps(row), flush=True)


if __name__ == '__main__':
    main()
