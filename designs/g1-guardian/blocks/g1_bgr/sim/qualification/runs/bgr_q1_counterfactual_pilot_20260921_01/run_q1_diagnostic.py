#!/usr/bin/env python3
"""Fixed-draw Q1-area counterfactual; not a hardware or yield improvement.
No model-card edit and no random-distribution scaling. Alter one realized device
area to its nominal value while auditing every other representative device draw.
"""
import argparse,hashlib,json,math,re,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprint(text):return {k.lower():v for k,v in re.findall(r'(?m)^(@[^\s]+)\s*=\s*([-+0-9.eE]+)',text)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--seeds',default='42081,42093,42031');a=ap.parse_args()
 assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 out=HERE/'runs'/a.run_id;out.mkdir(parents=True,exist_ok=False)
 source=HERE/'runs/bgr_mc20_20260921_01/pex_mm.spice'
 shutil.copy(source,out/'bgr.spice');shutil.copy(HERE/'.spiceinit',out/'.spiceinit');shutil.copy(Path(__file__),out/Path(__file__).name)
 queries=[]
 for line in source.read_text().splitlines():
  p=line.split()
  if not p:continue
  device=p[0].lower()
  if p[0].startswith('XM'):queries.append(f'@n.xbgr.{device}.n{p[5]}[delvto]')
  elif p[0].startswith('XR'):queries.append(f'@n.xbgr.{device}.nr1[nsmm_rsh]')
  elif p[0].startswith('XQ'):queries.append(f'@q.xbgr.{device}.qnpn13g2[area]')
 q1='@q.xbgr.xq56.qnpn13g2[area]';assert q1 in queries
 dump=''.join(f'print {q}\n' for q in queries)
 manifest={'command':sys.argv,'image_id':a.image_id,'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'pdk_commit':(PDK/'COMMIT').read_text().strip(),'source_sha256':sha(source),'runner_sha256':sha(Path(__file__)),'models_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'queried_device_parameters':queries,'counterfactual':'After initial OP set only actual Q1 VBIC area to1, the nominal value of its qarea. No reset or RNG reseeding; verify remaining draws exactly. Not a physically implemented fix.','cases':[]}
 for seed in map(int,a.seeds.split(',')):
  for variant in ['all_on','q1_nominal_area']:
   name=f's{seed}_{variant}'
   deck='* BGR fixed-draw Q1 counterfactual\n'+''.join(f'.lib {PDK}/libs.tech/ngspice/models/{lib}.lib {corner}\n' for lib,corner in [('cornerHBT','hbt_typ_mismatch'),('cornerMOShv','mos_tt_mismatch'),('cornerRES','res_typ_mismatch')])
   deck+=f'''.include bgr.spice
.option seed={seed} gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7
.global sub!
Vsub sub! 0 0
Vdd vdd 0 3.3
Vr4 r4 0 0
Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr
Vload iptat 0 1
Cload vref 0 1p
.control
set num_threads=1
set numdgt=15
set wr_singlescale
set wr_vecnames
op
echo FINGERPRINT_BEFORE
'''+dump
   if variant=='q1_nominal_area':deck+=f'alter {q1} = 1\nop\n'
   deck+='echo FINGERPRINT_AFTER_ALTER\n'+dump+'dc temp -40 125 5\necho FINGERPRINT_AFTER_SWEEP\n'+dump
   deck+=f'wrdata {name}.dat v(vref) i(vload) i(vdd) v(vbe) v(dvbe) v(pbias) v(pcasc) v(xbgr.c2) v(xbgr.vbe3) v(xbgr.vd1) v(xbgr.vd2)\nquit\n.endc\n.end\n';(out/(name+'.cir')).write_text(deck)
   start=time.monotonic();timed=False
   with (out/(name+'.log')).open('w') as log:
    try:rc=subprocess.run(['ngspice','-b',name+'.cir'],cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
    except subprocess.TimeoutExpired:rc=None;timed=True
   row={'seed':seed,'variant':variant,'watchdog_seconds':120,'solver_exit':rc,'timed_out':timed,'wall_seconds':time.monotonic()-start,'status':'not run' if timed else 'failed','deck_sha256':sha(out/(name+'.cir'))}
   log=(out/(name+'.log')).read_text(errors='replace');before=fingerprint(log.split('FINGERPRINT_BEFORE')[-1].split('FINGERPRINT_AFTER_ALTER')[0]);after=fingerprint(log.split('FINGERPRINT_AFTER_ALTER')[-1].split('FINGERPRINT_AFTER_SWEEP')[0]);final=fingerprint(log.split('FINGERPRINT_AFTER_SWEEP')[-1]);row['fingerprints']={'before':before,'after_alter':after,'after_sweep':final}
   row['other_draws_status']='passed' if len(before)==len(after)==len(final)==len(queries) and all(before[k]==after[k]==final[k] for k in before if k!=q1) else 'failed'
   row['q1_status']='passed' if q1 in before and q1 in after and q1 in final and ((before[q1]==after[q1]==final[q1]) if variant=='all_on' else float(after[q1])==float(final[q1])==1) else 'failed'
   try:
    with (out/(name+'.dat')).open() as f:next(f);d=[list(map(float,line.split())) for line in f if line.strip()]
    if rc==0 and len(d)==34 and d[-1][0]==125 and all(len(x)==12 and all(map(math.isfinite,x)) for x in d) and not re.search(r'(?im)^Error|Timestep too small|analysis aborted|no such parameter',log):
     v25=next(x[1] for x in d if x[0]==25);tc=(max(x[1] for x in d)-min(x[1] for x in d))/v25/165*1e6;row.update(status='passed',vref25_V=v25,tc_ppm_C=tc,tc_status='passed' if tc<=50 else 'failed',iptat25_A=next(x[2] for x in d if x[0]==25),supply_current25_A=-next(x[3] for x in d if x[0]==25))
    if variant=='all_on':
     old=HERE/'runs'/('bgr_mc20_20260921_01' if seed<=42020 else 'bgr_mc100_20260921_01')/f'mc_{seed}.dat';row['original_vectors_byte_identical']=old.read_bytes()==(out/(name+'.dat')).read_bytes()
   except (OSError,ValueError,IndexError,StopIteration):pass
   manifest['cases'].append(row);(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:v for k,v in row.items() if k!='fingerprints'}),flush=True)
if __name__=='__main__':main()
