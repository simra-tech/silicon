#!/usr/bin/env python3
"""Selected cell internal cut/contact groups without name-based electrical merging."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import pya
from sense_route_manifest import load_candidate_resistances

METALS = [8,10,30,50,67,126,134]
CUTS = {19:(8,10,'Via1',.19),29:(10,30,'Via2',.19),49:(30,50,'Via3',.19),
        66:(50,67,'Via4',.19),125:(67,126,'TopVia1',.42),133:(126,134,'TopVia2',.9)}
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--cells',nargs='+',default=['sg13g2_IOPadOut30mA','sg13g2_IOPadIOVdd','sg13g2_IOPadIOVss','sg13g2_IOPadAnalog'])
a=p.parse_args();assert not a.output.exists();assert len(os.sched_getaffinity(0))==1;assert pya.__version__=='0.30.9'
manifest,_=load_candidate_resistances(a.manifest)
ly=pya.Layout();ly.read(str(a.manifest.parent/'g1_chip_top.gds'));dbu=ly.dbu
limit_path=Path(__file__).with_name('current_limits_20260922.json');limits=json.loads(limit_path.read_text())
records=[]
for cell_name in a.cells:
    cell=ly.cell(cell_name);assert cell is not None
    regions={number:pya.Region(cell.begin_shapes_rec(ly.layer(number,0))).merged() for number in METALS}
    islands={number:list(region.each()) for number,region in regions.items()}
    active=pya.Region(cell.begin_shapes_rec(ly.layer(1,0))).merged()
    poly=pya.Region(cell.begin_shapes_rec(ly.layer(5,0))).merged()
    resistor=pya.Region(cell.begin_shapes_rec(ly.layer(128,0))).merged()
    islands['diffusion']=list((active-poly).merged().each())
    islands['poly']=list((poly-resistor).merged().each())
    network=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,cell,[]));nl={}
    for number in METALS:
        nl[number]=network.make_layer(ly.layer(number,0),'M'+str(number));network.connect(nl[number])
    for cut,(lower,upper,_,_) in CUTS.items():
        layer=network.make_layer(ly.layer(cut,0),'V'+str(cut));network.connect(layer);network.connect(layer,nl[lower]);network.connect(layer,nl[upper])
    network.extract_netlist()
    def probe(layer,point):
        net=network.probe_net(nl[layer],point)
        return None if net is None else {'circuit':net.circuit().name,'cluster_id':net.cluster_id}
    label_probes=[]
    top_port_label_probes=[]
    for number in METALS:
        it=cell.begin_shapes_rec(ly.layer(number,25))
        while not it.at_end():
            shape=it.shape()
            if shape.is_text() and shape.text.string.lower() in ('pad','iovdd','iovss','vdd','vdda','vss','c2p','gate_core','sense_p','sense_n','vref','vref_buf','iptat','isense','pbias','pcasc'):
                point=it.trans()*shape.text.trans.disp
                label_probes.append({'label':shape.text.string,'layer':number,'point_um':[point.x*dbu,point.y*dbu], 'physical_net':probe(number,point)})
            it.next()
        for shape in cell.shapes(ly.layer(number,25)).each():
            if shape.is_text() and shape.text.string.lower() in ('pad','iovdd','iovss','vdd','vdda','vss','c2p','gate_core','sense_p','sense_n','vref','vref_buf','iptat','isense','pbias','pcasc'):
                point=shape.text.trans.disp
                top_port_label_probes.append({'label':shape.text.string,'layer':number,'point_um':[point.x*dbu,point.y*dbu],'physical_net':probe(number,point)})
    def island_at(kind,shape):
        center=shape.bbox().center()
        matches=[index for index,p in enumerate(islands[kind]) if p.bbox().contains(center) and p.inside(center)]
        if len(matches)!=1:return None
        index=matches[0]
        return index if (pya.Region(shape)-pya.Region(islands[kind][index])).is_empty() else None
    groups={};unassigned=[]
    for cut,(lower,upper,name,canonical_width) in {6:(None,8,'Contact',.16),**CUTS}.items():
        cuts=pya.Region(cell.begin_shapes_rec(ly.layer(cut,0))).merged()
        for shape in cuts.each():
            bottom_kind=lower
            if cut==6:
                candidates=[(kind,island_at(kind,shape)) for kind in ('diffusion','poly')]
                candidates=[item for item in candidates if item[1] is not None]
                if len(candidates)==1:bottom_kind,bottom=candidates[0]
                else:bottom=None
            else:bottom=island_at(lower,shape)
            upper_id=island_at(upper,shape)
            if bottom is None or upper_id is None:
                unassigned.append({'cut_layer':cut,'bbox_um':str(shape.bbox().to_dtype(dbu)), 'lower_island':bottom, 'upper_island':upper_id})
                continue
            key=(cut,bottom_kind,bottom,upper_id)
            physical=probe(upper,shape.bbox().center())
            group=groups.setdefault(key,{'cut_layer':cut,'cut_name':name,'lower_kind':bottom_kind,'upper_layer':upper,
                'lower_plate_bbox_um':str(islands[bottom_kind][bottom].bbox().to_dtype(dbu)),
                'upper_plate_bbox_um':str(islands[upper][upper_id].bbox().to_dtype(dbu)),
                'physical_upper_net':physical,'cut_count':0,'noncanonical_square_cut_count':0,'cut_bboxes_um':[]})
            assert group['physical_upper_net']==physical
            bbox=shape.bbox();group['cut_count']+=1
            group['noncanonical_square_cut_count']+=int(not shape.is_box() or abs(bbox.width()*dbu-canonical_width)>1e-9 or abs(bbox.height()*dbu-canonical_width)>1e-9)
            group['cut_bboxes_um'].append(str(bbox.to_dtype(dbu)))
    for group in groups.values():
        count=group['cut_count'];limit=limits['cut_limit_mA'][group['cut_name']];target=limits['engineering_screen']['utilization_target']
        group.update(existing_label_aliases=sorted({row['label'] for row in label_probes if row['physical_net'] is not None and row['physical_net']==group['physical_upper_net']}),
                     top_cell_port_label_aliases=sorted({row['label'] for row in top_port_label_probes if row['physical_net'] is not None and row['physical_net']==group['physical_upper_net']}),
                     one_cut_open_same_plate_local_bridge_remaining=count>1,
                     per_standard_cut_table_limit_mA_105C_11years=limit,
                     target_branch_mA_worst_single_cut_allocation=target*limit,
                     target_branch_mA_conditional_equal_sharing=target*limit*count,
                     target_branch_mA_conditional_equal_sharing_one_cut_open=target*limit*max(count-1,0),
                     current_margin_status='not run; device/branch current allocation and unequal sharing unknown',
                     shape_applicability='standard square cuts' if not group['noncanonical_square_cut_count'] else 'not run: noncanonical contact/cut geometry needs independent applicable-limit interpretation')
    record={'cell':cell_name,'existing_label_probes_without_merging':label_probes,'top_cell_port_label_probes_without_merging':top_port_label_probes,
            'label_scope_note':'Recursive child text retains child-local aliases; it is not a top-cell net identity. Only top-cell port labels are used for port association; physical tracing never merges labels.',
            'groups':list(groups.values()),'unassigned_cuts':unassigned,
            'top_instances':[str(inst.cplx_trans) for inst in ly.cell('g1_chip_top').each_inst() if inst.cell.name==cell_name],
            'counts':{'groups':len(groups),'single_cut_groups':sum(group['cut_count']==1 for group in groups.values()),'unassigned_cuts':len(unassigned)}}
    records.append(record);print(cell_name,record['counts'],flush=True)
    a.output.write_text(json.dumps({'candidate_sha256':manifest['candidate_sha256'],'klayout_version':pya.__version__,
        'scope':'Selected cell internal connected lower/upper conductor plate-pair cut groups, not claimed uniformly loaded arrays. Contacts grouped by actual diffusion-minus-gate or poly-minus-recognized-resistor island and M1 plate. No substrate/well/device-current merging, no electrical netlist comparison. All current allocations/margins and full-path single-cut-open checks notrun.',
        'limit_record_sha256':hashlib.sha256(limit_path.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cells':records},indent=2)+'\n')
