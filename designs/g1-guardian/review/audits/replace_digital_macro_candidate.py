#!/usr/bin/env python3
"""Isolated full-parent digital replacement with exact other-cell preservation.

No routing, pad, analog or library edit is made. Fresh full-context checks are
mandatory after this preparation; standalone macro success is not adoption.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import klayout.db as k
from place_closed_analog import sha
from streamout_native_signal_routes import text_records


def physical(layout, cell, info):
    li=layout.find_layer(info)
    if li is None: return k.Region()
    it=cell.begin_shapes_rec(li)
    it.shape_flags=k.Shapes.SBoxes|k.Shapes.SPolygons|k.Shapes.SPaths
    return k.Region(it).merged()


def cell_signature(layout, cell):
    rows=[]
    for li in layout.layer_indexes():
        info=layout.get_info(li)
        rows.extend((info.layer,info.datatype,s.to_s()) for s in cell.shapes(li).each())
    children=sorted((i.cell.name,str(i.cplx_trans),str(i.a),str(i.b),i.na,i.nb)
                    for i in cell.each_inst())
    return hashlib.sha256(json.dumps([sorted(rows),children],separators=(',',':')).encode()).hexdigest()


def protected_cells(top, replaced):
    """All cells reachable without entering replaced macro, including shared ones."""
    todo=[top]; protected={}
    while todo:
        cell=todo.pop()
        if cell.cell_index()==replaced.cell_index() or cell.name in protected: continue
        protected[cell.name]=cell
        todo.extend(i.cell for i in cell.each_inst())
    return protected


def equal_macro(left, lc, right, rc):
    assert left.dbu==right.dbu and lc.bbox()==rc.bbox()
    infos={(i.layer,i.datatype) for i in left.layer_infos()+right.layer_infos()}
    rows=[]
    for layer,datatype in sorted(infos):
        info=k.LayerInfo(layer,datatype)
        delta=physical(left,lc,info)^physical(right,rc,info)
        assert delta.is_empty(),(layer,datatype)
        rows.append(dict(layer=layer,datatype=datatype,xor_dbu2=delta.area()))
    assert text_records(left,lc)==text_records(right,rc)
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','macro','old-macro','macro-lvs','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--parent-sha256',required=True)
    p.add_argument('--macro-sha256',required=True)
    a=p.parse_args(); assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert k.__version__=='0.30.9'
    assert sha(a.parent)==a.parent_sha256 and sha(a.macro)==a.macro_sha256
    proof=json.loads(a.macro_lvs.read_text())
    assert proof['status']=='passed strict native stock macro LVS'
    assert all(proof['strict_checks'].values()) and proof['inputs_rules_held']
    # LVS was on the exact derived geometry view; bind its generation proof.
    flat_gds=next(Path(name) for name in proof['inputs_sha256'] if name.endswith('.gds'))
    flat_proof=json.loads((flat_gds.parent/'summary.json').read_text())
    assert flat_proof['status'].startswith('passed geometry-exact') and flat_proof['saved_roundtrip']
    assert flat_proof['input_gds_sha256']==a.macro_sha256
    assert sha(flat_gds)==flat_proof['output_sha256']==proof['inputs_sha256'][str(flat_gds)]
    inputs={str(f):sha(f) for f in [a.parent,a.macro,a.old_macro,a.macro_lvs,flat_gds.parent/'summary.json',Path(__file__)]}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',inputs=inputs,not_run=['Full-parent terminal graph','Full-parent DRC/maximal/density/antenna',
        'Full-chip device LVS','Affected integrated timing and parasitics','Adoption'],not_applicable=['Statistical seed'])
    start=time.monotonic()
    try:
        layout=k.Layout();layout.read(str(a.parent));top=layout.top_cell()
        old=k.Layout();old.read(str(a.old_macro));oc=old.cell('g1_digital');assert oc is not None
        new=k.Layout();new.read(str(a.macro));nc=new.cell('g1_digital');assert nc is not None
        target=layout.cell('retained_g1_digital');assert target is not None
        instance,=[i for i in top.each_inst() if i.cell_index==target.cell_index()]
        assert str(instance.trans)=='r0 367000,364000'
        result['old_macro_native_equality']=equal_macro(old,oc,layout,target)
        assert oc.bbox()==nc.bbox()
        original_cells={name:cell_signature(layout,c) for name,c in protected_cells(top,target).items()}
        original_top=cell_signature(layout,top)
        # Only this root cell's contents change. Other retained native cells
        # and root-level overlays, moved pads, labels and arrays are immutable.
        target.clear();target.copy_tree(nc)
        assert cell_signature(layout,top)==original_top
        for name,digest in original_cells.items():
            assert cell_signature(layout,layout.cell(name))==digest,name
        result['new_macro_native_equality']=equal_macro(new,nc,layout,target)
        output=a.output/'digital_replaced_native.gds';layout.write(str(output))
        reread=k.Layout();reread.read(str(output))
        assert cell_signature(reread,reread.cell(top.name))==original_top
        for name,digest in original_cells.items():
            assert cell_signature(reread,reread.cell(name))==digest,name
        result['saved_macro_equality']=equal_macro(new,nc,reread,reread.cell(target.name))
        assert all(sha(Path(name))==digest for name,digest in inputs.items())
        result.update(status='passed isolated digital replacement and exact other-cell preservation',
            GDS_sha256=sha(output),original_parent_sha256=a.parent_sha256,macro_sha256=a.macro_sha256,
            unchanged_cell_signatures=original_cells,unchanged_top_signature=original_top,
            transform=str(instance.trans),top_cell=top.name,die_size_and_pad_bonding_map='unchanged',
            source_ports_and_PDN_landing_connectivity='not run: independently required full-parent audit')
    except Exception as exc:
        result.update(status='failed digital replacement proof',error=repr(exc));raise
    finally:
        result['wall_s']=time.monotonic()-start
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
