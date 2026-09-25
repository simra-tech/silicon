import os
SIM=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import csv,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from gen import *
S=os.path.join(SIM,'campaigns','night_20260924_run','summary.csv')
rows=list(csv.DictReader(open(S)))
ids=[r['id'] for r in rows]
cnt={}
inv=[];tmo=[];fail=[]
def repl(i):
    base=i[:-len('_c1414m')]
    c=[j for j in ids if j!=i and j.startswith(base+'_r') ]
    return ', '.join('`%s`'%j for j in c) or '—'
for r in rows:
    x=info(r['log']); i=r['id']
    if x.get('mism') or 'cosim' in x['status']:
        k='invalid'; inv.append('| `%s` | %s%s | %s | %s | `%s` |'%(i,x['status'],', log contains "mismatched XSPICE"' if x.get('mism') else '',x.get('wall') or '—',repl(i),r['log']))
    elif x['status']=='timeout':
        k='timeout'; tmo.append('| `%s` | timeout (exit %s) at %s µs sim | %s | %s | `%s` |'%(i,x.get('exit'),f3(float(x['simt'])*1e6,1) if x.get('simt') else '?',x.get('wall'),repl(i),r['log']))
    elif x['status']=='completed': k='completed'
    elif x['status']=='running': k='running'
    else:
        k='failed'; fail.append('| `%s` | %s | %s | %s | `%s` |'%(i,verdict('q',x),x.get('wall'),repl(i),r['log']))
    cnt[k]=cnt.get(k,0)+1
print('COUNTS',cnt,len(rows),file=sys.stderr)
print('#### Invalid (RTL-loading defect)\n\n| Job id | Status / reason | Wall (s) | Re-run id(s) | Log |\n| --- | --- | --- | --- | --- |'); print('\n'.join(inv))
print('\n#### Timeouts\n\n| Job id | Status | Wall (s) | Re-run id(s) | Log |\n| --- | --- | --- | --- | --- |'); print('\n'.join(tmo))
print('\n#### Numerical failures\n\n| Job id | Status | Wall (s) | Re-run id(s) | Log |\n| --- | --- | --- | --- | --- |'); print('\n'.join(fail))
