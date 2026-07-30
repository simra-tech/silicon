import bisect, math, sys
path=sys.argv[1]
t=[];raw=[]
for line in open(path):
    p=line.split()
    if len(p)<2: continue
    try: t.append(float(p[0])); raw.append(float(p[1]))
    except ValueError: continue
if not t: print("no data"); sys.exit()
C=200e-12
def rho(start_ns):
    o=[];k=int(start_ns*1e-9/C)
    while True:
        ts=k*C+100e-12
        if ts>t[-1]: break
        o.append(raw[bisect.bisect_left(t,ts)]); k+=1
    b=[1 if x>0.6 else 0 for x in o]; n=len(b)
    if n<20: return None
    p=sum(b)/n
    if not (0<p<1): return (n,p,None)
    xb=[x-p for x in b]; d=sum(x*x for x in xb)
    return (n,p,sum(xb[i]*xb[i+1] for i in range(n-1))/d)
print("last %.1f ns"%(t[-1]*1e9))
for s in (2,20,50,100,200):
    r=rho(s)
    if r is None: continue
    n,p,r1=r
    print("  window from %3d ns: N=%3d  P(1)=%.3f  rho1=%s"%(s,n,p,("%+.4f"%r1) if r1 is not None else "degenerate"))
