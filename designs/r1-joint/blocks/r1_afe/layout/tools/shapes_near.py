import pya
ly=pya.Layout(); ly.read(gds)
c=ly.cell('r1_afe_ch')
pts=[(154.23,141.9),(137.43,83.7),(57.6,2.68),(60.8,2.68)]
for (x,y) in pts:
    print('== near',x,y)
    box=pya.DBox(x-0.6,y-0.6,x+0.6,y+0.6)
    for li in ly.layer_indexes():
        info=ly.get_info(li)
        if (info.layer,info.datatype) not in ((8,0),(10,0),(19,0),(29,0),(6,0)): continue
        it=c.begin_shapes_rec_overlapping(li, box)
        while not it.at_end():
            sh=it.shape()
            print(' ',info.layer,info.datatype,sh.dbbox().transformed(it.dtrans()))
            it.next()
