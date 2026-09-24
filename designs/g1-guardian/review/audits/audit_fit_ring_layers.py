#!/usr/bin/env python3
"""Read-only actual ring/macro layer control and proposed translation screen; no GDS."""
import argparse, hashlib, json, os
from pathlib import Path
import pya
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--gds',type=Path,required=True)
p.add_argument('--pack',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
assert pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1 and not a.output.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.gds)=='38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59'
pack=json.loads(a.pack.read_text())
ly=pya.Layout();ly.read(str(a.gds));top=ly.cell('g1_chip_top');dbu=ly.dbu
def bounds(b):return [b.left*dbu,b.bottom*dbu,b.right*dbu,b.top*dbu]
def region(cell,layer):return pya.Region(cell.begin_shapes_rec(ly.layer(layer,0))).merged()
layers=(8,10,30,50,67,126,134,19,29,49,66,125,133)
ring={};ring_rows=[]
for layer in (126,134):
    r=pya.Region()
    for shape in top.shapes(ly.layer(layer,0)).each():
        if not (shape.is_box() or shape.is_polygon() or shape.is_path()):continue
        poly=shape.polygon;b=poly.bbox();x1,y1,x2,y2=bounds(b);w=x2-x1;h=y2-y1
        # Select actual unmodified long15um core-ring conductors, not arbitrary43um bands.
        vertical=abs(w-15)<1e-7 and h>500 and (321<=x1<x2<=364 or 986<=x1<x2<=1029)
        horizontal=abs(h-15)<1e-7 and w>500 and (321<=y1<y2<=364 or 986<=y1<y2<=1029)
        if vertical or horizontal:
            r.insert(poly)
            ring_rows.append(dict(layer=layer,bbox_um=[x1,y1,x2,y2],area_um2=poly.area()*dbu*dbu))
    ring[layer]=r.merged()
assert all(not r.is_empty() for r in ring.values())
names={'g1_dut_macro':'g1_dut','g1_dose_macro':'g1_dose','g1_bgr':'g1_bgr_candidate','g1_sense':'g1_sense_candidate'}
targets={r['name']:r['bbox_um'] for r in pack['macros']};rows=[];ls=0
for inst in top.each_inst():
    name=inst.cell.name
    if not name.startswith('g1_'):continue
    target_name=names.get(name,name)
    if name=='g1_ls_up':target_name='g1_ls_'+str(ls);ls+=1
    assert target_name in targets
    old=inst.bbox();new=targets[target_name];dx=round(new[0]/dbu)-old.left;dy=round(new[1]/dbu)-old.bottom
    data=dict(cell=name,original_bbox_um=bounds(old),proposed_bbox_um=new,translate_um=[dx*dbu,dy*dbu],layers={})
    for layer in layers:
        local=region(inst.cell,layer);original=local.transformed(inst.trans);moved=original.transformed(pya.Trans(dx,dy))
        row=dict(native_drawing_area_um2=local.area()*dbu*dbu,native_drawing_bbox_um=None if local.is_empty() else bounds(local.bbox()))
        if layer in ring:
            ov=original&ring[layer];mv=moved&ring[layer]
            row.update(baseline_actual_ring_overlap_um2=ov.area()*dbu*dbu,
                translated_unchanged_macro_vs_original_west_south_and_old_east_north_ring_overlap_um2=mv.area()*dbu*dbu,
                translated_overlap_bbox_um=None if mv.is_empty() else bounds(mv.bbox()))
        data['layers'][str(layer)]=row
    if name in ('g1_bgr','g1_sense'):
        data['translation_scope']='Original macro only: not resized candidate. Candidate exact native/reserved uppermetal assessment remains separate.'
    else:
        data['translation_scope']='Unchanged native macro translated to proposed rectangle, no GDS save. Original west/south ring stays physical; old east/north ring comparison is diagnostic, not expanded-ring geometry.'
    rows.append(data)
assert len(rows)==12
result=dict(status='passed read-only inventory; candidate no-short/spacing/access acceptance not run',
    script_sha256=sha(Path(__file__)),source_GDS_sha256=sha(a.gds),pack_sha256=sha(a.pack),KLayout=pya.__version__,
    actual_core_ring_conductors=ring_rows,macros=rows,no_saved_GDS=True,
    all_layer43um_exclusion_area=dict(expanded_inner_placement_side_um=pack['die_side_um']-728,
        available_um2=(pack['die_side_um']-728)**2,
        macro_plus_decap_LEF_um2=sum((m['bbox_um'][2]-m['bbox_um'][0])*(m['bbox_um'][3]-m['bbox_um'][1]) for m in pack['macros'])+59118.5952,
        status='failed necessary area condition, before corridors'),
    limitations=['Any nonzero same-layer intersection is not a net-aware short classification until net IDs are compared.',
        'No proposed expanded ring generated; west/south exact original conductors provide unchanged geometric control.',
        'No lower-layer-under-ring waiver: actual uppermetal, via, spacing, no-short, capacitance and device-access checks remain required.',
        'No source/cards/decks/canonical geometry modified.'])
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'ring_conductors':len(ring_rows),'all_layer_exclusion':result['all_layer43um_exclusion_area'],
    'macro_overlaps':[(r['cell'],{l:(v.get('baseline_actual_ring_overlap_um2'),v.get('translated_unchanged_macro_vs_original_west_south_and_old_east_north_ring_overlap_um2')) for l,v in r['layers'].items() if l in ('126','134')}) for r in rows]},indent=2))
