#!/usr/bin/env python3
"""Direct nominal VBIC currents for baseline and isolated density-array candidate."""
import argparse,hashlib,json,math,re,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True);a=ap.parse_args();out=HERE/'runs'/a.run_id;out.mkdir(exist_ok=False);shutil.copy(__file__,out/Path(__file__).name);shutil.copy(HERE/'.spiceinit',out/'.spiceinit');m={'command':sys.argv,'image_id':a.image_id,'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'pdk_commit':(PDK/'COMMIT').read_text().strip(),'model_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'cases':[],'limitations':'DC nominal unit-current comparison only; same emittergeometry0.07x0.9um. Existing CPEX retained; added routing/physicalimplementation notqualified.'};save=lambda:(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');save()
 for variant,source in [('baseline',HERE.parent/'postlayout/g1_bgr_pex.spice'),('density_v2',HERE/'candidates/bgr_array4_density_v2/bgr_array4_density_v2.spice')]:
  shutil.copy(source,out/(variant+'.spice'));devices=[]
  for line in source.read_text().splitlines():
   p=line.split()
   if p and p[0].startswith('XQ') and p[1:4]!=['vss','vss','vss']:devices.append(p[0].lower())
  queries=[f'@q.xbgr.{d}.qnpn13g2[{parameter}]' for d in devices for parameter in ['area','ic','ib']]
  for temp in [-40,25,125]:
   name=f'{variant}_T{temp}';deck='* Direct unitHBT current probe; unchangedmodelcards\n'+''.join(f'.lib {PDK}/libs.tech/ngspice/models/{lib}.lib {corner}\n' for lib,corner in [('cornerHBT','hbt_typ'),('cornerMOShv','mos_tt'),('cornerRES','res_typ')])+f'.include {variant}.spice\n.temp {temp}\n.option gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7\n.global sub!\nVsub sub! 0 0\nVdd vdd 0 3.3\nVr4 r4 0 0\nXbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr\nVload iptat 0 1\nCload vref 0 1p\n.control\nset num_threads=1\nset numdgt=15\nop\n'+''.join('print '+q+'\n' for q in queries)+'print v(vref) i(vload) i(vdd) v(vbe) v(dvbe) v(pbias) v(pcasc)\nquit\n.endc\n.end\n';(out/(name+'.cir')).write_text(deck);start=time.monotonic()
   with (out/(name+'.log')).open('w') as log,(out/(name+'.stderr')).open('w') as err:
    try:rc=subprocess.run(['ngspice','-b',name+'.cir'],cwd=out,stdout=log,stderr=err,timeout=120).returncode;timed=False
    except subprocess.TimeoutExpired:rc=None;timed=True
   log=(out/(name+'.log')).read_text();err=(out/(name+'.stderr')).read_text();values=re.findall(r'(@[^\s]+)\s*=\s*([-+0-9.eE]+)',log);ok=rc==0 and len(values)==len(queries) and all(math.isfinite(float(v)) for k,v in values) and not re.search(r'(?im)^Error|no such parameter|not available|analysis aborted',log+'\n'+err);r={'variant':variant,'temperature_C':temp,'source_sha256':sha(source),'deck_sha256':sha(out/(name+'.cir')),'expected_parameter_count':len(queries),'parameters':{k:float(v) for k,v in values},'solver_exit':rc,'timed_out':timed,'wall_seconds':time.monotonic()-start,'status':'passed' if ok else ('not run' if timed else 'failed')};m['cases'].append(r);save();print(json.dumps({k:v for k,v in r.items() if k!='parameters'}),flush=True)
   if not ok:return
if __name__=='__main__':main()
