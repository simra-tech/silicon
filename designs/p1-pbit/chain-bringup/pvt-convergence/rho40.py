import bisect, math, sys
path = sys.argv[1]
t=[];raw=[]
for line in open(path):
    p=line.split()
    if len(p)<2: continue
    try: t.append(float(p[0])); raw.append(float(p[1]))
    except ValueError: continue
if not t: print("no data"); sys.exit()
C=200e-12; o=[]; k=int(2e-9/C)
while True:
    ts=k*C+100e-12
    if ts>t[-1]: break
    o.append(raw[bisect.bisect_left(t,ts)]); k+=1
b=[1 if x>0.6 else 0 for x in o]; n=len(b); p=sum(b)/n
if 0<p<1:
    xb=[x-p for x in b]; d=sum(x*x for x in xb)
    r=[sum(xb[i]*xb[i+l] for i in range(n-l))/d for l in (1,2,3)]
    print("last %.1f ns  N=%d  P(1)=%.3f  rho= %+.4f %+.4f %+.4f"%(t[-1]*1e9,n,p,r[0],r[1],r[2]))
else:
    print("last %.1f ns  N=%d  degenerate P(1)=%.3f"%(t[-1]*1e9,n,p))
