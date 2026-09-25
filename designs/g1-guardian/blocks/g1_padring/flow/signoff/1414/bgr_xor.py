import pya,json
ly=pya.Layout();ly.read(g)
bgr=ly.cell('__rz_port_text_031_g1_bgr_candidate');ov=ly.cell('bgr_supply_additive_context_candidate')
T=pya.ICplxTrans(pya.Trans(-331000,-732000))
out={}
for ref in refs.split(','):
    r=pya.Layout();r.read(ref);rt=r.top_cell();res={}
    for li in r.layer_indexes():
        info=r.get_info(li)
        if info.datatype in (22,23): continue  # fill datatypes excluded
        a=pya.Region(rt.begin_shapes_rec(li))
        j=ly.find_layer(info)
        b=pya.Region()
        if j is not None:
            b=pya.Region(bgr.begin_shapes_rec(j))+pya.Region(ov.begin_shapes_rec(j)).transformed(T)
        x=(a^b).merged()
        if not x.is_empty(): res[info.to_s()]=[x.count(),round(x.area()*1e-6,4)]
    out[ref.split('/evidence/')[-1]]=dict(ref_top=rt.name,xor_nonempty=res,layers=len(r.layer_indexes()))
print(json.dumps(out,indent=1))
