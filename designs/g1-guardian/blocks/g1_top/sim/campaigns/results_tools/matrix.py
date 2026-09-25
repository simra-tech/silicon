import os
SIM=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import csv,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from gen import *
S=os.path.join(SIM,'campaigns','night_20260924_run','summary.csv')
rows=list(csv.DictReader(open(S)))
byid={r['id']:r for r in rows}
import glob
for p in glob.glob(os.path.join(SIM,'logs','*_r4_c1414m.log')):
    i=re.search(r'functional_(.+_r4_c1414m)\.log$',os.path.basename(p)).group(1)
    byid.setdefault(i,{'id':i,'log':os.path.basename(p)})
used=set(); out=[]
def T(t): return 'm40C' if t==-40 else '%dC'%t
H='| Case | Corner | T (°C) | Status | trip_d (µs) | GATE < 1 V (µs) | GATE < 0.33 V (µs) | Cause | VDDA (µA) | Wall (s) | Log |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |'
def pick(base):
    c=[i for i in byid if i==base+'_c1414m' or (i.startswith(base+'_r') and i.endswith('_c1414m') and 'vdd' not in i[len(base):])]
    infos=[(i,info(byid[i]['log'])) for i in c]
    valid=[(i,x) for i,x in infos if x['status']=='completed' and not x.get('mism')]
    for i,_ in infos: used.add(i)
    if valid:
        valid.sort(key=lambda p: len(p[0])); return valid[0],[v[0] for v in valid[1:]],infos
    r4=[p for p in infos if '_r4_' in p[0]]
    if r4: return r4[0],[],infos
    infos.sort(key=lambda p: len(p[0])); return infos[0],[],infos
cases=sys.argv[1].split(',') if len(sys.argv)>1 else ['c_mid','c','e20','f_mid','b_s','q']
stat={}
for case in cases:
    print('\n#### '+case+'\n'); print(H)
    for corner in ('tt','ss','ff'):
        for t in (-40,27,85,125):
            base='%s_%s_%s'%(case,corner,T(t))
            if not any(i.startswith(base) for i in byid): continue
            (i,x),dups,allx=pick(base)
            rr=row(case,x)
            if dups: rr[0]+=' (identical valid duplicate: %s)'%', '.join('`%s`'%d for d in dups)
            stat[rr[0].split(' (')[0]]=stat.get(rr[0].split(' (')[0],0)+1
            print('| %s | %s | %d | '%(case,corner,t)+' | '.join(rr)+' |')
print('\n', stat, file=sys.stderr)
