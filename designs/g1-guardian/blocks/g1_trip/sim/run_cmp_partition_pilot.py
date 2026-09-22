#!/usr/bin/env python3
import argparse,json,subprocess,sys
from pathlib import Path
SIM=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True);a=p.parse_args();out=SIM/'qualification'/a.run_id;out.mkdir(exist_ok=False);(out/'driver.py').write_text(Path(__file__).read_text());results=[]
for i,temp in enumerate([-40,125]):
 if (out/'PAUSE_REQUESTED').exists():break
 leaf=f'{a.run_id}-p{i:02d}';cmd=[sys.executable,str(SIM/'run_cmp_qualification.py'),'--run-id',leaf,'--image-id',a.image_id,'--seeds','62001','--temps',str(temp),'--cm','.75','--maxstep-ns','.2','--tight-trap','--netlist','cell-pex']
 rc=subprocess.run(cmd,cwd=SIM).returncode;row={'run':leaf,'temperature_C':temp,'runner_returncode':rc};results.append(row)
 if rc==0:row['comparison_returncode']=subprocess.run([sys.executable,str(SIM/'compare_cmp_partition.py'),'--reference','cmp-cellpex-smoke-b1-20260922-a','--candidate',leaf,'--seed','62001'],cwd=SIM).returncode
 (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
