#!/usr/bin/env python3
"""Bounded independent SDF checker qualification and matching-netlist pilot."""
import argparse,datetime,hashlib,json,re,shutil,subprocess,sys,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded,atomic_json
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--image-id',required=True)
ap.add_argument('--cvc',type=Path,default=ROOT/'build/cvc-source/build64/cvc64')
ap.add_argument('--mode',choices=['checker','annotation','functional'],default='checker')
ap.add_argument('--corner',choices=['nom_typ_1p20V_25C','nom_slow_1p08V_125C','nom_fast_1p32V_m40C'],default='nom_typ_1p20V_25C')
ap.add_argument('--timeout',type=float,default=300);a=ap.parse_args();a.cvc=a.cvc.resolve()
out=HERE/'campaigns'/('cvc_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
md=dict(options={k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},image_id=a.image_id,cvc_sha256=sha(a.cvc),cvc_source_commit=subprocess.check_output(['git','-c','safe.directory='+str(ROOT/'build/cvc-source'),'-C',str(ROOT/'build/cvc-source'),'rev-parse','HEAD'],text=True).strip(),runner_sha256=sha(Path(__file__)),pdk_commit=Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip())
results=[]
def run(name,cmd,scope,expected):
 dest=out/name;dest.mkdir();shutil.copyfile(HERE/'checker.sdf',dest/'checker.sdf')
 with (dest/'tool.log').open('x') as log:r=run_bounded(cmd,log,dest/'run.json',a.timeout,cwd=dest,metadata=md,interval_s=5)
 text=(dest/'tool.log').read_text();r['scope']=scope
 r['acceptance']='passed' if r['status']=='completed' and expected in text and not re.search(r'CHECKER_FAIL|SOME TESTS FAILED|ERROR\*\*|FATAL',text,re.I) else 'failed'
 r['warning_lines']=[l for l in text.splitlines() if re.search(r'\b(?:WARN|ERROR|FATAL)\*\*|timing violation|unsupported|SDF.*(fail|skip|unmatched)',l,re.I)][:100]
 if a.mode!='checker' and r['warning_lines']:r['acceptance']='failed'
 atomic_json(dest/'run.json',r);results.append(dict(case=name,status=r['status'],acceptance=r['acceptance'],warning_lines=r['warning_lines'],wall_s=r['wall_s']));print(name,r['acceptance'],flush=True)
if a.mode=='checker':
 md['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in [HERE/'tb_sdf_checker.v',HERE/'checker.sdf']}
 for annotated in [False,True]:
  run('annotated' if annotated else 'clean',[str(a.cvc),'+interp']+(['+define+ANNOTATE'] if annotated else [])+[str(HERE/'tb_sdf_checker.v')],'Deliberate violation must be detected after SDF, clean control must stay quiet','CHECKER_EXPECTED_VIOLATION_PASS' if annotated else 'CHECKER_EXPECTED_CLEAN_PASS')
else:
 nl=HERE.parent/'layout/g1_digital.nl.v';built=ROOT/'build/g1_digital/final_run7/nl/g1_digital.nl.v'
 if sha(nl)!=sha(built):raise SystemExit('matching netlist provenance failed')
 sdf=ROOT/'build/g1_digital/final_run7/sdf'/a.corner/('g1_digital__'+a.corner+'.sdf');shutil.copyfile(sdf,out/'input.sdf')
 fixture=(HERE/'tb_g1_digital.v').read_text().replace('module tb_g1_digital;','module tb_g1_digital;\ninitial begin $sdf_annotate("'+str(out/'input.sdf')+'",dut,,,"MAXIMUM"); $display("SDF_ANNOTATION_RETURNED"); end')
 if a.mode=='annotation':fixture=fixture.replace('module tb_g1_digital;','module tb_g1_digital;\ninitial begin #1000;$display("ANNOTATION_PILOT_END");$finish;end')
 tb=out/'testbench.v';tb.write_text(fixture);models=Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog')
 sources=[models/'sg13g2_udp.v',models/'sg13g2_stdcell.v',nl,tb]
 md['source_sha256']={str(p):sha(p) for p in sources+[sdf]}
 run(a.mode,[str(a.cvc),'+interp','+maxdelays','+define+GLS',str(sources[0]),'-v',str(sources[1]),str(nl),str(tb)],'Matching run7 netlist and unchanged stock PDK timing model','ANNOTATION_PILOT_END' if a.mode=='annotation' else 'ALL TESTS PASSED')
atomic_json(out/'campaign.json',dict(md,cases=results,status='passed' if all(r['acceptance']=='passed' for r in results) else 'failed'))
print(out)
if any(r['acceptance']!='passed' for r in results):raise SystemExit(1)
