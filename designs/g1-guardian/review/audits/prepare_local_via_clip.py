#!/usr/bin/env python3
"""PREPARATION-ONLY helper until authorized: uniquely labeled local via metal clips."""
import argparse,hashlib,json,os
from pathlib import Path
import pya
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage-manifest',type=Path,required=True);p.add_argument('--stage-id',type=int,choices=[4,19],required=True);p.add_argument('--gds',type=Path,required=True);p.add_argument('--expected-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest();assert sha(a.gds)==a.expected_sha256
m=json.loads(a.stage_manifest.read_text());stage=m['via_patches'][a.stage_id];point=stage['point_um'];bounds=[point[0]-6,point[1]-6,point[0]+6,point[1]+6]
assert all(bounds[0]<=b[0] and bounds[1]<=b[1] and bounds[2]>=b[2] and bounds[3]>=b[3] for b in [stage['added_cut_bbox_um']]+[row['landing_bbox_um'] for row in stage['metals']])
ly=pya.Layout();ly.read(str(a.gds));top=ly.cell('g1_chip_top');dbu=ly.dbu;window=pya.DBox(*bounds).to_itype(dbu)
metals=(8,10,30,50,67,126,134);cuts={19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134)}
network=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,top,[]));layers={}
for layer in metals:layers[layer]=network.make_layer(ly.layer(layer,0),'M'+str(layer));network.connect(layers[layer])
for cut,(lower,upper) in cuts.items():
    region=network.make_layer(ly.layer(cut,0),'V'+str(cut));network.connect(region);network.connect(region,layers[lower]);network.connect(region,layers[upper])
network.extract_netlist()
def identity(layer,p):
    net=network.probe_net(layers[layer],p);assert net is not None
    return [net.circuit().name,net.cluster_id]
target_point=pya.DPoint(*point).to_itype(dbu);target_layer=stage['metals'][0]['layer'];target=identity(target_layer,target_point)
inventory=json.loads(Path(__file__).with_name('route-via-inventory-20260922-r2.json').read_text());anchors=[]
for net in inventory['nets']:
    if net['net']!=stage['net']:continue
    for via in net['vias']:
        for cut in via['cut_stages']:
            observed=identity(cut['lower_layer'],pya.DPoint(*via['point_um']).to_itype(dbu));assert observed==target
            anchors.append({'point_um':via['point_um'],'layer':cut['lower_layer'],'physical_net':observed})
assert anchors
regions={};labels=[];primary=0
for layer in list(metals)+list(cuts):
    for datatype in ([0,22] if layer in metals else [0]):
        region=(pya.Region(top.begin_shapes_rec_overlapping(ly.layer(layer,datatype),window))&pya.Region(window)).merged();regions[layer,datatype]=region
        if layer not in metals:continue
        for index,polygon in enumerate(region.each()):
            pt=polygon.bbox().center()
            if not polygon.inside(pt):pt=list(polygon.decompose_trapezoids())[0].bbox().center()
            assert polygon.inside(pt)
            physical=None if datatype==22 else identity(layer,pt)
            group='fill' if datatype==22 else ('target' if physical==target else 'grounded_context')
            if layer==target_layer and datatype==0 and polygon.inside(target_point):name='P';pt=target_point;primary+=1
            else:name=('PSEG' if group=='target' else 'FILL' if group=='fill' else 'CTX')+'_L%d_%d'%(layer,index)
            labels.append({'label':name,'group':group,'source_layer':[layer,datatype],'point_dbu':[pt.x,pt.y],'physical_full_net':physical})
assert primary==1 and all(row['physical_full_net']==target for row in labels if row['group']=='target')
a.output.mkdir(parents=True);variants=[]
for mode in ('no_fill','actual_fill'):
    out=pya.Layout();out.dbu=dbu;cell=out.create_cell('sense_fill_clip')
    for (layer,datatype),region in regions.items():
        if mode=='actual_fill' or datatype!=22:cell.shapes(out.layer(layer,datatype)).insert(region)
    for label in labels:
        layer,datatype=label['source_layer']
        if mode=='actual_fill' or datatype!=22:cell.shapes(out.layer(layer,25)).insert(pya.Text(label['label'],pya.Trans(*label['point_dbu'])))
    path=a.output/(mode+'.gds');out.write(str(path));check=pya.Layout();check.read(str(path))
    for (layer,datatype),region in regions.items():
        expected=region if mode=='actual_fill' or datatype!=22 else pya.Region()
        assert (expected^pya.Region(check.cell('sense_fill_clip').begin_shapes_rec(check.layer(layer,datatype)))).is_empty()
    variants.append({'variant':mode,'sha256':sha(path)})
result={'status':'passed geometry/identity preparation only','source_gds_sha256':a.expected_sha256,'stage_manifest_sha256':sha(a.stage_manifest),'script_sha256':sha(Path(__file__)),
    'stage_id':a.stage_id,'net':stage['net'],'point_um':point,'clip_bbox_um':bounds,'actual_target_net':target,'matching_route_anchors':anchors,'labels':labels,'variants':variants,
    'electrical_boundary':'Each local conductor component keeps a UNIQUE label. Only components independently proven on target full-layout metalnet may later be held at same ideal potential as a declared outside-clip boundary. No text-based physical connectivity joining. Otherdrawingnetsgrounded andfillfloating/grounded are diagnostics, not actual activity.',
    'scope':'Metal/via/fill only12x12um window; no device/diffusion/depletion or fullrouteR. Prepared helper is not stockDRC/PEX/circuitacceptance. Remoteclockstage4 andT2F_VDDstage19 only; no automatic expansion.'}
(a.output/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');assert sha(a.gds)==a.expected_sha256
print(json.dumps({'status':result['status'],'stage_id':a.stage_id,'target_components':sum(row['group']=='target' for row in labels),'variants':variants}))
