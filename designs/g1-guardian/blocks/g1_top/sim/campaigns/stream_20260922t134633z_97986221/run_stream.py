#!/usr/bin/env python3
"""Stream batch transient data to an immutable raw file, retaining partial observations.

A streamed raw file is not a restart state. Completed endpoints and circuit
acceptance are separate. Source deck's measurements are replaced by postprocessing.
"""
import argparse,datetime,hashlib,json,math,os,re,shutil,struct,subprocess,sys,uuid
from pathlib import Path
from run_bounded import run_bounded,atomic_json
from run_top import RTL_FILES
from simulation_errors import solver_failure
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_raw(path):
 with path.open('rb') as f:
  header=[]
  while True:
   line=f.readline()
   if not line:raise ValueError('raw binary header incomplete')
   header.append(line.decode('ascii').rstrip())
   if line.strip()==b'Binary:':break
  h='\n'.join(header)
  if re.search(r'^Flags:.*complex',h,re.M):raise ValueError('complex plot unsupported')
  nv=int(re.search(r'^No\. Variables:\s*(\d+)',h,re.M)[1])
  point_field=re.search(r'^No\. Points:[ \t]*(\d*)',h,re.M)
  declared=int(point_field[1]) if point_field and point_field[1] else None
  start=header.index('Variables:')+1;names=[]
  for line in header[start:-1]:
   p=line.split()
   if len(p)>=3 and p[0].isdigit():names.append(p[1])
  if len(names)!=nv or names[0]!='time':raise ValueError('unexpected variables/scale')
  raw=f.read();width=nv*8;count=len(raw)//width;extra=len(raw)%width
  # ngspice raw doubles use producer-native byte order; campaign records architecture.
  rows=list(struct.iter_unpack('='+('d'*nv),raw[:count*width]))
  if not rows or any(not all(map(math.isfinite,r)) for r in rows):raise ValueError('empty/nonfinite raw records')
  if rows[0][0]!=0 or any(q[0]<p[0] for p,q in zip(rows,rows[1:])):raise ValueError('invalid times')
 return names,rows,dict(declared_points=declared,complete_records=count,trailing_bytes=extra,header=h)
def normal_name(n):
 if n=='time' or n.startswith(('v(','i(')):return n
 return 'i('+n[:-7]+')' if n.endswith('#branch') else 'v('+n+')'
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source_deck',type=Path);ap.add_argument('--image-id',required=True);ap.add_argument('--timeout',type=float,default=900);ap.add_argument('--threads',type=int,default=2);a=ap.parse_args()
 if a.timeout<=0 or not 1<=a.threads<=8:ap.error('invalid resources')
 source=a.source_deck.resolve();s=source.read_text();before,control=s.split('.control\n',1);tran=next(l for l in control.splitlines() if l.startswith('tran '));stop_token=tran.split()[2]
 def spice_num(v):
  suffix={'u':1e-6,'n':1e-9,'m':1e-3,'p':1e-12};return float(v[:-1])*suffix[v[-1]] if v[-1] in suffix else float(v)
 stop=spice_num(stop_token)
 # ngspice lowercases d_cosim's sim_args. Keep executable path components
 # lowercase so they work on case-sensitive receiving-host filesystems.
 tag='stream_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ').lower()+'_'+uuid.uuid4().hex[:8];out=HERE/'campaigns'/tag;out.mkdir(parents=True,exist_ok=False)
 for script in ['run_stream.py','run_top.py','run_bounded.py','simulation_errors.py']:
  shutil.copyfile(HERE/script,out/script)
 (out/'.spiceinit').write_text((HERE/'.spiceinit').read_text()+f'\nset num_threads={a.threads}\nset filetype=binary\n')
 # Own the executable and input stimulus: another runner may rebuild the common
 # build/g1_top executable, so a campaign must not depend on that mutable path.
 vvp=out/'g1_dig_cosim.vvp'
 compile_command=['iverilog','-g2005','-Wall','-Wno-timescale','-o',str(vvp)]+RTL_FILES
 compiled=subprocess.run(compile_command,capture_output=True,text=True)
 (out/'compile.log').write_text(compiled.stdout+compiled.stderr)
 if compiled.returncode:
  atomic_json(out/'assessment.json',dict(completion='failed',electrical_acceptance='not assessed',error='RTL compilation failed',returncode=compiled.returncode));raise SystemExit(1)
 before=re.sub(r'(sim_args=\[")[^"]+("\])',lambda m:m[1]+str(vvp)+m[2],before)
 stimulus_sha={}
 for index,match in enumerate(list(re.finditer(r'input_file="([^"]+)"',before))):
  old=Path(match[1]);new=out/('stimulus_%d.txt'%index);shutil.copyfile(old,new)
  stimulus_sha[str(old).replace(str(ROOT)+'/', '')]=sha(new);before=before.replace(str(old),str(new))
 deck=out/'fixture.cir';deck.write_text(before+'.'+tran+'\n.end\n');raw=out/'transient.raw'
 included={}
 for p in re.findall(r'^\.include\s+(\S+)',before,re.M):
  path=Path(p)
  if path.exists():included[str(path).replace(str(ROOT)+'/', '')]=sha(path)
 pdk=Path('/foss/pdks/ihp-sg13g2')
 md=dict(image_id=a.image_id,options={k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},pdk_commit=(pdk/'COMMIT').read_text().strip(),source_deck=str(source.relative_to(ROOT)),source_deck_sha256=sha(source),deck_sha256=sha(deck),runner_sha256=sha(Path(__file__)),init_sha256=sha(out/'.spiceinit'),included_sha256=included,model_sha256={str(p.relative_to(pdk)):sha(p) for p in sorted((pdk/'libs.tech/ngspice/models').rglob('*')) if p.is_file()},ngspice_version=subprocess.check_output(['ngspice','-v'],text=True),byteorder=sys.byteorder,scope='Same analog/RTL source deck, batch .tran with binary streaming instead of control tran/postprocessing; numerical equivalence requires qualification.')
 md.update(rtl_sha256={str(Path(p).relative_to(ROOT)):sha(Path(p)) for p in RTL_FILES},vvp_sha256=sha(vvp),compile_command=compile_command,stimulus_sha256=stimulus_sha,iverilog_version=subprocess.run(['iverilog','-V'],capture_output=True,text=True).stdout)
 md['runner_source_snapshots']={name:sha(out/name) for name in ['run_stream.py','run_top.py','run_bounded.py','simulation_errors.py']}
 env=dict(os.environ)
 env['LD_LIBRARY_PATH']='/foss/tools/iverilog/lib'+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 md['icarus_library_path']=env['LD_LIBRARY_PATH']
 with (out/'run.log').open('x') as log:r=run_bounded(['ngspice','-b','-r',str(raw),str(deck)],log,out/'run.json',a.timeout,cwd=out,env=env,metadata=md,interval_s=5)
 result=dict(solver_status=r['status'],wall_s=r['wall_s'],completion='not run to completion' if r['status'] in ['timeout','interrupted'] else 'failed',electrical_acceptance='not assessed')
 try:
  names,rows,meta=read_raw(raw);result.update(raw=meta,raw_sha256=sha(raw),observed_end_s=rows[-1][0],requested_end_s=stop)
  bad=solver_failure((out/'run.log').read_text())
  if bad:result['solver_failure_diagnostic']=bad.group(0)
  result['completion']='passed' if r['status']=='completed' and not bad and abs(rows[-1][0]-stop)<1e-12 and meta['declared_points']==len(rows) and meta['trailing_bytes']==0 else 'not run to completion' if r['status'] in ['timeout','interrupted'] else 'failed'
  # Save every complete record, including partial runs, without repairing raw header.
  dest=out/'observations.tsv'
  with dest.open('x') as f:
   f.write(' '.join(map(normal_name,names))+'\n')
   for row in rows:f.write(' '.join(format(v,'.17g') for v in row)+'\n')
  result['observation_sha256']=sha(dest);result['partial_observations_are_not_restart']='No analog integrator or RTL process state is restored from these vectors.'
 except (OSError,ValueError,IndexError,TypeError) as e:result['error']=str(e).replace(str(ROOT)+'/', '')
 atomic_json(out/'assessment.json',result);print(out.relative_to(ROOT));print(json.dumps({k:v for k,v in result.items() if k!='raw'},indent=2))
 if result['completion']!='passed':raise SystemExit(1)
if __name__=='__main__':main()
