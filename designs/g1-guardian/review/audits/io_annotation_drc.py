#!/usr/bin/env python3
"""Stock DRC comparison of preserved standalone IO recognition diagnostic."""
import collections,hashlib,json,os,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path
import pya
R=Path(__file__).resolve().parents[4];out=R/'designs/g1-guardian/review/audits/io-annotation-drc-20260921';out.mkdir(exist_ok=False)
P=Path('/foss/pdks/ihp-sg13g2');deck=P/'libs.tech/klayout/tech/drc/ihp-sg13g2.drc';os.environ['KLAYOUT_PATH']=str(P/'libs.tech/klayout')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
result={'scope':'Non-production standalone pad diagnostic; stock full hard+recommended rules unchanged','pdk_commit':(P/'COMMIT').read_text().strip(),'klayout_version':pya.__version__,'deck_sha256':sha(deck),'script_sha256':sha(Path(__file__)),'checks':[]}
for name,gds in [('baseline',P/'libs.ref/sg13g2_io/gds/sg13g2_io.gds'),('annotation',R/'build/scratch/io-recognition-20260921/sg13g2_io_annotation_only.gds')]:
    report=out/(name+'.lyrdb');cmd=['klayout','-b','-zz','-r',str(deck),'-rd','input='+str(gds),'-rd','topcell=sg13g2_IOPadAnalog','-rd','report='+str(report),'-rd','run_mode=deep','-rd','threads=1'];start=time.monotonic()
    with (out/(name+'.log')).open('w') as log:run=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    cats=collections.Counter(x.findtext('category').strip("'") for x in ET.parse(report).findall('./items/item')) if report.exists() else None
    result['checks'].append({'name':name,'command':[v.replace(str(R)+'/','') for v in cmd],'input_sha256':sha(gds),'status':'passed' if run.returncode==0 and cats is not None and not cats else 'failed','exit_code':run.returncode,'wall_seconds':time.monotonic()-start,'categories':dict(cats) if cats is not None else None,'markers':sum(cats.values()) if cats is not None else None})
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['checks'],indent=2))
