import pya
def rep(path,names):
    ly=pya.Layout();ly.read(path)
    for n in names:
        c=ly.cell(n)
        if c is None: print(path.split('/')[-1],n,'absent');continue
        out=[]
        for L,D in [(5,0),(128,0),(28,0),(7,0),(14,0)]:
            i=ly.find_layer(L,D); r=pya.Region(c.begin_shapes_rec(i)) if i is not None else pya.Region()
            out.append(f'{L}/{D}:{r.count()}:{r.area()*1e-6:.2f}um2')
        g=ly.find_layer(5,0);p=ly.find_layer(128,0)
        if g is not None and p is not None:
            ov=(pya.Region(c.begin_shapes_rec(g))&pya.Region(c.begin_shapes_rec(p))).area()*1e-6
            out.append(f'GatPoly&PolyRes:{ov:.2f}um2')
        print(path.split('/')[-1],n,' '.join(out))
rep('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds',['sg13g2_RCClampResistor','sg13g2_SecondaryProtection'])
rep(g,['g1_io_rc_polyres_r1','g1_io_rc_polyres_r1_alias1','g1_io_secondary_polyres_r1','g1_io_secondary_polyres_r1_alias1'])
