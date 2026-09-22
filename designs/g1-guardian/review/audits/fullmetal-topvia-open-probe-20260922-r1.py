#!/usr/bin/env python3
"""Remove each upper-only bridge cut from extraction geometry; trace all seven metal layers."""
import argparse,hashlib,json,os
from pathlib import Path
import pya
from sense_route_manifest import load_candidate_resistances
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--upper-screen',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
m,_=load_candidate_resistances(a.manifest);upper=json.loads(a.upper_screen.read_text());assert upper['candidate_sha256']==m['candidate_sha256']
targets=[row for row in upper['records'] if row['status'].startswith('not run')];assert len(targets)==8
ly=pya.Layout();ly.read(str(a.manifest.parent/'g1_chip_top.gds'));top=ly.cell('g1_chip_top');dbu=ly.dbu
metals=(8,10,30,50,67,126,134);cuts={19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134)}
results=[]
for target in targets:
    network=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,top,[]));layers={}
    for layer in metals:
        layers[layer]=network.make_layer(ly.layer(layer,0),'M'+str(layer));network.connect(layers[layer])
    box=pya.DBox(*target['cut_bbox_um']).to_itype(dbu)
    for cut,(lower,higher) in cuts.items():
        region=network.make_layer(ly.layer(cut,0),'V'+str(cut))
        if cut==133:
            removed=region&pya.Region(box);assert removed.area()==box.area()
            region=region-pya.Region(box)
        network.connect(region);network.connect(region,layers[lower]);network.connect(region,layers[higher])
    network.extract_netlist()
    nets=[network.probe_net(layers[layer],box.center()) for layer in (126,134)];assert all(net is not None for net in nets)
    ids=[{'circuit':net.circuit().name,'cluster_id':net.cluster_id} for net in nets]
    result={**target,'post_removal_probe_nets':ids,'all_seven_metal_path_after_cut_removal':ids[0]==ids[1],
        'status':'passed alternate full-metal path' if ids[0]==ids[1] else 'failed metal-only connectivity after cut removal'}
    results.append(result);print(target['net'],target['point_um'],result['status'],flush=True)
    a.output.write_text(json.dumps({'candidate_sha256':m['candidate_sha256'],'upper_screen_sha256':hashlib.sha256(a.upper_screen.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'Each selected actual.9um TopVia2 cut removed separately only from derived extraction region, never savedGDS. Seven drawingmetal layers and six cut types; no labels/virtualjoining, diffusion/deviceconduction or RC/current assumptions. Physical source unchanged. A disconnected metal path is a conditional robustness failure, not a stockDRC/LVS failure.',
        'results':results,'complete':len(results)==8},indent=2)+'\n')
