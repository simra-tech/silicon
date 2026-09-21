#!/usr/bin/env python3
"""Compare streaming records with saved control-mode reference vectors.

Eight binary64 ULPs allow the reference's 16-significant-digit text rounding.
No interpolation is used: every compared time and value must match in row order.
Partial-prefix parity never promotes a timed-out run to completed status.
"""
import argparse,hashlib,json,math
from pathlib import Path
from check_campaign import read_wave
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('stream');ap.add_argument('reference');a=ap.parse_args()
 out=HERE/'campaigns'/a.stream;assessment=json.loads((out/'assessment.json').read_text())
 cols,rows=read_wave(out/'observations.tsv');idx={c:i for i,c in enumerate(cols)}
 tests={};comparisons=[]
 for suffix in ['', '_state']:
  path=HERE/'results/waves'/(a.reference+suffix+'.txt');rc,rr=read_wave(path)
  tests['columns'+suffix]=all(c in idx for c in rc)
  tests['row_count'+suffix]=len(rows)<=len(rr) and (assessment['completion']!='passed' or len(rows)==len(rr))
  maximum={};bad=0
  for i,c in enumerate(rc):
   ulps=[]
   for r,s in zip(rr,rows):
    x,y=r[i],s[idx[c]];u=abs(x-y)/max(math.ulp(x),math.ulp(y));ulps.append(u);bad+=u>8
   maximum[c]=max(ulps)
  tests['eight_ulp_values'+suffix]=bad==0
  comparisons.append(dict(reference=str(path.relative_to(HERE)),reference_sha256=sha(path),reference_rows=len(rr),compared_rows=min(len(rr),len(rows)),failed_values=bad,max_ulp_by_column=maximum))
 result=dict(stream=a.stream,reference=a.reference,criterion=__doc__,tests=tests,comparison= comparisons,parity='passed' if all(tests.values()) else 'failed',endpoint_completion=assessment['completion'],observation_sha256=sha(out/'observations.tsv'),scope='Only the reference saved columns; other streamed signals lack a separate original vector reference. Circuit acceptance remains separate.')
 dest=out/'reference_parity.json'
 with dest.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
 if result['parity']!='passed':raise SystemExit(1)
if __name__=='__main__':main()
