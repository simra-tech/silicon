#!/usr/bin/env python3
"""Read-only BGR PCell footprint and local neighborhood estimate; not placement signoff."""
import argparse,collections,hashlib,json,re
from pathlib import Path
import pya
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists();a.output.mkdir();root=Path(__file__).resolve().parents[4];gds=root/'designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds';ly=pya.Layout();ly.read(str(gds));bgr=ly.cell('g1_bgr');dbu=ly.dbu
rows=[]
for i in bgr.each_inst():
 c=i.cell;name=c.name; b=c.bbox();kind=next((s for s in ['pmosHV','nmosHV','rppd','rhigh','npn13G2'] if name.startswith(s)),None)
 if kind is None:continue
 active=pya.Region(c.begin_shapes_rec(ly.layer(1,0)));poly=pya.Region(c.begin_shapes_rec(ly.layer(5,0)));gates=active&poly
 rows.append({'kind':kind,'cell':name,'bbox_um':[b.left*dbu,b.bottom*dbu,b.right*dbu,b.top*dbu],'width_um':b.width()*dbu,'height_um':b.height()*dbu,'bbox_area_um2':b.area()*dbu**2,'placement_um':[i.dcplx_trans.disp.x,i.dcplx_trans.disp.y], 'gate_boxes_um':[[q.bbox().width()*dbu,q.bbox().height()*dbu] for q in gates.each()] if 'mos' in kind else [],'contacts':pya.Region(c.begin_shapes_rec(ly.layer(6,0))).count()})
placements=[]
for i in ly.cell('g1_chip_top').each_inst():
 b=i.bbox();placements.append({'cell':i.cell.name,'bbox_um':[b.left*dbu,b.bottom*dbu,b.right*dbu,b.top*dbu]})
data={'gds_sha256':hashlib.sha256(gds.read_bytes()).hexdigest(),'klayout':pya.__version__,'pcells':rows,'all_top_placements':placements,'scope':'Actual installed PCell bboxes include native implant/well/contacts; extra layout-level guard rings, dummies and routing are separate. Bounding rectangles can overlap in legal placements, so summed area is footprint accounting rather than a rigorous packing bound.'}
(a.output/'inventory.json').write_text(json.dumps(data,indent=2)+'\n')
for k,v in sorted(collections.Counter((r['kind'],r['width_um'],r['height_um'],str(r['gate_boxes_um'])) for r in rows).items()):print(k,v)
print('TOP',[(r['cell'],r['bbox_um']) for r in placements if r['cell'].startswith('g1_')])
# Independent selection from qualified netlist, mapped to actual PCell dimensions.
netpath=root/'designs/g1-guardian/blocks/g1_bgr/sim/qualification/runs/bgr_array_baseline_nominal_20260921_01/pex_nominal.spice'
net=netpath.read_text();units=[]
for line in net.splitlines():
 t=line.split()
 if not t or not re.match(r'X[MRQ]\d+$',t[0]):continue
 name=t[0];kind=None
 if name.startswith('XM'):
  kind='pmosHV' if 'sg13_hv_pmos' in t else 'nmosHV';w=float(re.search(r'\bw=([\d.]+)u',line)[1]);length=float(re.search(r'\bl=([\d.]+)u',line)[1]);hits=[r for r in rows if r['kind']==kind and r['gate_boxes_um']==[[length,w]]]
 elif name.startswith('XR'):
  kind='rhigh' if 'rhigh' in t else 'rppd';length=float(re.search(r'\bl=([\d.]+)u',line)[1]);hits=[r for r in rows if r['kind']==kind and abs(r['height_um']-(length+1.22))<1e-6]
 else:
  if t[1:5]==['vss']*4:continue
  kind='npn13G2';hits=[r for r in rows if r['kind']==kind]
 assert hits,name
 if name in ['XM40','XM46','XM53']:continue
 assert len({(r['width_um'],r['height_um']) for r in hits})==1
 units.append({'name':name,'kind':kind,'width_um':hits[0]['width_um'],'height_um':hits[0]['height_um'],'bbox_area_um2':hits[0]['bbox_area_um2']})
assert collections.Counter(u['kind'][0:3] for u in units)=={'pmo':16,'nmo':9,'npn':13,'rhi':15,'rpp':21}
basearea=sum(r['bbox_area_um2'] for r in rows);corearea=sum(r['bbox_area_um2'] for r in units);macro=84*124
# Local envelope constrained by neighboring macro edges; top IO inward edge1029.
window=[638,855,850,1029];wa=(window[2]-window[0])*(window[3]-window[1]);obstacles=[]
for r in placements:
 b=r['bbox_um'];overlap=max(0,min(b[2],window[2])-max(b[0],window[0]))*max(0,min(b[3],window[3])-max(b[1],window[1]))
 if overlap and (r['cell'].startswith('g1_') and r['cell']!='g1_bgr' or r['cell'].startswith('sg13g2_decap')):obstacles.append(dict(r,overlap_area_um2=overlap))
summary={'source_netlist_sha256':hashlib.sha256(netpath.read_bytes()).hexdigest(),'scaled_units':units,'scaled_count':len(units),'core_unit_bbox_sum_um2':corearea,'baseline_all_PCell_bbox_sum_um2':basearea,'baseline_macro_um2':macro,'baseline_macro_to_bbox_ratio':macro/basearea,'local_envelope_um':window,'local_envelope_area_um2':wa,'local_decaps_and_other_macro_intersections':obstacles,'scalings':{str(n):{'native_bbox_sum_um2':basearea+(n-1)*corearea,'same_baseline_overhead_estimate_um2':(basearea+(n-1)*corearea)*macro/basearea,'incremental_unit_count':(n-1)*len(units)} for n in [4,16]},'limitations':['PCell bboxes include native contacts/implants/wells but legal enclosure overlap can reduce their union. This is not an impossibility proof.','Existing macro overhead factor is a labeled extrapolation for guards/dummies/routing, not a floorplan.','Local envelope retains neighbor macros and ring positions, but contains route/PDN/decap resources. Available routable area is smaller; nothing is moved or deleted.','Larger nonlocal floorplan within same die is not evaluated.']}
(a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['scaled_units','local_decaps_and_other_macro_intersections']},indent=2))
