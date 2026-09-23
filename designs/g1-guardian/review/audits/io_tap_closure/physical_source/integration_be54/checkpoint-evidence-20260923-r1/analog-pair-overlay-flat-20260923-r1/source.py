#!/usr/bin/env python3
"""Exact 33-object hierarchy-only extraction view; no physical or source change."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import pya

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'flow/run.sh').is_file())
AUDITS=ROOT/'designs/g1-guardian/review/audits'
sys.path.insert(0,str(AUDITS))
from prepare_digital_reroute_native_hierarchy import signature,properties


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def shapes(layout,cell):
    return Counter((layout.get_info(i).layer,layout.get_info(i).datatype,s.to_s(),properties(s))
        for i in layout.layer_indexes() for s in cell.shapes(i).each())


def children(cell):
    return Counter((i.cell.name,str(i.cplx_trans),str(i.a),str(i.b),i.na,i.nb,properties(i)) for i in cell.each_inst())


def physical(cell,index):
    it=cell.begin_shapes_rec(index);it.shape_flags=pya.Shapes.SBoxes|pya.Shapes.SPolygons|pya.Shapes.SPaths
    return pya.Region(it).merged()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    source=bulk/'analog-pair-poly-fill-20260923-r2/poly_fill_pruned.gds';meta=source.parent/'analysis.json'
    overlay=bulk/'bgr-dvbe-cuts-candidate-20260923-r2/redundant_cuts_overlay.gds'
    cdl=bulk/'analog-pair-reference-20260923-r1/physical_taps_reader.cdl'
    helper=AUDITS/'prepare_digital_reroute_native_hierarchy.py'
    expected={source:'9f7bb2edd378cb008f2431887fbd982e1e0342ddb7bf51b841dd76bd24cfce4a',
        meta:'f05e1d524e369f8df0d897268bb657759dd4b84f52a209fbcdc637952637b5df',
        overlay:'c7135cbe9741e192c32f9eb469396781469e02fba1c42fb467d41c4c739a6ed8',
        cdl:'35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51',
        helper:'0d881688d344c59705fb8a1c768d2ec37ed83f0da30227c863314f8978d0de3c'}
    assert all(sha(p)==h for p,h in expected.items())
    a.output.mkdir(parents=True);result=dict(status='running exact overlay hierarchy projection',inputs={str(p):h for p,h in expected.items()})
    def save():(a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    save();ly=pya.Layout();ly.read(str(source));top=ly.cell('placed_core_NOT_CONNECTED_FULLCHIP')
    assert ly.dbu==.001 and [c.name for c in ly.top_cells()]==[top.name]
    name='bgr_redundant_cuts_context_candidate';inst,=[i for i in top.each_inst() if i.cell.name==name]
    child=inst.cell;trans=inst.cplx_trans
    assert str(trans)=='r0 *1 331000,732000' and inst.na<=1 and inst.nb<=1
    assert not inst.properties() and not child.properties() and not list(child.each_inst())
    original=pya.Layout();original.read(str(overlay));oc=original.top_cell()
    assert shapes(ly,child)==shapes(original,oc)
    before={c.name:signature(ly,c) for c in ly.each_cell()};rootshapes=shapes(ly,top);rootchildren=children(top)
    excluded=next(r for r in rootchildren if r[0]==name);assert rootchildren[excluded]==1
    expectedchildren=rootchildren.copy();del expectedchildren[excluded]
    rootprops=properties(top);bbox=str(top.bbox());ledger=[];added=[]
    for li in ly.layer_indexes():
        info=ly.get_info(li)
        for shape in child.shapes(li).each():
            assert not shape.properties() and (shape.is_box() or shape.is_polygon())
            obj=shape.box.transformed(trans) if shape.is_box() else shape.polygon.transformed(trans)
            inserted=top.shapes(li).insert(obj);added.append(inserted)
            ledger.append(dict(layer=[info.layer,info.datatype],local=shape.to_s(),placed=inserted.to_s(),properties=properties(inserted)))
    assert len(ledger)==33
    cuts={(29,0),(49,0),(66,0)}
    assert sum(tuple(r['layer']) in cuts for r in ledger)==26
    assert {tuple(r['layer']) for r in ledger}-cuts=={(10,0),(30,0),(50,0),(67,0)}
    inst.delete()
    expectedshapes=rootshapes+Counter((r['layer'][0],r['layer'][1],r['placed'],r['properties']) for r in ledger)
    assert shapes(ly,top)==expectedshapes and children(top)==expectedchildren and properties(top)==rootprops
    assert all(signature(ly,ly.cell(n))==h for n,h in before.items() if n!=top.name)
    # Remove only the now-unreachable, device-free overlay definition when
    # serializing; all remaining definitions and instances are exact.
    clean=pya.Layout();clean.dbu=ly.dbu;ct=clean.create_cell(top.name);ct.copy_tree(top)
    assert clean.cell(name) is None
    dest=a.output/'overlay_flattened.gds';clean.write(str(dest))
    saved=pya.Layout();saved.read(str(dest));st=saved.cell(top.name)
    assert [c.name for c in saved.top_cells()]==[top.name] and saved.dbu==.001
    assert shapes(saved,st)==expectedshapes and children(st)==expectedchildren and properties(st)==rootprops
    assert str(st.bbox())==bbox
    after={c.name:signature(saved,c) for c in saved.each_cell()}
    assert set(after)==set(before)-{name}
    assert all(after[n]==h for n,h in before.items() if n not in (name,top.name))
    # Independent full-parent physical XOR on every affected layer. All other
    # layers and all texts are exact by the complete local-record/hierarchy proof.
    old=pya.Layout();old.read(str(source));ot=old.cell(top.name);xor=[]
    for pair in sorted({tuple(r['layer']) for r in ledger}):
        delta=physical(st,saved.layer(*pair))^physical(ot,old.layer(*pair))
        assert delta.is_empty(),pair;xor.append(dict(layer=list(pair),xor_dbu2=0))
    # Reverse the saved projection, using exact record multiplicities, and
    # reconstruct the original root and all original cell definitions.
    for r in ledger:
        li=saved.layer(*r['layer']);matches=[s for s in st.shapes(li).each() if s.to_s()==r['placed'] and properties(s)==r['properties']]
        assert matches;matches[0].delete()
    restored=saved.create_cell(name);restored.copy_tree(old.cell(name))
    st.insert(pya.CellInstArray(restored.cell_index(),pya.Trans(331000,732000)))
    assert {c.name:signature(saved,c) for c in saved.each_cell()}==before
    assert all(sha(p)==h for p,h in expected.items())
    result.update(status='passed exact 33-object hierarchy-only projection; stock LVS not run',
        GDS_sha256=sha(dest),top_cell=top.name,object_count=33,via_cut_count=26,metal_landing_count=7,
        ledger=ledger,full_affected_layer_XOR=xor,all_other_cell_definitions_exact=True,
        all_root_text_and_nonoverlay_objects_exact=True,source_bytes_exact=True,
        inverse_saved_projection_all_definitions_exact=True,original_GDS_sha256=sha(source),
        native_LVS='not run',physical_geometry_change='not applicable',adoption='not run')
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes());save()


if __name__=='__main__':main()
