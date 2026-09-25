import os
SIM=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import csv,re,json,os,sys
S=SIM
L=S+'/logs'
def g(k,s):
    m=re.search(r'(?<![A-Za-z_.])'+re.escape(k)+r'=\s*([-+0-9.Ee]+)',s or ''); return m.group(1) if m else ''
def info(log):
    p=L+'/'+log; r={'log':log}
    if not os.path.exists(p): r['status']='nolog'; return r
    t=open(p,errors='replace').read()
    r['mism']='mismatched XSPICE' in t
    m=re.findall(r'# run status (.*)',t); r['status']=m[-1].strip() if m else 'running'
    m=re.findall(r'# ngspice exit (\S+), wall time (\S+) s',t); r['exit'],r['wall']=(m[-1] if m else ('',''))
    for k in ['QUIET','TRIP','NO_TRIP_EXPECTED','REARM','POWERUP','T2F','CLOCK','SUPPLY_uA']:
        ls=[l for l in t.splitlines() if l.startswith(k+' ')]
        r[k]=ls[-1] if ls else ''
    m=re.search(r'Timestep too small; time = (\S+),.*trouble with (.+)',t); r['tts']=(m.group(1),m.group(2)) if m else None
    pj=p[:-4]+'.progress.jsonl'
    r['simt']=''
    if os.path.exists(pj):
        ls=open(pj).read().splitlines()
        if ls:
            try: r['simt']=json.loads(ls[-1]).get('last_reported_sim_time_s','')
            except Exception: pass
            try: r['wall_now']=json.loads(ls[-1]).get('wall_s','')
            except Exception: pass
    return r
def f3(x,n=3):
    try: return ('%.'+str(n)+'f')%float(x)
    except: return '—'
def verdict(case,r):
    st=r['status']
    if r.get('mism') or 'cosim' in st: return 'invalid (RTL load)'
    if st=='timeout': return 'not run to completion (timeout at %s µs sim)'%f3(float(r['simt'])*1e6,1) if r.get('simt') else 'not run to completion (timeout)'
    if st=='running': return 'running at time of writing, not run to completion'
    if st!='completed':
        if r.get('tts'): return 'failed (timestep too small at %s µs, %s)'%(f3(float(r['tts'][0])*1e6,2),r['tts'][1])
        if r.get('exit')=='-15': return 'not run to completion (stopped, exit −15, at %s µs sim)'%(f3(float(r['simt'])*1e6,1) if r.get('simt') else '?')
        return 'failed (%s)'%st
    t=r['TRIP']; nt=r['NO_TRIP_EXPECTED']
    if case in('q','hard_pulse','a_s','osc','q_t2f','fm_no'):
        ok=g('gate_min',nt or t) and float(g('gate_min',nt or t))>2.9 and g('cause',nt or t) in ('0','')
        if case=='fm_no': return 'characterization: no trip' if ok else 'characterization: trip'
        return 'passed' if ok else 'failed'
    exp={'c':'2','c_mid':'2','e20':'2','c_fast':'2','b_s':'1','fm':'2'}
    if case=='f_mid':
        re_=r['REARM']; ok=g('t_gate_1V_us',t) and float(g('t_gate_1V_us',t))<10 and g('gate_end',re_)=='3.3' and g('iload_end_A',re_)=='1'
        return 'passed' if ok else 'failed'
    ok=g('cause',t)==exp[case] and g('t_gate_1V_us',t)!=''
    if case=='fm': return 'characterization: hard trip' if ok else 'characterization: no trip'
    if case!='b_s' and ok: ok=float(g('t_gate_1V_us',t))<10
    return 'passed' if ok else 'failed'
def row(case,r):
    t=r.get('TRIP','') or r.get('NO_TRIP_EXPECTED','')
    s=r.get('SUPPLY_uA','')
    notrip=case in('q','hard_pulse','a_s','osc','q_t2f','fm_no')
    done=r.get('status')=='completed' and not r.get('mism')
    td=f3(g('t_trip_d_us',t)) if done and not notrip else ('no trip' if done else '—')
    g1=f3(g('t_gate_1V_us',t)) if done and not notrip else ('GATE min %s V'%g('gate_min',t) if done else '—')
    g2=f3(g('t_gate_0.33V_us',t)) if done and not notrip else '—'
    cause=g('cause',t) if done else '—'
    if case=='f_mid' and done: cause='0 after re-arm (tripped); re-arm GATE 90 %% in %s µs, load %s A'%(f3(g('EN_high_to_GATE_90pct_us',r['REARM']),2),g('iload_end_A',r['REARM']))
    vdda=f3(g('VDDA',s),0) if done and g('VDDA',s) else '—'
    wall=r.get('wall') or (('%.0f (so far)'%float(r['wall_now'])) if r.get('wall_now') else '—')
    return [verdict(case,r),td,g1,g2,cause,vdda,wall,'`%s`'%r['log']]
if __name__=='__main__':
    print(json.dumps(info(sys.argv[1]),indent=1))
