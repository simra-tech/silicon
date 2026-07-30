import sys,re
def load(p):
    t=[];v=[]
    started=False; buf=[]
    for line in open(p,errors='replace'):
        if not started:
            if line.startswith('Values:'): started=True
            continue
        s=line.strip()
        if not s: continue
        parts=s.split()
        if len(parts)==2 and parts[0].isdigit():
            if buf: v.append(buf[0])
            t.append(float(parts[1])); buf=[]
        else:
            buf.append(float(parts[0]))
    if buf: v.append(buf[0])
    n=min(len(t),len(v))
    return t[:n],v[:n]

def bits(t,v,start,period=200e-12,thr=0.6):
    out=[]; k=0
    # sample at start + k*period
    import bisect
    tt=start
    while tt<=t[-1]:
        i=bisect.bisect_left(t,tt)
        if i>=len(t): break
        out.append(1 if v[i]>thr else 0)
        tt+=period
    return out

def rho1(b):
    n=len(b)
    if n<3: return float('nan')
    m=sum(b)/n
    num=sum((b[i]-m)*(b[i+1]-m) for i in range(n-1))
    den=sum((x-m)**2 for x in b)
    return num/den if den else float('nan')

for p in sys.argv[1:]:
    t,v=load(p)
    name=p.split('/')[-1]
    print(f"{name}  N={len(t)}  tstop={t[-1]*1e9:.1f}ns  Vmin={min(v):.3f} Vmax={max(v):.3f}")
    for st,lab in ((2e-9,'2ns'),(30e-9,'30ns')):
        b=bits(t,v,st)
        if len(b)<5: print(f"   from {lab}: too few"); continue
        print(f"   from {lab:>4}: N={len(b):4d} P(1)={sum(b)/len(b):.3f} rho1={rho1(b):+.4f}")
