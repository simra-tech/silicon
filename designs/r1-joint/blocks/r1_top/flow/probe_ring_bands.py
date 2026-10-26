import klayout.db as db, sys, collections
ly=db.Layout(); ly.read(sys.argv[1]); top=ly.cell('r1_top'); ring=ly.cell('r1_padring')
c=collections.defaultdict(lambda:[1e9,-1e9,1e9,-1e9,0])
for i in ring.each_inst():
    b=i.dbbox(); k=i.cell.name
    if 'FILL' in k: continue
    e=c[k]; e[0]=min(e[0],b.left); e[1]=max(e[1],b.right); e[2]=min(e[2],b.bottom); e[3]=max(e[3],b.top); e[4]+=1
for k,v in sorted(c.items()): print(k,v)
for l in [(39,0),(41,0),(9,0),(134,0),(126,0),(67,0)]:
    li=ly.find_layer(*l); r=db.Region(top.begin_shapes_rec(li)); print(l,r.count(),r.bbox())
es=db.Region(top.begin_shapes_rec(ly.find_layer(39,0))); h=es.holes(); print('holes',h.count(),h.bbox())
for l in [(8,23),(1,23),(134,23),(160,0),(5,23)]:
    li=ly.find_layer(*l); 
    for p in db.Region(top.begin_shapes_rec(li)).each(): print(l,p.bbox())
