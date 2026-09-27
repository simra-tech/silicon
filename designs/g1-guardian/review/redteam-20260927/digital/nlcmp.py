# Red-team 2026-09-27: compare two flat gate netlists cell by cell (instance -> cell, pin -> net), ignoring
# power pins and fill/decap/antenna/tap cells. Usage: python3 nlcmp.py <nl.v> <pnl.v>
import re,sys
def parse(fn):
    txt=open(fn).read()
    txt=re.sub(r'//.*','',txt)
    inst={}
    for m in re.finditer(r'^\s*(sg13g2_\w+)\s+(\S+)\s*\((.*?)\);',txt,re.S|re.M):
        cell,name,body=m.groups()
        pins={}
        for p in re.finditer(r'\.(\w+)\s*\(\s*(.*?)\s*\)\s*(?:,|$)',body,re.S):
            pn,net=p.groups()
            if pn in ('VDD','VSS','VPWR','VGND'): continue
            pins[pn]=net.strip()
        inst[name]=(cell,tuple(sorted(pins.items())))
    return inst
a=parse(sys.argv[1]); b=parse(sys.argv[2])
skip=lambda c: any(k in c for k in ('fill','decap','antenna','tap'))
fa={k:v for k,v in a.items() if not skip(v[0])}; fb={k:v for k,v in b.items() if not skip(v[0])}
print('nl insts',len(a),'logic',len(fa),'pnl insts',len(b),'logic',len(fb))
d=[k for k in set(fa)|set(fb) if fa.get(k)!=fb.get(k)]
print('differences',len(d)); 
for k in d[:10]: print(k,fa.get(k),fb.get(k))
