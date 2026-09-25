import pya,json,hashlib
ly=pya.Layout();ly.read(g)
out=[]
for pair in pairs.split(';'):
    cn,ref=pair.split("=");ref,refcell=(ref.split("@")+[None])[:2]
    c=ly.cell(cn); r=pya.Layout(); r.read(ref); tops=sorted(r.top_cells(),key=lambda t:-t.bbox().area()); rt=r.cell(refcell) if refcell else tops[0]; extra_tops=[t.name for t in tops[1:]]
    infos={(i.layer,i.datatype) for i in r.layer_infos()}|{(ly.get_info(i).layer,ly.get_info(i).datatype) for i in ly.layer_indexes() if not pya.Region(c.begin_shapes_rec(i)).is_empty()}
    res={};skipped=[]
    for L,D in sorted(infos):
        if D in (22,23): skipped.append(f'{L}/{D}');continue
        info=pya.LayerInfo(L,D);i=ly.find_layer(info);j=r.find_layer(info)
        a=pya.Region(c.begin_shapes_rec(i)) if i is not None else pya.Region()
        b=pya.Region(rt.begin_shapes_rec(j)) if j is not None else pya.Region()
        x=(a^b).merged()
        if not x.is_empty(): res[f'{L}/{D}']=[x.count(),round(x.area()*1e-6,4)]
    out.append(dict(cell=cn,ref=ref,ref_sha256=hashlib.sha256(open(ref,'rb').read()).hexdigest(),ref_top=rt.name,other_tops=extra_tops,
                    cell_bbox=str(c.bbox()),ref_bbox=str(rt.bbox()),xor_nonempty=res,excluded_fill_layers=skipped))
print(json.dumps(out,indent=1))
