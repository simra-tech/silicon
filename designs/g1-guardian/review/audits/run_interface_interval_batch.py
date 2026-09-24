#!/usr/bin/env python3
"""Bounded whole-parallel-interval pilot; not full-net or assembled PEX."""
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
    parser.add_argument('--pair', choices=['isense_clock', 'vref_dac', 'vrefbuf_dac', 'iptat_isense'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--image-id', required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    names = ['prepare_interface_clip.py', 'run_fill_clip_pex.py', 'analyze_interface_clip.py',
             'clip_cap_graph.py', 'check_fill_clip_ac.py', 'export_clip_lvsdb.lvs', Path(__file__).name]
    frozen = {name: sha(HERE/name) for name in names}
    gds = ROOT/'designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds'
    gds_hash = '38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59'
    assert sha(gds) == gds_hash
    for name in names:
        shutil.copyfile(HERE/name, out/name)
    report = dict(status='not run', pair=args.pair, source_sha256=frozen, gds_sha256=gds_hash,
                  image_id=args.image_id, matrix_context_tolerance=0.01, mutual_end_tolerance=0.01,
                  contexts_um=[12,24], end_margins_um=[10,20], cases=[],
                  scope='Exact metal/via clips include shared parallel interval and stated ends, not entire nets. Other context grounded, fill floating/grounded diagnostics. Require1percent matrix convergence12to24um at fixed ends;1percent mutual-C convergence10to20um ends at fixed width. Ground capacitance need not converge with increasing retained target length. No actual-source/time-domain acceptance.')
    atomic_json(out/'manifest.json', report)
    for width in [12,24]:
        for margin in [10,20]:
            assert sha(gds) == gds_hash and all(sha(HERE/name) == value for name,value in frozen.items())
            leaf = out/('w%d_m%d' % (width,margin))
            leaf.mkdir()
            item = dict(context_um=width,end_margin_um=margin,status='not run',steps=[])
            report['cases'].append(item)
            commands = [
                [sys.executable,str(HERE/'prepare_interface_clip.py'),'--pair',args.pair,'--context-um',str(width),
                 '--end-margin-um',str(margin),'--expected-sha256',gds_hash,'--output',str(leaf/'clip')],
                [sys.executable,str(HERE/'run_fill_clip_pex.py'),'--clip',str(leaf/'clip'),'--output',str(leaf/'pex')],
                [sys.executable,str(HERE/'analyze_interface_clip.py'),'--input',str(leaf/'pex'),'--output',str(leaf/'analysis')],
                [sys.executable,str(HERE/'check_fill_clip_ac.py'),str(leaf/'analysis')],
            ]
            for index,command in enumerate(commands):
                with (leaf/('step%d.log' % index)).open('x') as log:
                    completed = subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
                step = dict(command=[s.replace(str(ROOT)+'/', '') for s in command],returncode=completed.returncode)
                item['steps'].append(step)
                okay = completed.returncode == 0
                if index == 1 and okay:
                    children = json.loads((leaf/'pex/manifest.json').read_text())
                    okay = len(children)==2 and all(r.get('extract_status')=='completed' and r.get('kpex_status')=='completed'
                                                    and r.get('extract_returncode')==0 and r.get('kpex_returncode')==0 for r in children)
                    step['child_completion_passed'] = okay
                if not okay:
                    report['status'] = item['status'] = 'failed'
                    atomic_json(out/'manifest.json',report)
                    raise SystemExit(1)
                atomic_json(out/'manifest.json',report)
            item['status'] = 'passed'
            item['analysis_sha256'] = sha(leaf/'analysis/summary.json')
            atomic_json(out/'manifest.json',report)
            print(json.dumps(item),flush=True)
    def data(width,margin,variant,mode):
        return json.loads((out/('w%d_m%d' % (width,margin))/'analysis/summary.json').read_text())['results'][variant]['modes'][mode]
    checks=[]
    for variant in ['no_fill','actual_fill']:
        for mode in ['grounded','floating']:
            for margin in [10,20]:
                a,b=[data(w,margin,variant,mode)['matrix_fF'] for w in [12,24]]
                error=max(abs(a[i][j]-b[i][j])/abs(b[i][j]) for i in range(2) for j in range(2))
                checks.append(dict(type='transverse_matrix',variant=variant,mode=mode,end_margin_um=margin,relative_error=error,status='passed' if error<=.01 else 'failed'))
            for width in [12,24]:
                a,b=[data(width,m,variant,mode)['mutual_fF'] for m in [10,20]]
                error=abs(a-b)/abs(b)
                checks.append(dict(type='longitudinal_mutual',variant=variant,mode=mode,context_um=width,relative_error=error,status='passed' if error<=.01 else 'failed'))
    report['convergence_checks']=checks
    report['status']='passed' if all(r['status']=='passed' for r in checks) else 'failed'
    atomic_json(out/'manifest.json',report)
    if report['status']!='passed':
        raise SystemExit(1)


if __name__=='__main__':
    main()
