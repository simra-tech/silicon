#!/usr/bin/env python3
"""Compare actual drawing-metal partitions and simultaneous old/new cut removal."""
import argparse,hashlib,json,os
from pathlib import Path
import pya
from sense_route_manifest import load_candidate_resistances
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--parent-manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
m,_=load_candidate_resistances(a.manifest);old,_=load_candidate_resistances(a.parent_manifest);assert m['parent_candidate_sha256']==old['candidate_sha256']
base=Path(__file__).parent;inventory=json.loads((base/'route-via-inventory-20260922-r2.json').read_text());mesh=json.loads((base/'supply-mesh-20260921-r3/mesh.json').read_text())
metals=(8,10,30,50,67,126,134);cuts={19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134)}
probes=[]
for net in inventory['nets']:
    for via in net['vias']:
        for stage in via['cut_stages']:
            for layer in (stage['lower_layer'],stage['upper_layer']):probes.append((net['net'],layer,tuple(via['point_um'])))
for rail,source in mesh['source_interfaces'].items():probes.append((rail,{'TopMetal1':126,'TopMetal2':134}[source[0]],tuple(source[1:])))
for rail,network in mesh['networks'].items():
    for row in network['terminals']:probes.append((rail,126,tuple(row['point_um'])))
probes=list(dict.fromkeys(probes));results=[];partitions=[]
for label,path,remove_key in [('parent',a.parent_manifest.parent/'g1_chip_top.gds',None),('candidate',a.manifest.parent/'g1_chip_top.gds',None),('candidate_all21_old_cuts_removed',a.manifest.parent/'g1_chip_top.gds','old_cut_bbox_um'),('candidate_all21_added_cuts_removed',a.manifest.parent/'g1_chip_top.gds','added_cut_bbox_um')]:
    ly=pya.Layout();ly.read(str(path));top=ly.cell('g1_chip_top');dbu=ly.dbu;network=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,top,[]));layers={}
    for layer in metals:layers[layer]=network.make_layer(ly.layer(layer,0),'M'+str(layer));network.connect(layers[layer])
    for cut,(lower,upper) in cuts.items():
        region=network.make_layer(ly.layer(cut,0),'V'+str(cut))
        if remove_key:
            remove=pya.Region()
            for patch in m['via_patches']:
                if patch['cut_layer']==cut:remove.insert(pya.DBox(*patch[remove_key]).to_itype(dbu))
            assert (remove-region).is_empty();region=region-remove
        network.connect(region);network.connect(region,layers[lower]);network.connect(region,layers[upper])
    network.extract_netlist();ids=[];missing=[]
    for index,(name,layer,point) in enumerate(probes):
        net=network.probe_net(layers[layer],pya.DPoint(*point).to_itype(dbu))
        ids.append(None if net is None else (net.circuit().name,net.cluster_id))
        if net is None:missing.append(index)
    # Stable partition encoding, never compare incidental KLayout cluster numbers across layouts.
    first={};partition=[]
    for index,identity in enumerate(ids):
        if identity is None:partition.append(None)
        else:first.setdefault(identity,index);partition.append(first[identity])
    partitions.append(partition)
    net_counts={circuit.name:sum(1 for net in circuit.each_net()) for circuit in network.netlist().each_circuit()}
    row={'view':label,'missing_probe_indices':missing,'net_counts_by_circuit':net_counts,'partition_matches_parent':partition==partitions[0],
        'full_net_count_matches_parent':not results or net_counts==results[0]['net_counts_by_circuit']}
    results.append(row);print(label,'partition',row['partition_matches_parent'],'netcounts',row['full_net_count_matches_parent'],'missing',len(missing),flush=True)
    a.output.write_text(json.dumps({'candidate_sha256':m['candidate_sha256'],'parent_sha256':old['candidate_sha256'],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'All seven drawing metals and six via types, no labels or device conduction. Probe partitions cover selected DEF routes,36macroaccesses and modeled source interfaces. Simultaneously remove each original cut, then each added cut, only from extraction regions, never GDS. Local common-landings separately prove either cut bridges each stage.',
        'probes':probes,'results':results,'status':'passed' if len(results)==4 and all(r['partition_matches_parent'] and r['full_net_count_matches_parent'] and not r['missing_probe_indices'] for r in results) else 'not run' if len(results)<4 else 'failed'},indent=2)+'\n')
