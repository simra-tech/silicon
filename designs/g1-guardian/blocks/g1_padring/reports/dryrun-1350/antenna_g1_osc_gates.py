import pya
ly=pya.Layout(); ly.read("designs/g1-guardian/blocks/g1_osc/layout/g1_osc.gds"); c=ly.cell("g1_osc")
# the marker polygons: (50.44,10)-(50.74,14) and (58.8,10)-(59.1,14): GatPoly gates 0.3 x 4 um
for x in (50.44, 58.8):
    box=pya.Box(int(x*1000)-500, 9000, int(x*1000)+800, 15000)
    for l,d,nm in ((5,0,"GatPoly"),(8,0,"Metal1"),(126,0,"TopMetal1"),(134,0,"TopMetal2"),(8,25,"M1 text"),(126,25,"TM1 text"),(134,25,"TM2 text"),(63,0,"TEXT")):
        li=ly.find_layer(l,d)
        if li is None: continue
        it=c.begin_shapes_rec_touching(li,box); out=[]
        while not it.at_end():
            sh=it.shape(); 
            out.append(sh.text.string if sh.is_text() else sh.bbox().transformed(it.trans()).to_s()); it.next()
        if out: print(f"x={x}: {nm}: {out[:4]}")
# texts on TopMetal1/2 anywhere in g1_osc
for l,d in ((126,25),(134,25),(126,0),(134,0)):
    li=ly.find_layer(l,d)
    if li is None: continue
    for sh in c.shapes(li).each():
        if sh.is_text(): print("label", l, d, sh.text.string, sh.text.x/1000, sh.text.y/1000)
