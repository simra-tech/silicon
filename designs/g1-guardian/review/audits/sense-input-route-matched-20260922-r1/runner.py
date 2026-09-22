#!/usr/bin/env python3
"""Copied ideal-rail baseline SENSE DC anchor with geometry-estimated padbare route R."""
import argparse,hashlib,json,math,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'designs/g1-guardian/blocks/g1_sense/sim';sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'));from run_bounded import run_bounded
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--matched-ohms',help='Comma-separated matched branch values, instead of scale0/1/2');a=p.parse_args();out=a.output.resolve();out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'runner.py');base=S/'qualification/corners-20260921-a/tt_typ_3.3V_27C.cir';net=base.parent/'sense_substrate_tied.spice';shutil.copyfile(net,out/net.name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prov={'scope':'Baseline schematic SENSE, ideal supply/ground/reference/PTAT. Geometry-estimated padbare input route R only; no stock 587ohm secondary branch, no pads, no wire PEX, no fill or transient qualification. Scales0/1/2 are diagnostic, not bounds.','inputs':{str(p.relative_to(ROOT)):sha(p) for p in [base,net,S/'.spiceinit',ROOT/'designs/g1-guardian/review/audits/sense-route-geometry-20260922-r1.json']},'ngspice_version':subprocess.check_output(['ngspice','--version'],text=True),'pdk_commit':Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip(),'R_P_ohm':77.6671,'R_N_ohm':138.2311,'temperature_C':27,'supply_V':3.3}
assert prov['pdk_commit']=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b';(out/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n');results=[]
for scale in ([float(x) for x in a.matched_ohms.split(',')] if a.matched_ohms else [0,1,2]):
 rp=rn=scale if a.matched_ohms else None
 if not a.matched_ohms:rp,rn=77.6671*scale,138.2311*scale
 leaf=out/f'r{scale:g}';leaf.mkdir();shutil.copyfile(S/'.spiceinit',leaf/'.spiceinit');deck=base.read_text().replace('.include qualification/corners-20260921-a/sense_substrate_tied.spice','.include ../sense_substrate_tied.spice');new='Vrp shp corep 0\nVrn cm coren 0' if scale==0 else f'Rrp shp corep {rp:.12g}\nRrn cm coren {rn:.12g}';deck=deck.replace('XDUT shp cm vref',new+'\nXDUT corep coren vref').replace('$&i(vdd)','$&i(vdd) $&v(shp) $&v(cm) $&v(corep) $&v(coren)');(leaf/'fixture.cir').write_text(deck)
 with (leaf/'tool.log').open('x') as f:state=run_bounded(['ngspice','-b','fixture.cir'],f,leaf/'run.json',90,cwd=leaf,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),metadata={'deck_sha256':sha(leaf/'fixture.cir'),'R_scale':scale},interval_s=.5)
 log=(leaf/'tool.log').read_text();rows={}
 for line in log.splitlines():
  if line.startswith('ROW '):
   t=line.split();vals=list(map(float,t[2:]));assert len(vals)==11 and all(map(math.isfinite,vals));rows[t[1]]=vals
 errors=[x for x in log.splitlines() if re.search(r'(?i)(^Error|fatal|timestep too small|doAnalyses:)',x)];rec={'scale':None if a.matched_ohms else scale,'R_P_ohm':rp,'R_N_ohm':rn,'rows':rows,'columns':['isense_V','vped_V','vref_buf_V','vp_V','vn_V','vped_ref_V','supply_current_A','external_P_V','external_N_V','core_P_V','core_N_V'],'status':'passed' if state['returncode']==0 and len(rows)==9 and 'QUALIFICATION_END' in log and not errors else 'failed','watchdog_status':state['status'],'returncode':state['returncode'],'wall_s':state['wall_s'],'errors':errors};results.append(rec);(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n');print(scale,rec['status'],state['wall_s'],flush=True)
assert all(r['status']=='passed' for r in results)
