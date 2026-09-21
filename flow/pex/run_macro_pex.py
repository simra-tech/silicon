#!/usr/bin/env python3
"""Bounded flat macro C-PEX with unchanged installed IHP/KPEX decks."""
import argparse, datetime, hashlib, json, shutil, subprocess, sys, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded, atomic_json
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('block',choices=['dut','dose','ls']);ap.add_argument('--image-id',required=True)
a=ap.parse_args()
base=ROOT/'designs/g1-guardian/blocks'
cfg={'dut':('g1_dut','g1_dut_macro','schematic/g1_dut_macro.cdl'),
     'dose':('g1_dose','g1_dose_macro','schematic/g1_dose_macro.cdl'),
     'ls':('g1_ctrl/ls','g1_ls_up','sim/netlist/g1_ls_up.cdl')}
block,cell,cdl=cfg[a.block]; block=base/block; cdl=block/cdl; gds=block/'layout'/f'{cell}.gds'
runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
out=block/'reports'/('flat-pex-'+runid); out.mkdir(parents=True,exist_ok=False)
work=ROOT/'build'/('flat-pex-'+a.block+'-'+runid);work.mkdir(parents=True,exist_ok=False)
flat=work/(cell+'.gds');db=work/(cell+'.lvsdb');net=work/(cell+'.cir')
wrapper=ROOT/'flow/pex/export_lvsdb.lvs'
deckroot=Path('/usr/local/lib/python3.12/dist-packages/klayout_pex/pdk/ihp-sg13g2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
md=dict(image_id=a.image_id,pdk_commit=Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip(),
        klayout_version=subprocess.check_output(['klayout','-v'],text=True).strip(),
        kpex_version=subprocess.check_output(['kpex','--version'],text=True).strip(),
        inputs={str(p.relative_to(ROOT)):sha(p) for p in [gds,cdl,wrapper,Path(__file__),ROOT/'flow/pex/prepare_flat.py']},
        extraction_support_hashes={str(p.relative_to(deckroot)):sha(p) for p in sorted(deckroot.rglob('*')) if p.is_file()},
        limitations=['Capacitance only; no wire resistance','Macro only; assembly routes and pads excluded','Not full design sign-off'])
steps=[]
def step(name,cmd,timeout):
    with (out/(name+'.log')).open('x') as log:
        r=run_bounded(cmd,log,out/(name+'.json'),timeout,metadata=md,interval_s=5)
    steps.append(dict(name=name,status=r['status'],returncode=r.get('returncode'),wall_s=r['wall_s']))
    atomic_json(out/'campaign.json',dict(md,status='running',steps=steps))
    if r['status']!='completed' or r.get('returncode')!=0:raise RuntimeError(name+' did not complete')
try:
    step('flatten',[sys.executable,str(ROOT/'flow/pex/prepare_flat.py'),'--input',str(gds),'--cell',cell,'--output',str(flat),'--report',str(out/'geometry.json')],120)
    cmd=['stdbuf','-o0','-e0','klayout','-b','-r',str(wrapper)]
    for v in [f'input={flat}',f'schematic={cdl}',f'report={db}',f'export_netlist={net}','thr=1','run_mode=deep','no_simplify=true','combine=false','combine_devices=false','purge=false','purge_nets=false','top_lvl_pins=true','spice_net_names=true','scale=false']:
        cmd+=['-rd',v]
    step('lvs-export',cmd,180)
    log=(out/'lvs-export.log').read_text()
    if 'Congratulations! Netlists match.' not in log or not db.exists():raise RuntimeError('explicit LVS match/database absent')
    shutil.copyfile(net,out/'extracted.cir')
    step('capacitance',['stdbuf','-o0','-e0','kpex','--pdk','ihp-sg13g2','--threads','1','--lvsdb',str(db),'--cell',cell,'--2.5D','--mode','CC','--out_dir',str(work/'kpex')],300)
    candidates=list((work/'kpex').rglob('*_k25d_pex_netlist.spice'))
    if len(candidates)!=1:raise RuntimeError('expected one extracted netlist')
    p=candidates[0];shutil.copyfile(p,out/'raw_pex.spice')
    caps=[l for l in p.read_text().splitlines() if l.startswith('Cext_')]
    if not caps:raise RuntimeError('no extracted capacitors')
    for p in (work/'kpex').rglob('*.csv'):shutil.copyfile(p,out/p.name)
    atomic_json(out/'campaign.json',dict(md,status='passed',scope='Flat macro LVS and C-PEX generation only',steps=steps,capacitor_count=len(caps),raw_pex_sha256=sha(out/'raw_pex.spice'),database_sha256=sha(db)))
except Exception as e:
    atomic_json(out/'campaign.json',dict(md,status='failed',steps=steps,error=str(e)));print(out);raise
print(out)
