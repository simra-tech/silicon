#!/usr/bin/env python3
"""Bounded paired original-seed method control; never population/yield credit."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
from prepare_rz100_mc_control import SIM, sha, instrument
from run_loaded_noise_audit import read_group, run_bounded, warning_inventory
from run_loaded_followthrough import errors
from run_loaded_compensation_candidate import CAP_QUERY, scale_interval

def parse(log, queries):
    lines = re.findall(r'^ROW .+$', log, re.M)
    rows = {}
    for line in lines:
        _, key, *values = line.split()
        assert key not in rows
        values = list(map(float, values))
        assert len(values) == 7 and all(map(math.isfinite, values))
        rows[key] = values
    expected = {f't{t}_c{cm}_s{s}' for t in range(4)
                for cm in [-.1, 0, .3] for s in [0, .025, .05]}
    assert set(rows) == expected and len(lines) == 36
    legacy = []
    for i in range(4):
        sections = re.findall(r'^FINGERPRINT '+str(i)+r'\n((?:@n\.[^\n]+\n){51})', log, re.M)
        assert len(sections)==1, 'Missing/repeated legacy fingerprint'
        section=sections[0]
        legacy.append(section)
    assert len(set(legacy)) == 1
    assert all(rows[k] == rows[k.replace('t0_', 't3_')] for k in rows if k.startswith('t0_'))
    groups = [read_group(log, 'SENSE_FULL_'+str(i), queries) for i in range(4)] if queries else []
    if groups:
        assert len(groups[0]) == 529 and all(g == groups[0] for g in groups)
    return dict(rows=rows, row_lines=lines, legacy=legacy[0], parameters=groups[0] if groups else [])

def electrical(rows):
    nominal = 51/53*1.04
    correction = (rows['t0_c0_s0.025'][0]-nominal)/20-.025
    gains = []
    points = []
    for t in range(3):
        for cm in [-.1, 0, .3]:
            gains.append((rows[f't{t}_c{cm}_s0.05'][0]-rows[f't{t}_c{cm}_s0'][0])/.05)
            for s in [0, .025, .05]:
                points.append(dict(temperature_C=[25,-40,125][t], sense_n_V=cm,
                    true_cm_V=cm+s/2, shunt_V=s,
                    residual_V=(rows[f't{t}_c{cm}_s{s}'][0]-nominal)/20-s-correction))
    supported = [p for p in points if -.1 <= p['true_cm_V'] <= .3]
    assert len(supported) == 21
    return dict(calibration_V=correction, gain_min=min(gains), gain_max=max(gains),
        gain_status='passed' if min(gains)>=19.9 and max(gains)<=20.1 else 'failed',
        supported_offset_status='passed' if max(abs(p['residual_V']) for p in supported)<.0005 else 'failed',
        all27_offset_status='passed' if max(abs(p['residual_V']) for p in points)<.0005 else 'failed',
        points=points, scope='Simulated ideal continuous correction; not digital trim or joint-chain yield.')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--packet', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a=ap.parse_args()
    assert os.sched_getaffinity(0)=={1} and not a.output.exists()
    pc=json.loads((a.packet/'contract.json').read_text())
    assert sha(a.packet/'contract.json')=='e014fa892b04904419ec5fc7614281a96580283088f8514289170434966a6741'
    original=SIM/pc['original_run_relative']
    old=parse((original/'seed41039.log').read_text(), [])
    provenance=json.loads((original/'provenance.json').read_text())
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),
        model_hashes={str(p.relative_to(pd)):sha(p) for p in (pd/'libs.tech/ngspice/models').rglob('*') if p.is_file()})
    assert all(runtime[k]==provenance[k] for k in runtime)
    for kind in ['historical','candidate']:
        assert sha(a.packet/(kind+'.cir'))==pc['artifacts'][kind]['deck_sha256']
        assert sha(a.packet/(kind+'.spice'))==pc['artifacts'][kind]['source_sha256']
        assert (a.packet/(kind+'.cir')).read_text()==instrument((original/'seed41039.cir').read_text(),a.packet/(kind+'.spice'),pc['queries'])
    a.output.mkdir(parents=True)
    (a.output/'runner.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'provenance.json').write_text(json.dumps(runtime,indent=2)+'\n')
    result=dict(status='failed', seed=41039, contract_sha256=sha(a.packet/'contract.json'),
        runs={}, population='not run', full_PEX='not run', hardware='not applicable')
    try:
        for kind in ['historical','candidate']:
            with (a.output/(kind+'.log')).open('x') as log:
                state=run_bounded(['ngspice','-b',str(a.packet/(kind+'.cir'))],log,
                    a.output/(kind+'.json'),120,cwd=SIM,interval_s=.2)
            log=(a.output/(kind+'.log')).read_text()
            item=dict(runtime=state, errors=errors(log), warnings=warning_inventory(log))
            result['runs'][kind]=item
            assert state['status']=='completed' and state['returncode']==0
            assert not item['errors'] and 'QUALIFICATION_END' in log
            item.update(parse(log,pc['queries']))
            assert item['legacy']==old['legacy']
            if kind=='historical':
                assert item['row_lines']==old['row_lines']
                item['print_only_parity']='passed exact36rows and51legacy parameters'
            else:
                prior=result['runs']['historical']['parameters']
                cap=CAP_QUERY.replace('.xs.','.xdut.')
                assert [r for r in prior if r[0]!=cap]==[r for r in item['parameters'] if r[0]!=cap]
                item['cap_native_law']=scale_interval(dict(prior)[cap],dict(item['parameters'])[cap],'45')
                assert item['cap_native_law']['status']=='passed'
            item['electrical']=electrical(item['rows'])
        result['status']='passed paired method controls; electrical statuses separate'
    except (AssertionError,ValueError,KeyError,OSError) as exc:
        result['analysis_error']=repr(exc)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],analysis_error=result.get('analysis_error'),
        electrical={k:v.get('electrical') for k,v in result['runs'].items()})))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)

if __name__=='__main__': main()
