#!/usr/bin/env python3
import argparse,json,re,subprocess,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();d=a.directory;shutil.copyfile(__file__,d/'ac_checker.py');s=json.loads((d/'summary.json').read_text());rows=[]
for deck in sorted(d.glob('*.cir')):
 v,m,drive=deck.stem.rsplit('_',2);proc=subprocess.run(['ngspice','-b',str(deck.resolve())],text=True,capture_output=True,timeout=30);log=proc.stdout+proc.stderr;(deck.with_suffix('.log')).write_text(log);vals={n:float(x) for n,x in re.findall(r'^(cp|cn)\s*=\s*([\deE.+-]+)',log,re.M)};matrix=s['results'][v]['modes'][m]['matrix_fF'];col=0 if drive=='P' else 1;expected=[matrix[i][col]*1e-15 for i in range(2)];error=max(abs(vals.get(n,float('inf'))-expected[i]) for i,n in enumerate(['cp','cn']));rows.append({'deck':deck.name,'sha256':hashlib.sha256(deck.read_bytes()).hexdigest(),'returncode':proc.returncode,'observed_F':vals,'expected_F':expected,'max_abs_error_F':error,'tolerance_F':1e-25,'status':'passed' if proc.returncode==0 and error<1e-25 else 'failed'})
(d/'ac_checks.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2));assert all(r['status']=='passed' for r in rows)
