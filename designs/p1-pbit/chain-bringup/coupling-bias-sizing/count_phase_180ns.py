import bisect, math, sys

def load(p):
    t=[];pb=[];clk=[]
    started=False; buf=[]
    for line in open(p, errors='replace'):
        if not started:
            if line.startswith('Values:'): started=True
            continue
        s=line.strip()
        if not s: continue
        parts=s.split()
        if len(parts)==2 and parts[0].isdigit():
            if buf: pb.append(buf[0]); clk.append(buf[1])
            t.append(float(parts[1])); buf=[]
        else: buf.append(float(parts[0]))
    if buf: pb.append(buf[0]); clk.append(buf[1])
    n=min(len(t),len(pb),len(clk))
    return t[:n],pb[:n],clk[:n]

def edges(t,clk,thr):
    return [t[i] for i in range(1,len(clk)) if clk[i-1]<=thr<clk[i]]

def rho1(b):
    n=len(b); m=sum(b)/n
    d=sum((x-m)**2 for x in b)
    return None if d==0 else sum((b[i]-m)*(b[i+1]-m) for i in range(n-1))/d

for f,vdd,vtrip,lab in ((sys.argv[1],1.20,0.593,'27C TT'),(sys.argv[2],1.32,0.656,'-40C FF')):
    t,pb,clk=load(f)
    e=[x for x in edges(t,clk,vdd/2) if x>=50e-9]      # discard 50 ns of settling
    print(f"\n=== {lab}  points={len(t)} tstop={t[-1]*1e9:.0f}ns  edges after 50ns={len(e)}  slice at vtrip={vtrip} V")
    se=1/math.sqrt(len(e))
    print(f"    se(rho) = 1/sqrt(N) = {se:.4f}")
    print(f"    {'phase':>6} {'P(1)':>7} {'rho1':>9} {'z':>7}")
    flagged=[]
    for ph in range(0,200,10):
        b=[1 if pb[bisect.bisect_left(t,ed+ph*1e-12)]>vtrip else 0
           for ed in e if bisect.bisect_left(t,ed+ph*1e-12)<len(t)]
        r=rho1(b)
        if r is None: print(f"    {ph:>6} {sum(b)/len(b):>7.3f} {'degen':>9}"); continue
        z=r/se
        mark=' <-- correlated' if abs(z)>=3 else ''
        if abs(z)>=3: flagged.append(ph)
        print(f"    {ph:>6} {sum(b)/len(b):>7.3f} {r:>+9.4f} {z:>+7.2f}{mark}")
    print(f"    phases with |z| >= 3: {flagged if flagged else 'none'}")
