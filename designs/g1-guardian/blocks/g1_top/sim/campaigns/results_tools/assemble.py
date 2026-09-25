import os
SIM=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys,glob,os,re,subprocess,datetime
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from gen import *
L=os.path.join(SIM,'logs')
def lg(p):
    m=sorted(os.path.basename(x) for x in glob.glob(L+'/'+p)); assert len(m)==1,(p,m); return m[0]
TOOLS=os.path.dirname(os.path.abspath(__file__))
import tempfile; os.chdir(tempfile.mkdtemp())
def sh(c): return subprocess.run(c,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
for s in ['supply','k1','hot','n2','full','thr']: open('sec_%s.md'%s,'w').write(sh('python3 %s/other.py %s'%(TOOLS,s)).stdout)
r=sh('python3 %s/matrix.py'%TOOLS); open('matrix.md','w').write(r.stdout)
r2=sh('python3 %s/inval.py'%TOOLS); open('inval.md','w').write(r2.stdout)
cnt=eval(r2.stderr.split('COUNTS')[1].rsplit(' ',1)[0])
# power-up
pw=[]
for case in ('gA','gA_pd','gB','gB_pd'):
    for lab,pat in [('tt, 27 °C','%s_pex_c1414_beh_tt_27C_ovr-bgrsch_padsnodcn_clockfix_functional_c1414pwr.log'),('ss, 125 °C','%s_pex_c1414_beh_ss_125C_*_r3_c1414m.log'),('ff, −40 °C','%s_pex_c1414_beh_ff_-40C_*_r3_c1414m.log')]:
        ms=glob.glob(L+'/'+pat%case)
        if not ms: pw.append('| %s | %s | not run | — | — | — | — | — |'%(case,lab)); continue
        n=os.path.basename(ms[0]); x=info(n); p=x['POWERUP']
        io=case.startswith('gA'); gm=float(g('GATE_max_EN_low',p))
        st=('failed (GATE high, IO first; expected, P1)' if gm>1 else 'passed') if io else ('passed' if gm<0.33 else 'failed')
        fr=g('GATE_above_1V_from_us',p); to=g('to_us',p)
        ft='%.2f–%.2f'%(float(fr)*1e6,float(to)*1e6) if fr else 'never'
        pw.append('| %s | %s | %s | %.4f | %s | %.2f | %s | `%s` |'%(case,lab,st,gm,ft,float(g('charge_As',p))*1e6,x['wall'],n))
for case in ('gA','gA_pd','gB','gB_pd'):
    n=lg('%s_pex_c1414_beh_tt_27C_clockfix_functional_c1414n1.log'%case); x=info(n); p=x['POWERUP']
    if x['status']=='completed':
        gm=float(g('GATE_max_EN_low',p)); pw.append('| %s, stock pads | tt, 27 °C | %s | %.4f | never | %.2f | %s | `%s` |'%(case,'passed' if gm<0.33 else 'failed',gm,float(g('charge_As',p))*1e6,x['wall'],n))
    else: pw.append('| %s, stock pads | tt, 27 °C | not run to completion (timeout) | — | — | — | %s | `%s` |'%(case,x['wall'],n))
# osc
oh='| Run | Corner, T, VDD | Integration, max step, receiver | Status | f_osc (MHz) | OSC VDD current (µA) | VDDA (µA) | Wall (s) | Log |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |'
orows=[]
for p in sorted(glob.glob(L+'/osc*c1414*.log')):
    n=os.path.basename(p); x=info(n)
    if x.get('mism') or 'cosim' in x['status']: continue
    tag=n.split('functional_')[-1][:-4]
    pre=n.split('_c1414_tl_')[1].split('_clockfix')[0]; opts=n.split('_clockfix_')[1].split('_functional')[0]
    cor=pre.split('_')[0]; T=pre.split('_')[1].replace('C',' °C').replace('-','−')
    vdd='1.32 V' if 'vdd1p32' in pre else ('1.08 V' if 'vdd1p08' in pre else '1.2 V')
    meth='gear' if 'gear' in pre else 'trap'
    ms=re.search(r'maxstep([0-9.]+)ns',opts); ms=(ms.group(1)+' ns') if ms else 'none'
    rx='Schmitt' if 'rxschmitt' in opts else 'bridge'
    extra=[]
    if 'bgrsch' in pre: extra.append('`bgr=sch`')
    if 'maxord1' in opts: extra.append('maxord 1')
    if 'klu' in opts: extra.append('KLU')
    if 'gmin1em11' in opts: extra.append('gmin 1e-11')
    if 'reltol0002' not in opts: extra.append('default tolerances' if meth=='trap' else '')
    v=verdict('osc',x)
    if v=='passed': v='completed'
    f=g('f_osc_MHz',x['CLOCK']) if x['status']=='completed' else '—'
    orows.append((tag,'| `%s` | %s, %s, %s | %s, %s, %s%s | %s | %s | %s | %s | %s | `%s` |'%(tag,cor,T,vdd,meth,ms,rx,(', '+', '.join(e for e in extra if e)) if any(extra) else '',v,f,f3(g('osc',x['SUPPLY_uA']),1) if f!='—' else '—',f3(g('VDDA',x['SUPPLY_uA']),0) if f!='—' else '—',x.get('wall') or 'running',n)))
osc=oh+'\n'+'\n'.join(r for _,r in orows)
# t2f
th='| Run | T (°C) | Status | T2F f_out (MHz) | T2F VDDA (µA) | T2F VDD (µA) | GATE / trip | Wall (s) | Log |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |'
tr=[]
for n in [lg('q_pex_c1414_tl_tt_-40C_*t2ftl*_r3_c1414m.log'),lg('q_pex_c1414_tl_tt_-40C_*c1414t2fv2.log'),lg('q_pex_c1414_tl_tt_-40C_*c1414t2fv3.log'),lg('q_pex_c1414_tl_tt_27C_*t2ftl*_r3_c1414m.log'),lg('q_pex_c1414_tl_tt_125C_*t2ftl*_r3_c1414m.log')]:
    x=info(n); t=x['T2F']; T=re.search(r'_tt_(-?\d+)C',n).group(1).replace('-','−')
    ok=x['status']=='completed'
    tr.append('| `%s` | %s | %s | %s | %s | %s | %s | %s | `%s` |'%(n.split('functional_')[-1][:-4],T,verdict('q',x) if ok else verdict('q',x),g('f_MHz',t) if ok else '—',f3(g('vdda_t2f_uA',t),1) if ok else '—',f3(g('vdd12_t2f_uA',t),2) if ok else '—','no trip, GATE %s V'%g('gate_min',x['NO_TRIP_EXPECTED']) if ok else '—',x['wall'] or 'running',n))
t2f=th+'\n'+'\n'.join(tr)
c=cnt
counts='%d completed (valid), %d invalid, %d timeout, %d numerical failure, %d running at time of writing.'%(c.get('completed',0),c.get('invalid',0),c.get('timeout',0),c.get('failed',0),c.get('running',0))
s=open(os.path.join(TOOLS,'template.md')).read()
rep={'matrix':open('matrix.md').read().strip(),'supply':open('sec_supply.md').read().strip(),'n2':open('sec_n2.md').read().strip(),'k1':open('sec_k1.md').read().strip(),'hot':open('sec_hot.md').read().strip(),'full':open('sec_full.md').read().strip(),'thr':open('sec_thr.md').read().strip(),'inval':open('inval.md').read().strip(),'pwr':'\n'.join(pw),'osc':osc,'t2f':t2f,'counts':counts,'when':datetime.datetime.now().strftime('%Y-%m-%d %H:%M %Z').strip()+' local'}
for k,v in rep.items(): s=s.replace('{{%s}}'%k,v)
assert '{{' not in s
open(os.path.join(SIM,'campaigns','RESULTS_20260925.md'),'w').write(s)
print(counts)
