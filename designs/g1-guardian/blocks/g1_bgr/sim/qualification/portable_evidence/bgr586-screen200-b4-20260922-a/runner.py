#!/usr/bin/env python3
"""Independent nominal-process BGR586 mismatch draws using qualified literal decks."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
sys.path.insert(0,str(HERE.parents[2]/'g1_trip/sim'))
from result_directory import allocate_run
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_deck(deck,seed):
    assert deck.count('seed=44001 ')==1 and 44002<=seed<=44300
    result=deck.replace('seed=44001 ','seed=%d '%seed)
    assert result.replace('seed=%d '%seed,'seed=44001 ')==deck
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--seeds',required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    seeds=list(map(int,a.seeds.split(',')));assert len(seeds)<=20 and len(seeds)==len(set(seeds))
    ref=HERE/'runs/bgr_one_draw_20260922_r1';m=json.loads((ref/'manifest.json').read_text());assert m['status']=='passed harness qualification'
    enabled=m['cases'][0];assert enabled['seed']==44001 and enabled['status']=='passed'
    parameters=m['parameters'];assert len(parameters)==len(set(parameters))==2842
    source=ref/'enabled';assert sha(source/'pex_nominal.spice')==m['source_sha256']=='586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    original=(source/'nominal.cir').read_text();assert sha(source/'nominal.cir')==enabled['deck_sha256']
    for seed in seeds:seed_deck(original,seed)
    pd=Path('/foss/pdks/ihp-sg13g2');assert (pd/'COMMIT').read_text().strip()==m['runtime']['pdk_commit']
    assert a.image_id=='sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
    for key,folder,pattern in [('model_sha256','models','*.lib'),('osdi_sha256','osdi','*.osdi')]:
        assert m['runtime'][key]=={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice'/folder).glob(pattern))}
    assert subprocess.check_output(['ngspice','--version'],universal_newlines=True)==m['ngspice']
    out=allocate_run(HERE.parent,a.run_id)
    shutil.copyfile(str(Path(__file__)),str(out/'runner.py'))
    provenance={'arguments':sys.argv[1:],'runner_sha256':sha(Path(__file__)),'source_sha256':m['source_sha256'],'runtime':m['runtime'],
                'image_manifest':a.image_id,'qualified_reference_manifest_sha256':sha(ref/'manifest.json'),'qualified_reference_run':str(ref.relative_to(ROOT)),
                'source_snapshot_sha256':{name:sha(source/name) for name in ['pex_nominal.spice','pex_mm.spice','.spiceinit']},
                'reference_deck_sha256':enabled['deck_sha256'],'parameter_count':2842,'seeds':seeds,
                'scope':'Independent586 mismatch draws, exactqualifiedenabled deck exceptseed;34temps−40..125/5C; standalone1pF VREF/ideal1V IPTATload. Not jointnominalBGRdraws, actualloadedcalibration, finalgeometryPEX or modelvalidity.'}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    rows=[]
    for seed in seeds:
        if (out/'PAUSE_REQUESTED').exists():break
        leaf=out/('s%d'%seed);leaf.mkdir()
        for name in ['pex_nominal.spice','pex_mm.spice','.spiceinit']:shutil.copyfile(str(source/name),str(leaf/name))
        (leaf/'nominal.cir').write_text(seed_deck(original,seed))
        with (leaf/'run.log').open('x') as log:
            state=run_bounded(['ngspice','-b','nominal.cir'],log,leaf/'run.json',120,cwd=leaf,interval_s=1)
        log=(leaf/'run.log').read_text();errors=[line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|analysis aborted|no such parameter|no such vector)',line)]
        row={'seed':seed,'status':'failed','tc_status':'not run','wall_s':state['wall_s'],'watchdog_status':state['status'],'returncode':state['returncode'],
             'errors':errors,'warnings':warning_inventory(log),'deck_sha256':sha(leaf/'nominal.cir')}
        try:
            assert state['status']=='completed' and state['returncode']==0 and not errors
            observed=re.findall(r'^(@[^\s]+)\s*=\s*(\S+)',log,re.M)
            assert [key for key,value in observed]==parameters+parameters
            assert all(np.isfinite(float(value)) for key,value in observed)
            before,after=observed[:2842],observed[2842:];assert before==after
            data=np.loadtxt(str(leaf/'nominal.dat'),skiprows=1)
            assert data.shape==(34,12) and np.isfinite(data).all() and np.array_equal(data[:,0],np.arange(-40,126,5))
            tc=float(np.ptp(data[:,1])/data[13,1]/165*1e6)
            row.update(status='passed',tc_status='passed' if tc<=50 else 'failed',tc_ppm_C=tc,parameters_before=before,parameters_after=after,
                       vref25_V=float(data[13,1]),waveform_sha256=sha(leaf/'nominal.dat'))
        except (AssertionError,ValueError,OSError,IndexError) as error:row['analysis_error']=repr(error)
        rows.append(row);(out/'summary.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps({key:row[key] for key in ['seed','status','tc_status','wall_s']}),flush=True)
    raise SystemExit(0 if len(rows)==len(seeds) and all(row['status']=='passed' for row in rows) else 1)


if __name__=='__main__':main()
