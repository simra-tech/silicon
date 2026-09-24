#!/usr/bin/env python3
"""Remove only declared old floating-fill repetitions around replaced macro.

This is an isolated preparation, not DRC/density/connectivity acceptance.
Native functional shapes, pin labels, pads and all cell definitions are held.
"""
import argparse
import collections
import json
import os
from pathlib import Path
import time
import pya
from place_closed_analog import region,sha
from streamout_native_signal_routes import text_records

METALS=(10,30,50,67)


def fill_payload(layout,cell):
    assert '_FILL_CELL' in cell.name and not list(cell.each_inst())
    payload=[(info,s) for info in layout.layer_infos() for s in cell.shapes(layout.layer(info)).each()]
    assert len(payload)==1
    info,shape=payload[0]
    assert info.datatype==22 and info.layer in METALS and not shape.is_text()
    return info,shape.polygon


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    meta=json.loads((a.candidate/'analysis.json').read_text())
    assert meta['status']=='passed isolated digital replacement and exact other-cell preservation'
    source=a.candidate/'digital_replaced_native.gds';assert sha(source)==meta['GDS_sha256']
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',source_GDS_sha256=sha(source),source_metadata_sha256=sha(a.candidate/'analysis.json'),
        not_run=['Fresh main/maximal DRC','Density and replacement fill','Antenna','Terminal connectivity','Adoption'])
    start=time.monotonic()
    try:
        ly=pya.Layout();ly.read(str(source));top=ly.cell(meta['top_cell']);assert ly.dbu==.001
        macro=ly.cell('retained_g1_digital');inst,=[i for i in top.each_inst() if i.cell_index==macro.cell_index()]
        window=pya.Region(inst.bbox().enlarged(600))
        texts=text_records(ly,top)
        # A cell definition never changes. Only selected root array repetitions
        # are removed; other repetitions are expanded exactly, not clipped.
        def local(cell):
            return sorted((info.layer,info.datatype,s.to_s()) for info in ly.layer_infos() for s in cell.shapes(ly.layer(info)).each())
        definitions={cell.name:local(cell) for cell in ly.each_cell()}
        nonfill=collections.Counter((i.cell.name,str(i.cell_inst),i.prop_id) for i in top.each_inst() if '_FILL_CELL' not in i.cell.name)
        before={layer:region(ly,top,pya.LayerInfo(layer,22)) for layer in METALS}
        removed={layer:pya.Region() for layer in METALS};ledger=[]
        for instance in list(top.each_inst()):
            if '_FILL_CELL' not in instance.cell.name or not instance.bbox().overlaps(window.bbox()):continue
            infos=[info for info in ly.layer_infos() if not instance.cell.shapes(ly.layer(info)).is_empty()]
            if not any(info.layer in METALS and info.datatype==22 for info in infos):continue
            assert instance.prop_id==0
            info,polygon=fill_payload(ly,instance.cell)
            selected=[];keep=[]
            for tr in instance.cell_inst.each_cplx_trans():
                poly=polygon.transformed(tr)
                if (pya.Region(poly)&window).is_empty():keep.append(tr)
                else:selected.append((tr,poly))
            if not selected:continue
            row=dict(cell=instance.cell.name,array=str(instance.cell_inst),layer=[info.layer,22],
                removed=[dict(transform=str(tr),hull_dbu=[[v.x,v.y] for v in poly.each_point_hull()]) for tr,poly in selected],
                retained_transforms=[str(tr) for tr in keep])
            index=instance.cell_index;instance.delete()
            for tr in keep:top.insert(pya.CellInstArray(index,tr))
            for tr,poly in selected:removed[info.layer].insert(poly)
            ledger.append(row)
        assert ledger and definitions=={cell.name:local(cell) for cell in ly.each_cell()}
        assert nonfill==collections.Counter((i.cell.name,str(i.cell_inst),i.prop_id) for i in top.each_inst() if '_FILL_CELL' not in i.cell.name)
        assert texts==text_records(ly,top)
        areas=[]
        for layer in METALS:
            actual=region(ly,top,pya.LayerInfo(layer,22))
            assert (actual^(before[layer]-removed[layer])).is_empty(),layer
            areas.append(dict(layer=layer,removed_area_um2=(before[layer]-actual).area()*ly.dbu**2,
                              removed_repetitions=sum(len(r['removed']) for r in ledger if r['layer'][0]==layer)))
        output=a.output/'digital_fill_pruned.gds';ly.write(str(output))
        reread=pya.Layout();reread.read(str(output));rt=reread.cell(meta['top_cell'])
        assert rt is not None and text_records(reread,rt)==texts and rt.bbox()==top.bbox()
        for layer in METALS:
            assert (region(reread,rt,pya.LayerInfo(layer,22))^region(ly,top,pya.LayerInfo(layer,22))).is_empty()
        assert sha(source)==result['source_GDS_sha256']
        result.update(status='passed exact macro-near floating-fill pruning',GDS_sha256=sha(output),top_cell=meta['top_cell'],
            original_parent_sha256=meta['original_parent_sha256'],macro_sha256=meta['macro_sha256'],
            native_cell_definitions_and_nonfill_instances='passed exact preservation',all_texts='passed exact preservation',
            halo_um=.6,ledger=ledger,removed_by_layer=areas)
    except Exception as exc:
        result.update(status='failed fill-pruning proof',error=repr(exc));raise
    finally:
        result['wall_s']=time.monotonic()-start
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
