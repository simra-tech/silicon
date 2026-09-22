#!/usr/bin/env python3
"""Reduce a pad convergence failure using unchanged PDK components and ideal drive."""
import argparse
import datetime
import json
from pathlib import Path
import re
import subprocess
import uuid
from run_isolated import SIM, ROOT, sha, wave, run_bounded, atomic_json

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--image-id', required=True)
    ap.add_argument('--timeout', type=float, default=30)
    ap.add_argument('--replay', type=Path, help='Impose the saved driver output through50ohm; diagnostic only')
    ap.add_argument('--cases', nargs='+', choices=['dpantenna','dantenna','secondary','analog'], default=['dpantenna','secondary','analog'])
    ap.add_argument('--show-devices', action='store_true')
    a=ap.parse_args()
    out=SIM/'campaigns'/('diode_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    (out/'.spiceinit').write_bytes((SIM/'.spiceinit').read_bytes())
    pdk=Path('/foss/pdks/ihp-sg13g2');models=pdk/'libs.tech/ngspice/models'
    io=pdk/'libs.ref/sg13g2_io/spice/sg13g2_io.spi'
    metadata=dict(options=vars(a),image_id=a.image_id,pdk_commit=(pdk/'COMMIT').read_text().strip(),
        runner_sha256=sha(Path(__file__)),io_sha256=sha(io),init_sha256=sha(out/'.spiceinit'),
        ngspice_version=subprocess.check_output(['ngspice','-v'],text=True),
        model_sha256={str(p.relative_to(pdk)):sha(p) for p in sorted(models.rglob('*')) if p.is_file()},
        scope='Convergence reproducer only: ideal imposed input, no GATE-core/driver/load acceptance. Unchanged library subcircuits.')
    metadata['options']={k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()}
    stimulus='0 0 .1u 0 .2u 3.3 1u 3.3 1.1u 0 2u 0'
    stop=2e-6
    if a.replay:
        cols,rows=wave(a.replay)
        col=cols.index('v(drive)')
        if rows[0][0]!=0 or any(y[0]<=x[0] for x,y in zip(rows,rows[1:])):
            raise ValueError('replay must have strictly increasing times from zero')
        stimulus='\n+ '.join(f'{r[0]:.17g} {r[col]:.17g}' for r in rows)
        stop=rows[-1][0]
        metadata.update(replay_sha256=sha(a.replay),replay_column='v(drive)',replay_limit='Imposed voltage removes transistor feedback and original output impedance.')
    results=[]
    circuits={
        'dpantenna':'Xdiode drive va dpantenna l=4.98u w=640n m=1\n',
        'dantenna':'Xdiode 0 drive dantenna l=3.1u w=640n m=1\n',
        'secondary':'Xsecondary drive 0 gate va sg13g2_SecondaryProtection\nRg gate gfet 10\nCg gfet 0 5n\nRpd gate 0 10k\n',
        'analog':'Xpad gate drive vd 0 va 0 sg13g2_IOPadAnalog\nRg gate gfet 10\nCg gfet 0 5n\nRpd gate 0 10k\n'}
    for name,circuit in circuits.items():
        if name not in a.cases:continue
        text='* Unchanged PDK diode/pad convergence reduction\n'
        for lib,section in [('MOSlv','mos_tt'),('MOShv','mos_tt'),('RES','res_typ'),('CAP','cap_typ'),('DIO','dio_tt')]:
            text+=f'.lib {models}/corner{lib}.lib {section}\n'
        text+=f'.include {io}\n.global sub!\nVsub sub! 0 0\n.temp 27\n.option method=gear reltol=1e-5 abstol=1e-14 vntol=1e-7 chgtol=1e-14 itl4=100\n'
        text+=f'Va va 0 3.3\nVd vd 0 1.2\nVin input 0 pwl({stimulus})\nRinput input drive 50\n'+circuit
        text+=f'.control\nset num_threads=1\nset numdgt=17\nset wr_singlescale\nset wr_vecnames\ntran .5n {stop:.17g} 0 .5n\nwrdata {out/(name+".tsv")} v(input) v(drive) i(va) i(vin)\nquit 0\n.endc\n.end\n'
        if a.show_devices:text=text.replace('quit 0','show all\nquit 0')
        deck=out/(name+'.cir');deck.write_text(text)
        with (out/(name+'.log')).open('x') as log:
            r=run_bounded(['ngspice','-b',str(deck)],log,out/(name+'.json'),a.timeout,cwd=out,metadata=dict(metadata,deck_sha256=sha(deck)),interval_s=2)
        assessment=dict(case=name,solver_status=r['status'],wall_s=r['wall_s'],completion='failed',electrical_acceptance='not applicable')
        try:
            _,rows=wave(out/(name+'.tsv'))
            bad=re.search(r'Timestep too small|doAnalyses:|^Error:|simulation\s+aborted',(out/(name+'.log')).read_text(),re.M|re.I)
            assessment.update(completion='passed' if r['status']=='completed' and not bad and abs(rows[-1][0]-stop)<1e-12 else 'failed',observed_end_s=rows[-1][0],wave_sha256=sha(out/(name+'.tsv')))
        except (ValueError,OSError) as e:
            assessment['error']=str(e).replace(str(ROOT)+'/', '')
        if r['status'] in ['timeout','interrupted']:assessment['completion']='not run to completion'
        results.append(assessment);atomic_json(out/'assessment.json',dict(metadata,cases=results))
        print(json.dumps(assessment),flush=True)
    print(out.relative_to(ROOT),flush=True)
    if any(r['completion']!='passed' for r in results):raise SystemExit(1)

if __name__=='__main__':main()
