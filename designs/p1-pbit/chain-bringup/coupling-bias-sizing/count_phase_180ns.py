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

for f,vdd,vtrip,lab in ((sys.argv[1],1.20,0.59383,'27C TT'),(sys.argv[2],1.32,0.65602,'-40C FF')):
    t,pb,clk=load(f)
    e=[x for x in edges(t,clk,vdd/2) if x>=50e-9]      # discard 50 ns of settling
    print(f"\n=== {lab}  points={len(t)} tstop={t[-1]*1e9:.0f}ns  edges after 50ns={len(e)}  slice at vtrip={vtrip} V")
    print(f"    {'phase':>6} {'N':>5} {'P(1)':>7} {'rho1':>9} {'se':>7} {'z':>7}")
    for ph in range(0,200,10):
        b=[1 if pb[bisect.bisect_left(t,ed+ph*1e-12)]>vtrip else 0
           for ed in e if bisect.bisect_left(t,ed+ph*1e-12)<len(t)]
        r=rho1(b)
        se=1/math.sqrt(len(b))
        if r is None: print(f"    {ph:>6} {len(b):>5} {sum(b)/len(b):>7.3f} {'degen':>9} {se:>7.4f}"); continue
        z=r/se
        print(f"    {ph:>6} {len(b):>5} {sum(b)/len(b):>7.3f} {r:>+9.4f} {se:>7.4f} {z:>+7.2f}")
