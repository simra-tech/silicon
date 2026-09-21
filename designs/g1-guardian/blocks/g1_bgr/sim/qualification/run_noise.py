#!/usr/bin/env python3
"""Single bounded standalone C-PEX reference AC PSRR/output-noise pilot."""
import argparse,hashlib,json,re,shutil,subprocess,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent; PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True);a=ap.parse_args()
 assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 out=HERE/'runs'/a.run_id;out.mkdir(parents=True,exist_ok=False)
 shutil.copy(Path(__file__),out/Path(__file__).name)
 shutil.copy(HERE/'.spiceinit',out/'.spiceinit');shutil.copy(HERE.parent/'postlayout/g1_bgr_pex.spice',out/'pex.spice')
 deck='* BGR standalone C-PEX AC noise/PSRR pilot\n'+''.join(f'.lib {PDK}/libs.tech/ngspice/models/{lib}.lib {corner}\n' for lib,corner in [('cornerHBT','hbt_typ'),('cornerMOShv','mos_tt'),('cornerRES','res_typ')])+'''.include pex.spice
.option gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7
.temp 27
.global sub!
Vsub sub! 0 0
Vdd vdd 0 dc 3.3 ac 1
Vr4 r4 0 0
Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr
Vload iptat 0 1
Cload vref 0 1p
.control
set numdgt=15
set wr_singlescale
set wr_vecnames
ac dec 50 .1 100Meg
let rejection = -db(v(vref))
wrdata psrr.dat rejection
noise v(vref) Vdd dec 50 1 10Meg
setplot noise1
wrdata noise.dat onoise_spectrum
setplot noise2
print onoise_total
quit
.endc
.end
'''
 (out/'noise.cir').write_text(deck); start=time.monotonic();timed=False
 with (out/'noise.log').open('w') as log:
  try:proc=subprocess.run(['ngspice','-b','noise.cir'],cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=120);rc=proc.returncode
  except subprocess.TimeoutExpired:timed=True;rc=None
 log=(out/'noise.log').read_text(errors='replace');man={'command':['python3','run_noise.py',*__import__('sys').argv[1:]],'image_id':a.image_id,'pdk_commit':(PDK/'COMMIT').read_text().strip(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'git_commit':subprocess.check_output(['git','-c','safe.directory=/work','rev-parse','HEAD'],text=True).strip(),'runner_sha256':sha(Path(__file__)),'pex_sha256':sha(out/'pex.spice'),'deck_sha256':sha(out/'noise.cir'),'model_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'status':'not run' if timed else 'failed','timed_out':timed,'watchdog_seconds':120,'solver_exit':rc,'wall_seconds':time.monotonic()-start,'limitations':'Standalone ideal1V IPTAT/1pF VREF fixture;capacitance-only PEX ignores well/fill/wire-R effects;positive PSRR rejection convention;noise model predictions only;no acceptance budget adopted.'}
 try:
  ps=np.loadtxt(out/'psrr.dat',skiprows=1);noise=np.loadtxt(out/'noise.dat',skiprows=1);m=re.search(r'onoise_total\s*=\s*([-+0-9.eE]+)',log)
  if rc==0 and m and np.isfinite(ps).all() and np.isfinite(noise).all() and abs(noise[-1,0]-1e7)<1 and abs(ps[-1,0]-1e8)<1 and not re.search(r'(?im)^Error|analysis aborted',log):
   man.update(status='passed',noise_1Hz_10MHz_rms_V=float(m.group(1)),psrr_1Hz_dB=float(np.interp(1,ps[:,0],ps[:,1])),psrr_1kHz_dB=float(np.interp(1000,ps[:,0],ps[:,1])))
 except (OSError,ValueError,IndexError):pass
 (out/'manifest.json').write_text(json.dumps(man,indent=2)+'\n'); print(json.dumps(man),flush=True)
if __name__=='__main__':main()
