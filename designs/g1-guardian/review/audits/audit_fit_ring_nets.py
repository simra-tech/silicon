#!/usr/bin/env python3
"""Source-net-aware ring overlap and exact native/reserved candidate uppermetal.

Read-only in-memory experiment. No GDS, PDK change or legal-placement claim.
"""
import argparse,hashlib,json,os,sys
from pathlib import Path
for folder in ('/foss/pdks/ihp-sg13g2/libs.tech/klayout/python','/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python'):
    sys.path.insert(0,folder)
import pya,sg13g2_pycell_lib
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--gds',type=Path,required=True);p.add_argument('--pack',type=Path,required=True);p.add_argument('--ring-inventory',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text())
assert sha(a.gds)=='38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59'
pack=load(a.pack);old=load(a.ring_inventory);ly=pya.Layout();ly.read(str(a.gds));top=ly.cell('g1_chip_top');dbu=ly.dbu
def reg(cell,layer,datatype=0):return pya.Region(cell.begin_shapes_rec(ly.layer(layer,datatype))).merged()
metals=(8,10,30,50,67,126,134);cuts={19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134)}
net=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,top,[]));layers={}
for layer in metals:layers[layer]=net.make_layer(ly.layer(layer,0),'M'+str(layer));net.connect(layers[layer])
for layer,(lo,hi) in cuts.items():
    r=net.make_layer(ly.layer(layer,0),'V'+str(layer));net.connect(r);net.connect(r,layers[lo]);net.connect(r,layers[hi])
net.extract_netlist()
def inside_point(poly):
    pt=poly.bbox().center()
    if not poly.inside(pt):pt=list(poly.decompose_trapezoids())[0].bbox().center()
    assert poly.inside(pt);return pt
def netid(layer,point):
    n=net.probe_net(layers[layer],point);assert n is not None;return [n.circuit().name,n.cluster_id]
ring=[];delta=round((pack.get('ring_proposed_die_side_um',1414)-1350)/dbu)
for row in old['actual_core_ring_conductors']:
    layer=row['layer'];b=pya.DBox(*row['bbox_um']).to_itype(dbu);poly=pya.Polygon(b)
    assert (pya.Region(poly)-pya.Region(top.shapes(ly.layer(layer,0)))).is_empty()
    identity=netid(layer,b.center());x1,y1,x2,y2=b.left,b.bottom,b.right,b.top
    side=('east' if x1*dbu>986 else 'west') if layer==126 else ('north' if y1*dbu>986 else 'south')
    if layer==126:
        y2+=delta
        if side=='east':x1+=delta;x2+=delta
    else:
        x2+=delta
        if side=='north':y1+=delta;y2+=delta
    ring.append(dict(layer=layer,side=side,net=identity,original=poly,expanded=pya.Polygon(pya.Box(x1,y1,x2,y2))))
targets={r['name']:r for r in pack['macros']};names={'g1_dut_macro':'g1_dut','g1_dose_macro':'g1_dose','g1_bgr':'g1_bgr_candidate','g1_sense':'g1_sense_candidate'}
def move(region,oldbox,target):
    region=region.transformed(pya.Trans(-oldbox.left,-oldbox.bottom));new=target['bbox_um']
    if target.get('orientation','R0')=='R90':
        region=region.transformed(pya.Trans(pya.Trans.R90));dx=round(new[0]/dbu)+oldbox.height()
    else:dx=round(new[0]/dbu)
    return region.transformed(pya.Trans(dx,round(new[1]/dbu)))
rows=[];ls=0;obstructions=[]
def obstruction(name,layer,datatype,moved):
    relevant=(126,) if layer==125 else ((126,134) if layer==133 else (layer,))
    for target_layer in relevant:
        other=pya.Region()
        for rr in ring:
            if rr['layer']==target_layer:other.insert(rr['expanded'])
        overlap=moved&other
        nearby=moved.sized(5000)&other
        obstructions.append(dict(macro=name,source_layer=layer,datatype=datatype,ring_layer=target_layer,
            geometry_area_um2=moved.area()*dbu*dbu,overlap_um2=overlap.area()*dbu*dbu,
            conservative5um_box_clearance_passed=nearby.is_empty(),
            scope='Geometric ring-only screen;5um conservatively covers1.64/2um ordinary spacing,3umfill and5umwideTM2 recommendation. Not stockDRC or current/access/coupling acceptance.'))
for inst in top.each_inst():
    name=inst.cell.name
    if not name.startswith('g1_') or name in ('g1_bgr','g1_sense'):continue
    target_name=names.get(name,name)
    if name=='g1_ls_up':target_name='g1_ls_'+str(ls);ls+=1
    target=targets[target_name]
    for layer in (126,134,125,133):
        for datatype in ((0,22) if layer in (126,134) else (0,)):
            original=reg(inst.cell,layer,datatype).transformed(inst.trans)
            obstruction(name,layer,datatype,move(original,inst.bbox(),target))
    for layer in (126,134):
        original=reg(inst.cell,layer).transformed(inst.trans)
        for poly in original.each():
            identity=netid(layer,inside_point(poly));moved=move(pya.Region(poly),inst.bbox(),target)
            for rr in ring:
                if rr['layer']!=layer:continue
                for view in ('original','expanded'):
                    overlap=moved&pya.Region(rr[view])
                    if overlap.is_empty():continue
                    rows.append(dict(macro=name,layer=layer,ring_side=rr['side'],ring_view=view,
                        macro_original_physical_net=identity,ring_physical_net=rr['net'],same_original_net=identity==rr['net'],
                        overlap_um2=overlap.area()*dbu*dbu))
# Actual native candidate uppermetal: full PCell geometry at source-bound bbox placements.
lib=pya.Library.library_by_name('SG13_dev','sg13g2');probe=pya.Layout();probe.dbu=dbu
def pcell(kind,params):
    index=lib.layout().add_pcell_variant(lib.layout().pcell_id(kind),params)
    return probe.cell(probe.add_lib_cell(lib,index))
def preg(cell,layer):return pya.Region(cell.begin_shapes_rec(probe.layer(layer,0))).merged()
def place_native(cell,bbox,offset=(0,0)):
    oldbox=cell.bbox();dx=round((bbox[0]+offset[0])/dbu)-oldbox.left;dy=round((bbox[1]+offset[1])/dbu)-oldbox.bottom
    assert abs(oldbox.width()*dbu-(bbox[2]-bbox[0]))<1e-7 and abs(oldbox.height()*dbu-(bbox[3]-bbox[1]))<1e-7
    return {layer:preg(cell,layer).transformed(pya.Trans(dx,dy)) for layer in (67,126,134,125,133)}
native_summary={};geometry={name:{layer:pya.Region() for layer in (67,126,134,125,133)} for name in ('g1_bgr_candidate','g1_sense_candidate')}
cache={}
for d in pack['BGR_devices']:
    # Unique geometry source parameters are preserved, including requested full resistor length.
    import re
    pars=dict(re.findall(r'\b(w|l)=([^\s]+)',d['source_line']));kind=d['kind']
    if kind=='npn13G2':pars=dict(we='0.07u',le='0.9u',Nx=1)
    elif kind in ('rppd','rhigh'):pars.update(Calculate='R',b=0)
    else:pars['ng']=1
    key=(kind,json.dumps(pars,sort_keys=True))
    if key not in cache:cache[key]=pcell(kind,pars)
    placed=place_native(cache[key],d['bbox_um'])
    for layer,r in placed.items():geometry['g1_bgr_candidate'][layer]+=r
gm=load(Path(__file__).with_name('gm4-pcell-footprint-20260922-r2.json'))
source={r['device']:r for r in gm['devices'] if r['view']=='candidate'}
for d in pack['main_OTA_devices']:
    record=source[d['name']];cell=pcell(record['kind'],record['parameters']);placed=place_native(cell,d['bbox_um'],(5,5))
    for layer,r in placed.items():geometry['g1_sense_candidate'][layer]+=r
sense_cell=ly.cell('g1_sense');otas=[i.cell for i in sense_cell.each_inst() if i.cell.name.startswith('g1_ota')];assert len(otas)==3
for part in pack['SENSE_parts']:
    if not part['name'].startswith('unchanged_'):continue
    cell=otas[0];b=cell.bbox();target=part['bbox_um'];dx=round(target[0]/dbu)-b.left;dy=round(target[1]/dbu)-b.bottom
    assert abs(b.width()*dbu-(target[2]-target[0]))<1e-7 and abs(b.height()*dbu-(target[3]-target[1]))<1e-7
    for layer in geometry['g1_sense_candidate']:geometry['g1_sense_candidate'][layer]+=reg(cell,layer).transformed(pya.Trans(dx,dy))
for name,regions in geometry.items():
    target=targets[name];localbox=pya.Box(0,0,round(pack['BGR_macro_um'][0]/dbu),round(pack['BGR_macro_um'][1]/dbu)) if name=='g1_bgr_candidate' else pya.Box(0,0,385000,240000)
    native_summary[name]={}
    for layer,r in regions.items():
        r=r.merged();moved=move(r,localbox,target)
        if layer in (126,134,125,133):obstruction(name,layer,0,moved)
        overlaps=[dict(side=rr['side'],area_um2=(moved&pya.Region(rr['expanded'])).area()*dbu*dbu) for rr in ring if rr['layer']==layer]
        native_summary[name][str(layer)]=dict(native_area_um2=r.area()*dbu*dbu,expanded_ring_same_layer_overlaps=overlaps)
    # TopM1 external capacitor tab/TopVia access remains reserved, not drawn.
    if name=='g1_sense_candidate':
        reserved=move(pya.Region(pya.Box(5000,113000,235000,166000)),localbox,target)
        native_summary[name]['reserved_external_MIM_TopM1_access']=dict(
            local_bbox_um=[5,113,235,166],scope='reservation only; routing/contact connectivity not run',
            expanded_ring_overlap_um2=sum((reserved&pya.Region(rr['expanded'])).area()*dbu*dbu for rr in ring if rr['layer']==126))
        obstruction(name+'_external_MIM_access_reservation',126,0,reserved)
different=[r for r in rows if r['ring_view']=='expanded' and not r['same_original_net']]
obstruction_failed=[r for r in obstructions if not r['conservative5um_box_clearance_passed']]
result=dict(status='failed proposed ring no-short/obstruction screen' if different or obstruction_failed else 'passed scoped ring-only native/fill/via5um screen; new access/coupling/fullgeometry not qualified',
    source_sha256=sha(a.gds),pack_sha256=sha(a.pack),ring_inventory_sha256=sha(a.ring_inventory),script_sha256=sha(Path(__file__)),
    KLayout=pya.__version__,proposed_ring_die_side_um=1350+delta*dbu,
    ring_expansion_scope='In-memory rectangular extrapolation of actual8stockchecked15um conductors; no new ring GDS/deck run. West/south locations unchanged; north/east translated and lengths extended.',
    moved_macro_ring_intersections=rows,expanded_different_net_overlap_count=len(different),
    expanded_different_net_overlap_um2=sum(r['overlap_um2'] for r in different),candidate_native_uppermetal=native_summary,
    ring_obstruction_and_via_projection=obstructions,ring_obstruction_failures=obstruction_failed,
    no_saved_GDS=True,limitations=['Source-net IDs are actual7metal connectivity, not name/label joining.',
        'Native BGR0uppermetal does not qualify under-ring placement: new signal/power routing, contact access, via stacks, spacing and coupling remain not run.',
        'Exact gm4 native MIM and unchanged buffer topmetal included; resistor bank uses only lower metals. New external capacitor tab is an explicit reservation, not routed geometry.',
        'Unchanged macro local datatype22 filler is screened. New BGR/SENSE filler and global filler are not generated or screened; no full-fill clearance or density claim.',
        'No guard/access/routing/fullstockcheck or adoption claim.'])
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='moved_macro_ring_intersections'},indent=2))
