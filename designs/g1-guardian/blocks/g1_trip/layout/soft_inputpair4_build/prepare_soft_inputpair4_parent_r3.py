"""Isolated current-parent delta: soft folded cell and its necessary q-feed route.

All original cell names/instances/root shapes/fill remain; only soft-cell device
geometry and local q-feed metal change. No macro pin or source size changes.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path
from inspect_soft_inputpair4_parent_r1 import ROOT,PARENT,PARENT_SHA,STANDALONE,STANDALONE_SHA,sha
from soft_inputpair4_parent_reference_r1 import SOURCE,SOURCE_SHA

def reference(text):
    assert hashlib.sha256(text.encode()).hexdigest()==SOURCE_SHA
    block,=re.findall(r'(?ms)^\.subckt g1_cmp inp inn clk q qb vdd vss\n.*?^\.ends\n',text)
    changed=block;edits=[]
    for device,nodes in [('MM1','xp inp tail'),('MM2','xq inn tail')]:
        old=device+' '+nodes+' vss sg13_lv_nmos w=12u l=0.34u m=1'
        new=old.replace('w=12u l=0.34u','w=24u l=0.68u')
        assert changed.count(old+'\n')==1;changed=changed.replace(old,new);edits.append((old,new))
    result=text.replace(block,changed);inverse=result
    for old,new in edits:inverse=inverse.replace(new,old)
    assert inverse==text
    return result

def main():
    import pya
    sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_trip/layout'))
    import gen_trip_layout as g
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);assert not out.exists()
    assert sha(PARENT)==PARENT_SHA and sha(STANDALONE)==STANDALONE_SHA and sha(SOURCE)==SOURCE_SHA
    ly=pya.Layout();ly.read(str(PARENT));top=ly.top_cell();topname=top.name;topbox=top.bbox()
    def direct(cell):
        return {ly.get_info(i).to_s():sorted(str(s) for s in cell.shapes(i).each()) for i in ly.layer_indexes() if not cell.shapes(i).is_empty()}
    def instances(cell):return sorted((i.cell.name,str(i.cell_inst),i.prop_id) for i in cell.each_inst())
    before={c.name:dict(shapes=direct(c),instances=instances(c)) for c in ly.each_cell()}
    matches=[(c,i) for c in ly.each_cell() for i in c.each_inst() if i.trans.disp.x==141700 and i.trans.disp.y==162000 and 'g1_cmp' in i.cell.name]
    assert len(matches)==1;trip,inst=matches[0];soft=inst.cell;assert soft.child_cells()==0
    original=pya.Layout();original.dbu=.001;builder=g.CmpBuilder(original);builder.build()
    new=pya.Layout();new.read(str(STANDALONE));candidate=new.top_cell();deltas=[]
    infos={(i.layer,i.datatype):pya.LayerInfo(i.layer,i.datatype) for i in original.layer_infos()+new.layer_infos() if i.layer>=0}
    for info in infos.values():
        oi=original.find_layer(info);ni=new.find_layer(info);ai=ly.layer(info)
        old=pya.Region(builder.cell.begin_shapes_rec(oi)).merged() if oi is not None else pya.Region()
        replacement=pya.Region(candidate.begin_shapes_rec(ni)).merged() if ni is not None else pya.Region()
        remove=(old-replacement).merged();add=(replacement-old).merged()
        if remove.is_empty() and add.is_empty():continue
        actual=pya.Region(soft.begin_shapes_rec(ai)).merged();assert (remove-actual).is_empty(),('missing target geometry',info.to_s())
        texts=[s.text for s in soft.shapes(ai).each() if s.is_text()]
        soft.shapes(ai).clear();soft.shapes(ai).insert((actual-remove+add).merged())
        for text in texts:soft.shapes(ai).insert(text)
        deltas.append(dict(layer=info.to_s(),removed_um2=remove.area()*1e-6,added_um2=add.area()*1e-6))
    # Native scope already removed unused qb label; preserve it rather than
    # copying all standalone text. Only VSS label must follow its moved ring.
    ti=ly.layer(pya.LayerInfo(8,25));labels=[s.text for s in soft.shapes(ti).each() if s.is_text()]
    assert sum(t.string=='vss' for t in labels)==1
    assert all(s.is_text() for s in soft.shapes(ti).each())
    soft.shapes(ti).clear()
    for t in labels:
        if t.string=='vss':t.trans=pya.Trans(pya.Point(-16910,3000))
        soft.shapes(ti).insert(t)
    # Soft ring top y is held, so existing central VSS feed remains connected.
    # Original input M3 landing pads remain on the longer same-net M2 stubs.
    # q's old vertical would cross the enlarged cell's ynb routing: move only
    # that exact parent feed to the new outer q terminal.
    routes=[]
    for x in [127.44,124.64]:
        rly=pya.Layout();rly.dbu=.001;cell=rly.create_cell('route');d=g.Draw(rly,cell)
        d.vwire('M2',x,171.6,194.5);d.vpad('Via2',x,194.5,lo='v',hi='h');d.hwire('M3',x,228.5,194.5)
        routes.append((rly,cell))
    route_deltas=[]
    for oi in routes[0][0].layer_indexes():
        info=routes[0][0].get_info(oi);ni=routes[1][0].find_layer(info);ai=ly.layer(info)
        old=pya.Region(routes[0][1].begin_shapes_rec(oi)).merged()
        newroute=pya.Region(routes[1][1].begin_shapes_rec(ni)).merged() if ni is not None else pya.Region()
        remove=old-newroute;add=newroute-old
        if remove.is_empty() and add.is_empty():continue
        actual=pya.Region(trip.shapes(ai)).merged();assert (remove-actual).is_empty(),('old q-feed not exact',info.to_s())
        texts=[s.text for s in trip.shapes(ai).each() if s.is_text()]
        trip.shapes(ai).clear();trip.shapes(ai).insert((actual-remove+add).merged())
        for t in texts:trip.shapes(ai).insert(t)
        route_deltas.append(dict(layer=info.to_s(),removed_um2=remove.area()*1e-6,added_um2=add.area()*1e-6))
    box=inst.bbox();assert 0<=box.left<=box.right<=229000 and 0<=box.bottom<=box.top<=207000
    for c in ly.each_cell():
        assert instances(c)==before[c.name]['instances']
        if c.name not in [soft.name,trip.name]:assert direct(c)==before[c.name]['shapes'],c.name
    assert ly.top_cell().name==topname and top.bbox()==topbox
    # Trip pin/text/boundary layers cannot change: direct route layers only.
    for key,values in before[trip.name]['shapes'].items():
        if key not in ['10/0','29/0','30/0']:assert direct(trip).get(key)==values,('non-route parent layer changed',key)
    out.mkdir();ly.write(str(out/'candidate.gds'));(out/'candidate.cdl').write_text(reference(SOURCE.read_text()))
    report=dict(status='prepared isolated full-parent candidate; DRC/LVS not run',parent_sha256=PARENT_SHA,canonical_reference_sha256=SOURCE_SHA,
        candidate_sha256=sha(out/'candidate.gds'),candidate_reference_sha256=sha(out/'candidate.cdl'),source_sha256=sha(Path(__file__)),
        soft_cell=soft.name,trip_cell=trip.name,top=topname,top_bbox=str(topbox),soft_geometry_delta=deltas,q_route_delta=route_deltas,
        all_original_instances_exact=True,all_non_target_cells_exact=True,macro_pin_text_boundary_layers_exact=True,
        root_shapes_and_fill_held=True,no_adoption=True)
    (out/'preparation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
