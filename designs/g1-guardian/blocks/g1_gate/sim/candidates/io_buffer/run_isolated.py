#!/usr/bin/env python3
"""Bounded receiver/driver diagnostic; ideal input, no GATE-core qualification."""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
SIM = HERE.parents[1]
ROOT = SIM.parents[4]
sys.path.insert(0, str(SIM.parents[1] / 'g1_top/sim'))
from run_bounded import run_bounded, atomic_json

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def wave(p):
    with p.open() as f:
        header = f.readline().split()
        rows = [list(map(float, line.split())) for line in f if line.strip()]
    if not rows or any(len(r) != len(header) or not all(map(math.isfinite, r)) for r in rows):
        raise ValueError('empty, malformed or nonfinite waveform')
    return header, rows

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--image-id', required=True)
    ap.add_argument('--corner', choices=['tt', 'ss', 'ff'], default='tt')
    ap.add_argument('--temp', type=float, default=27)
    ap.add_argument('--vdda', type=float, default=3.3)
    ap.add_argument('--vdd', type=float, default=1.2)
    ap.add_argument('--timeout', type=float, default=120)
    ap.add_argument('--method', choices=['gear','trap'], default='gear')
    ap.add_argument('--maxstep-ns', type=float, default=.5)
    ap.add_argument('--pad-only', action='store_true')
    ap.add_argument('--bypass', type=int, choices=[0,1], default=1)
    ap.add_argument('--supply-resistance', type=float, default=.5, help='zero is an ideal-supply diagnostic')
    ap.add_argument('--driver-series', type=float, default=0, help='unadopted series resistor between driver and pad')
    ap.add_argument('--solver', choices=['default','klu','sparse'], default='default')
    ap.add_argument('--abstol', type=float, default=1e-14, help='Explicit current tolerance; changing this is a separately recorded numerical diagnostic')
    a = ap.parse_args()
    tag = 'isolated_' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
    out = SIM / 'campaigns' / tag
    out.mkdir(exist_ok=False)
    source = out / 'candidate_source.spice'
    source.write_bytes((HERE / 'driver.spice').read_bytes())
    (out / '.spiceinit').write_bytes((SIM / '.spiceinit').read_bytes())
    pdk = Path(os.environ.get('PDK_ROOT', '/foss/pdks')) / 'ihp-sg13g2'
    models = pdk / 'libs.tech/ngspice/models'
    io = pdk / 'libs.ref/sg13g2_io/spice/sg13g2_io.spi'
    metadata = dict(options=vars(a), image_id=a.image_id,
        pdk_commit=(pdk / 'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice', '-v'], text=True),
        git_revision=subprocess.check_output(['git', '-c', 'safe.directory='+str(ROOT), 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        source_sha256=sha(source), runner_sha256=sha(Path(__file__)), io_sha256=sha(io),
        init_sha256=sha(out / '.spiceinit'),
        model_sha256={str(p.relative_to(pdk)):sha(p) for p in sorted(models.rglob('*')) if p.is_file()},
        scope='Ideal core input, schematic candidate, 5nF/10ohm/10kohm fixture. No core, real FET, layout, EM or ESD qualification.')
    results = []
    for pad in ([True] if a.pad_only else [False, True]):
        name = 'analog_pad' if pad else 'direct'
        deck = '* Isolated unadopted IO receiver and driver\n'
        for lib, section in [('MOSlv', 'mos_'+a.corner), ('MOShv', 'mos_'+a.corner), ('RES','res_typ'), ('CAP','cap_typ'), ('DIO','dio_'+a.corner)]:
            deck += f'.lib {models}/corner{lib}.lib {section}\n'
        deck += f'.include {io}\n.include {source}\n.temp {a.temp}\n.global sub!\nVsub sub! 0 0\n'
        deck += f'.option method={a.method} bypass={a.bypass} reltol=1e-5 abstol={a.abstol:.17g} vntol=1e-7 chgtol=1e-14 itl4=100\n'
        if a.solver!='default':
            deck += f'.option {a.solver}\n'
        deck += f'Va as 0 {a.vdda}\n'
        deck += f'Ra as va {a.supply_resistance}\n' if a.supply_resistance else 'Vas as va 0\n'
        deck += f'Ca va 0 1n\nVd vd 0 {a.vdd}\n'
        deck += f'Vin core 0 pwl(0 0 1u 0 1.1u {a.vdd} 4u {a.vdd} 4.1u 0 8u 0)\n'
        deck += 'Xreceiver core driver va 0 g1_io_buffer_candidate\n'
        deck += f'Rseries driver drive {a.driver_series}\n' if a.driver_series else 'Vseries driver drive 0\n'
        deck += 'Xpad gate drive vd 0 va 0 sg13g2_IOPadAnalog\n' if pad else 'Vlink drive gate 0\n'
        deck += 'Rg gate gfet 10\nCg gfet 0 5n\nRpd gate 0 10k\n'
        deck += '.control\nset num_threads=1\nset numdgt=17\nset wr_singlescale\nset wr_vecnames\n'
        deck += f'dc Vin 0 {a.vdd} .005\nwrdata {out/(name+"_dc.tsv")} v(core) v(xreceiver.sense) v(drive) v(gate) v(gfet) i(va) i(vin)\n'
        deck += f'reset\ntran {a.maxstep_ns}n 8u 0 {a.maxstep_ns}n\nwrdata {out/(name+"_tran.tsv")} v(core) v(xreceiver.sense) v(drive) v(gate) v(gfet) i(va) i(vin)\nquit 0\n.endc\n.end\n'
        dp = out / (name+'.cir'); dp.write_text(deck)
        with (out / (name+'.log')).open('x') as log:
            result = run_bounded(['ngspice','-b',str(dp)], log, out/(name+'.json'), a.timeout, cwd=out, metadata=dict(metadata, deck_sha256=sha(dp)), interval_s=2)
        assessment = dict(case=name, solver_status=result['status'], wall_s=result['wall_s'], completion='failed', electrical_acceptance='not run')
        try:
            _, dc = wave(out/(name+'_dc.tsv')); _, tr = wave(out/(name+'_tran.tsv'))
            if result['status']!='completed' or re.search(r'Timestep too small|doAnalyses:|^Error:|simulation\s+aborted', (out/(name+'.log')).read_text(), re.I|re.M):
                raise ValueError('solver failure or incomplete')
            if abs(dc[-1][0]-a.vdd)>1e-9 or abs(tr[-1][0]-8e-6)>1e-12 or tr[0][0]!=0:
                raise ValueError('missing endpoint')
            if any(y[0]<x[0] for x,y in zip(tr,tr[1:])):
                raise ValueError('nonmonotonic time')
            before = [r for r in tr if r[0]<=1e-6]
            high = [r for r in tr if 3e-6<=r[0]<=4e-6]
            low = [r for r in tr if r[0]>=7e-6]
            checks = dict(dc_low=dc[0][4]<1, dc_high=dc[-1][4]>2.5,
                startup_low=max(r[5] for r in before)<1,
                armed_high=min(r[5] for r in high)>2.5,
                end_low=max(r[5] for r in low)<1)
            crossing = next((r[0] for r in tr if r[0]>=4.1e-6 and r[5]<1), None)
            checks['turnoff_under_10us'] = crossing is not None and crossing-4.1e-6<10e-6
            assessment.update(completion='passed', electrical_acceptance='passed' if all(checks.values()) else 'failed', checks=checks,
                metrics=dict(dc_gate_high_V=dc[-1][4], dc_supply_high_A=-dc[-1][6], dc_supply_max_A=max(-r[6] for r in dc), turnoff_after_input_fall_s=None if crossing is None else crossing-4.1e-6,
                    input_half_output_V=next((r[1] for r in dc if r[4]>=a.vdda/2),None)),
                wave_sha256={p.name:sha(p) for p in [out/(name+'_dc.tsv'),out/(name+'_tran.tsv')]})
        except (OSError, ValueError) as exc:
            assessment.update(error=str(exc).replace(str(ROOT)+'/', ''), completion='not run to completion' if result['status'] in ['timeout','interrupted'] else 'failed')
        results.append(assessment)
        atomic_json(out/'assessment.json', dict(metadata, cases=results))
        print(json.dumps(assessment), flush=True)
    print(out.relative_to(ROOT), flush=True)
    if any(r['electrical_acceptance']!='passed' for r in results):
        raise SystemExit(1)

if __name__=='__main__':
    main()
