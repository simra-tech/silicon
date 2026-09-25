import pya,json,collections
l=pya.LayoutVsSchematic();l.read(db);x=l.xref()
out=[]
for cp in x.each_circuit_pair():
    a,b=cp.first(),cp.second()
    d={'layout':a.name if a else None,'reference':b.name if b else None,'status':str(cp.status())}
    for kind,it in [('device',x.each_device_pair),('net',x.each_net_pair),('pin',x.each_pin_pair),('subcircuit',x.each_subcircuit_pair)]:
        c=collections.Counter(str(p.status()) for p in it(cp)); d[kind]=dict(c)
    out.append(d)
print(json.dumps(dict(circuits=out),indent=1))
