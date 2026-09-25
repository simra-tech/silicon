"""Bounded read-only exact-parent fit and local feed inspection; no candidate insertion."""
import argparse,hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6]
PARENT=Path(os.environ['G1_RESULTS_ROOT'])/'osc-r095-fullchip-integration-20260924-r1/osc_r095_fullchip.gds'
PARENT_SHA='18b897feb06b7a02508ea8734d40845d69bcb515955368daba9dd1938a1949c9'
STANDALONE=Path(os.environ['G1_RESULTS_ROOT'])/'soft-inputpair4-folded-native-20260924-r1/standalone.gds'
STANDALONE_SHA='576427ba66ba273d223d41db64e279686f0810910f35fab658378fdccb21236a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    import pya
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);assert not out.exists()
    assert sha(PARENT)==PARENT_SHA and sha(STANDALONE)==STANDALONE_SHA
    sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_trip/layout'))
    import gen_trip_layout as g
    ly=pya.Layout();ly.read(str(PARENT));new=pya.Layout();new.read(str(STANDALONE))
    matches=[]
    for cell in ly.each_cell():
        for inst in cell.each_inst():
            if inst.trans.disp.x==141700 and inst.trans.disp.y==162000 and 'g1_cmp' in inst.cell.name:
                matches.append((cell,inst))
    assert len(matches)==1,[(c.name,i.cell.name) for c,i in matches]
    parent,soft=matches[0];actual=soft.cell;assert actual.child_cells()==0
    baseline=pya.Layout();baseline.dbu=.001;builder=g.CmpBuilder(baseline);builder.build()
    candidate=new.top_cell();deltas=[]
    for index in baseline.layer_indexes():
        info=baseline.get_info(index);ai=ly.find_layer(info);ni=new.find_layer(info)
        old=pya.Region(builder.cell.begin_shapes_rec(index)).merged()
        nr=pya.Region(candidate.begin_shapes_rec(ni)).merged() if ni is not None else pya.Region()
        ar=pya.Region(actual.begin_shapes_rec(ai)).merged() if ai is not None else pya.Region()
        removed=(old-nr).merged();added=(nr-old).merged()
        if not removed.is_empty() or not added.is_empty():
            deltas.append(dict(layer=info.to_s(),removed_um2=removed.area()*1e-6,added_um2=added.area()*1e-6,
                missing_deletion_um2=(removed-ar).area()*1e-6,preserved_native_extra_um2=(ar-old).area()*1e-6))
    # Preserve all current native text/pin sites in any future integration.
    pins=[]
    for index in ly.layer_indexes():
        info=ly.get_info(index)
        for shape in actual.shapes(index).each():
            if shape.is_text() and shape.text.string in ['inp','inn','q','qb','clk','vdd','vss']:
                pins.append(dict(name=shape.text.string,layer=info.to_s(),text=shape.text.to_s()))
    m1=ly.find_layer(pya.LayerInfo(8,0));m2=ly.find_layer(pya.LayerInfo(10,0))
    windows=[]
    for side in [-1,1]:
        box=pya.Box(int(side*14110-650),1800,int(side*14110+650),4200)
        for tag,index in [('M1',m1),('M2',m2)]:
            if index is not None:
                reg=pya.Region(actual.begin_shapes_rec(index))&pya.Region(box)
                windows.append(dict(side=side,layer=tag,old_VSS_port_neighborhood=[str(x) for x in reg.each()]))
    report=dict(status='read-only exact parent/standalone inspection; insertion not run',parent_sha256=PARENT_SHA,standalone_sha256=STANDALONE_SHA,
        parent_top=ly.top_cell().name,parent_bbox=str(ly.top_cell().bbox()),trip_cell=parent.name,soft_cell=actual.name,
        soft_transform=str(soft.trans),actual_soft_bbox=str(actual.bbox()),new_soft_bbox=str(candidate.bbox()),
        layer_deltas=deltas,native_pin_texts=pins,old_port_neighborhoods=windows,
        source_sha256=sha(Path(__file__)),generator_sha256=sha(Path(g.__file__)),all_inputs_unchanged=True)
    assert sha(PARENT)==PARENT_SHA and sha(STANDALONE)==STANDALONE_SHA
    with out.open('x') as stream:json.dump(report,stream,indent=2)
    print(json.dumps(report))
if __name__=='__main__':main()
