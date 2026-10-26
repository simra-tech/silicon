import klayout.db as db
ly=db.Layout(); ly.read(g); top=ly.cell('r1_top'); dbu=ly.dbu
W=db.Region(db.Box(400000,400000,1200000,1200000))
for l,n in ((10,'M2'),(30,'M3'),(50,'M4'),(67,'M5')):
    r=db.Region()
    for d in (0,22):
        li=ly.find_layer(l,d)
        if li is not None: r+=db.Region(top.begin_shapes_rec(li))
    r=r.merged()
    print(n,'window coverage %.2f%%'%((r&W).area()/W.area()*100))
    for inst in top.each_inst():
        if inst.cell.name in ('r1_padring',) or inst.cell.name.startswith('sg13g2'): continue
        b=db.Region(inst.bbox())&W
        if b.is_empty(): continue
        print('   %-14s box-in-window %7.0f um2  cov %5.1f%%'%(inst.cell.name,b.area()*dbu*dbu,(r&b).area()/b.area()*100))
    allb=db.Region()
    for inst in top.each_inst():
        if inst.cell.name!='r1_padring': allb.insert(inst.bbox())
    fr=(W-allb.merged())
    print('   free area %.0f um2 cov %.1f%%'%(fr.area()*dbu*dbu,(r&fr).area()/fr.area()*100))
