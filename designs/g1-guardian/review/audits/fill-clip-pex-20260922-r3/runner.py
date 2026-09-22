#!/usr/bin/env python3
"""Stock KPEX route/fill extraction pilot; no LVS/circuit-signoff claim."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--clip',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output=a.output.resolve();a.clip=a.clip.resolve();a.output.mkdir(exist_ok=False);shutil.copyfile(__file__,a.output/'runner.py');steps=[]
for mode in ['no_fill','actual_fill']:
 leaf=a.output/mode;leaf.mkdir();db=leaf/'clip.lvsdb';net=leaf/'clip.cir';cmd=['klayout','-b','-r',str(ROOT/'designs/g1-guardian/review/audits/export_clip_lvsdb.lvs')]
 for opt in [f'input={a.clip/mode}.gds',f'report={db}',f'export_netlist={net}',f'target_netlist={leaf}/cleanup.cir','thr=1','run_mode=deep','net_only=true','no_simplify=true','combine_devices=false','purge=false','purge_nets=false','top_lvl_pins=true','spice_net_names=true','scale=false']:cmd+=['-rd',opt]
 with (leaf/'extract.log').open('x') as f:state=run_bounded(cmd,f,leaf/'extract.json',120,interval_s=1)
 record={'variant':mode,'extract_status':state['status'],'extract_returncode':state['returncode']};steps.append(record);(a.output/'manifest.json').write_text(json.dumps(steps,indent=2)+'\n')
 if state['returncode']!=0 or not db.exists():continue
 cmd=['kpex','--pdk','ihp-sg13g2','--threads','1','--lvsdb',str(db),'--cell','sense_fill_clip','--2.5D','--mode','CC','--out_dir',str(leaf/'kpex')]
 with (leaf/'kpex.log').open('x') as f:state=run_bounded(cmd,f,leaf/'kpex.json',120,interval_s=1)
 record.update(kpex_status=state['status'],kpex_returncode=state['returncode']);(a.output/'manifest.json').write_text(json.dumps(steps,indent=2)+'\n');print(record,flush=True)
