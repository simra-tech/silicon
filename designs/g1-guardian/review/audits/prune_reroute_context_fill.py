"""Remove only whole pure floating-fill repetitions near new signal metal.

Conservative design-side clearance reservations, not DRC-rule modifications.
Native cells, all functional metal, pins, routes and bond coordinates are held.
"""
import argparse,collections,json,os,time
from pathlib import Path
import pya
from place_closed_analog import region,sha
from prepare_digital_reroute_native_hierarchy import hierarchy,properties
LAYERS={8:600,10:600,30:600,50:600,67:600,126:3000,134:3000}
def payload(layout,cell):
 assert '_FILL_CELL' in cell.name and not list(cell.each_inst())
 rows=[(layout.get_info(li),s) for li in layout.layer_indexes() for s in cell.shapes(li).each()]
 assert len(rows)==1
 info,s=rows[0];assert info.layer in LAYERS and info.datatype==22 and not s.is_text()
 assert not s.properties() and not cell.properties()
 return info.layer,s.polygon
def direct(layout,cell):
 return sorted((layout.get_info(li).layer,layout.get_info(li).datatype,s.to_s(),properties(s)) for li in layout.layer_indexes() for s in cell.shapes(li).each())
def protected(top):
 return collections.Counter((i.cell.name,str(i.cell_inst),properties(i)) for i in top.each_inst() if '_FILL_CELL' not in i.cell.name)
def main():
 p=argparse.ArgumentParser()
 for key in ['candidate','output']:p.add_argument('--'+key,type=Path,required=True)
 a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
 meta=json.loads((a.candidate/'analysis.json').read_text());source=a.candidate/'signal_routed_native.gds'
 assert meta['status']=='passed native-preserving DEF signal-route streamout and exact geometry roundtrip'
 assert sha(source)==meta['GDS_sha256']
 a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes());start=time.monotonic()
 result=dict(status='running',source_GDS_sha256=sha(source),source_metadata_sha256=sha(a.candidate/'analysis.json'),
  clearance_reservation_dbu=LAYERS,not_run=['Fresh stock DRC antenna density','Terminal partition','Fill-dependent PEX and electrical','Adoption'])
 try:
  ly=pya.Layout();ly.read(str(source));top=ly.top_cell();assert top.name=='placed_core_NOT_CONNECTED_FULLCHIP' and ly.dbu==.001
  route,=[i for i in top.each_inst() if i.cell.name=='new_signal_routes'];assert route.cplx_trans==pya.ICplxTrans() and route.na<=1 and route.nb<=1
  windows={n:region(ly,route.cell,pya.LayerInfo(n,0)).sized(halo) for n,halo in LAYERS.items()}
  before=hierarchy(ly,top);direct_before=direct(ly,top);protected_before=protected(top);bbox=top.bbox();top_properties=properties(top)
  fills={n:region(ly,top,pya.LayerInfo(n,22)) for n in LAYERS};removed={n:pya.Region() for n in LAYERS};ledger=[]
  for i in list(top.each_inst()):
   if '_FILL_CELL' not in i.cell.name:continue
   infos=[ly.get_info(li) for li in ly.layer_indexes() if not i.cell.shapes(li).is_empty()]
   if not any(info.layer in LAYERS and info.datatype==22 for info in infos):continue
   n,poly=payload(ly,i.cell);assert not i.properties()
   if windows[n].is_empty() or not i.bbox().overlaps(windows[n].bbox()):continue
   selected=[];keep=[]
   for tr in i.cell_inst.each_cplx_trans():
    placed=poly.transformed(tr)
    if (pya.Region(placed)&windows[n]).is_empty():keep.append(tr)
    else:selected.append((tr,placed))
   if not selected:continue
   ledger.append(dict(cell=i.cell.name,original_array=str(i.cell_inst),layer=n,
    removed=[dict(transform=str(tr),polygon=placed.to_s()) for tr,placed in selected],retained_transforms=[str(tr) for tr in keep]))
   index=i.cell_index;i.delete()
   for tr in keep:top.insert(pya.CellInstArray(index,tr))
   for tr,placed in selected:removed[n].insert(placed)
  assert ledger and protected(top)==protected_before and direct(ly,top)==direct_before and properties(top)==top_properties and top.bbox()==bbox
  after=hierarchy(ly,top);assert all(before[name]==h for name,h in after.items() if name!=top.name)
  areas=[]
  for n in LAYERS:
   actual=region(ly,top,pya.LayerInfo(n,22));assert (actual^(fills[n]-removed[n])).is_empty()
   areas.append(dict(layer=n,removed_area_um2=(fills[n]-actual).area()*1e-6,repetitions=sum(len(r['removed']) for r in ledger if r['layer']==n)))
  clean=pya.Layout();clean.dbu=ly.dbu;ct=clean.create_cell(top.name);ct.copy_tree(top);assert hierarchy(clean,ct)==after
  output=a.output/'route_fill_pruned.gds';clean.write(str(output));saved=pya.Layout();saved.read(str(output));st=saved.top_cell()
  assert hierarchy(saved,st)==after and st.bbox()==bbox and saved.dbu==ly.dbu and sha(source)==meta['GDS_sha256']
  result.update(status='passed exact route-near floating-fill pruning',GDS_sha256=sha(output),top_cell=top.name,ledger=ledger,removed_by_layer=areas,
   native_cell_definitions='passed all reachable non-root definitions including properties held',functional_root_geometry='passed all direct shapes texts and nonfill instances held',
   exact_single_top_roundtrip='passed',source_terminal_partition_inheritance='not assumed; independent fresh check required')
 except Exception as e:result.update(status='failed route-near fill proof',error=repr(e));raise
 finally:
  result['wall_s']=time.monotonic()-start;(a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
