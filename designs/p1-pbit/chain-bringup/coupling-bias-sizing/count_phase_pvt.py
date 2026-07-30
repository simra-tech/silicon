import sys,bisect
def load(p):
    t=[];cols=[]
    started=False; buf=[]
    for line in open(p,errors='replace'):
        if not started:
            if line.startswith('Values:'): started=True
            continue
        s=line.strip()
        if not s: continue
        parts=s.split()
        if len(parts)==2 and parts[0].isdigit():
            if buf: cols.append(buf)
            t.append(float(parts[1])); buf=[]
        else: buf.append(float(parts[0]))
    if buf: cols.append(buf)
    n=min(len(t),len(cols))
    return t[:n],[c[0] for c in cols[:n]],[c[1] for c in cols[:n]]   # time, pbit, clk

def edges(t,clk,thr=0.6):
    e=[]
    for i in range(1,len(clk)):
        if clk[i-1]<=thr<clk[i]: e.append(t[i])
    return e

def rho1(b):
    n=len(b); m=sum(b)/n
    d=sum((x-m)**2 for x in b)
    if d==0: return None
    return sum((b[i]-m)*(b[i+1]-m) for i in range(n-1))/d

for p,lab in ((sys.argv[1],'27C'),(sys.argv[2],'-40C')):
    t,pb,clk=load(p)
    e=edges(t,clk)
    print(f"\n=== {lab}: {p.split('/')[-1]}  points={len(t)} tstop={t[-1]*1e9:.1f}ns  clock edges={len(e)}")
    if len(e)>2: print(f"    clock period from edges = {(e[-1]-e[0])/(len(e)-1)*1e12:.1f} ps")
    e=[x for x in e if x>=2e-9]
    for ph in range(0,200,10):
        b=[]
        for ed in e:
            ts=ed+ph*1e-12
            i=bisect.bisect_left(t,ts)
            if i<len(t): b.append(1 if pb[i]>0.6 else 0)
        r=rho1(b)
        print(f"    phase {ph:3d} ps: N={len(b):4d} P(1)={sum(b)/len(b):.3f} rho1={('%+.4f'%r) if r is not None else 'degenerate'}")
