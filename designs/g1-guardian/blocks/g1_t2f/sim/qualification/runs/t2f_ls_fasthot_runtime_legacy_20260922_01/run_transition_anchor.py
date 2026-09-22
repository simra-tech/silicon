#!/usr/bin/env python3
"""Shorter endpoint on a frozen full LS/receiver fixture for runtime comparison.
This numerical anchor does not replace the complete90us control-transition check.
"""
import argparse,hashlib,json,math,re,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--source-run',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--stop-us',type=float,default=6);a=ap.parse_args();assert 0<a.stop_us<90
 source=HERE/'runs'/a.source_run;out=HERE/'runs'/a.run_id;out.mkdir(exist_ok=False);shutil.copy(__file__,out/Path(__file__).name)
 for name in ['bgr.spice','t2f.spice','ls.spice','.spiceinit','route_estimates.json']:shutil.copy(source/name,out/name)
 src=json.loads((source/'manifest.json').read_text());deck=(source/'transitions.cir').read_text();assert deck.count('tran 5n 90u')==1;deck=deck.replace('tran 5n 90u',f'tran 5n {a.stop_us:g}u');(out/'transitions.cir').write_text(deck)
 models={str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))};assert models==src['model_sha256']
 m={'command':sys.argv,'image_id':a.image_id,'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'source_run':a.source_run,'source_manifest_sha256':sha(source/'manifest.json'),'original_deck_sha256':sha(source/'transitions.cir'),'deck_sha256':sha(out/'transitions.cir'),'model_sha256':models,'pdk_commit':(PDK/'COMMIT').read_text().strip(),'stop_us':a.stop_us,'conditions':src['conditions'],'source_sha256':{n:sha(out/n) for n in ['bgr.spice','t2f.spice','ls.spice','.spiceinit','route_estimates.json']},'status':'not run','scope':'Numerical same-fixture early-time runtime anchor only; laterenable/mode/r4 checks notrun in short fixture.'};save=lambda:(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');save();start=time.monotonic()
 with (out/'transitions.log').open('w') as log,(out/'transitions.stderr').open('w') as err:
  try:rc=subprocess.run(['ngspice','-b','transitions.cir'],cwd=out,stdout=log,stderr=err,timeout=300).returncode;timed=False
  except subprocess.TimeoutExpired:rc=None;timed=True
 m.update(solver_exit=rc,timed_out=timed,wall_seconds=time.monotonic()-start)
 try:
  with (out/'transitions.dat').open() as f:next(f);d=[list(map(float,line.split())) for line in f if line.strip()]
  if rc==0 and d and all(len(r)==18 and all(map(math.isfinite,r)) for r in d) and abs(d[-1][0]-a.stop_us*1e-6)<1e-12:m.update(status='passed',rows=len(d),final_values=d[-1],waveform_sha256=sha(out/'transitions.dat'))
  else:m['status']='not run' if timed else 'failed'
 except (OSError,ValueError,IndexError,StopIteration):m['status']='not run' if timed else 'failed'
 save();print(json.dumps({k:v for k,v in m.items() if k not in ['model_sha256','ngspice']},indent=2))
if __name__=='__main__':main()
