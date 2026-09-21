import re, sys
f=sys.argv[1]
def val(s):
    m=re.match(r'([0-9.eE+-]+)([afpnum]?)',s); sc={'a':1e-18,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'':1}
    return float(m.group(1))*sc[m.group(2)]/1e-15
tot={}; pair={}
for line in open(f):
    if not line.startswith('C'): continue
    t=line.split(); a,b=t[1].replace('\\',''),t[2].replace('\\',''); v=val(t[3])
    tot[a]=tot.get(a,0)+v; tot[b]=tot.get(b,0)+v; pair[tuple(sorted((a,b)))]=pair.get(tuple(sorted((a,b))),0)+v
names=dict(x.split('=') for x in sys.argv[2].split(',')) if len(sys.argv)>2 else {}
for n in list(names)+['clk','inp','inn','q','qb']:
    print('%-6s %-22s total %.3f fF'%(n,names.get(n,''),tot.get(n,0)))
print()
crit=[n for n in names if names[n][0] in 'xy']
for (a,b),v in sorted(pair.items(), key=lambda kv:-kv[1]):
    if (a in crit or b in crit) and v>0.05:
        print('%-6s %-6s %-14s %-14s %.3f'%(a,b,names.get(a,a),names.get(b,b),v))
