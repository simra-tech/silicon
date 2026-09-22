#!/usr/bin/env python3
"""Trace actual old/new metal nets for every moved decap; no label-based joins."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import pya

HERE=Path(__file__).resolve().parent
DESIGN=HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def physical(layout,top):
    net=pya.LayoutToNetlist(pya.RecursiveShapeIterator(layout,top,[]))
    metals={}
    for layer in (8,10,30,50,67,126,134):
        metals[layer]=net.make_layer(layout.layer(layer,0),'M'+str(layer))
        net.connect(metals[layer])
    for layer,lo,hi in ((19,8,10),(29,10,30),(49,30,50),(66,50,67),(125,67,126),(133,126,134)):
        cut=net.make_layer(layout.layer(layer,0),'V'+str(layer))
        net.connect(cut)
        net.connect(cut,metals[lo])
        net.connect(cut,metals[hi])
    net.extract_netlist()
    return net,metals


def identity(net,metal,point):
    found=net.probe_net(metal,pya.Point(*point))
    return (found.circuit().name,found.cluster_id) if found is not None else None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--placement',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    manifest=args.placement/'analysis.json'
    data=json.loads(manifest.read_text())
    assert data['status']=='passed source-preserving core placement' and len(data['decaps'])==4662
    original=DESIGN/'blocks/g1_padring/layout/g1_chip_top.gds'
    placed=args.placement/'placed_core.gds'
    assert sha(original)==data['baseline_sha256'] and sha(placed)==data['GDS_sha256']
    old=pya.Layout();old.read(str(original))
    new=pya.Layout();new.read(str(placed))
    oldnet,oldlayers=physical(old,old.cell('g1_chip_top'))
    newnet,newlayers=physical(new,new.top_cell())
    probes=[];errors=[];groups=collections.defaultdict(set)
    for row in data['decaps']:
        pair={}
        for label,point in row['pins'].items():
            before=identity(oldnet,oldlayers[8],point['original_dbu'])
            after=identity(newnet,newlayers[8],point['placed_dbu'])
            if before is None or after is None:
                errors.append(dict(index=row['index'],pin=label,error='off-metal probe',before=before,after=after))
            if before is not None and after is not None:
                groups[after].add(before)
            pair[label]=dict(original=before,placed=after)
        if pair['VDD']['original']==pair['VSS']['original']:
            errors.append(dict(index=row['index'],error='original VDD/VSS joined'))
        if pair['VDD']['placed']==pair['VSS']['placed']:
            errors.append(dict(index=row['index'],error='placed VDD/VSS joined'))
        probes.append(dict(index=row['index'],cell=row['cell'],pins=pair))
    merges=[dict(placed=list(k),original=[list(n) for n in sorted(v)]) for k,v in groups.items() if len(v)>1]
    old_groups=collections.Counter(tuple(p['pins']['VDD']['original']) for p in probes if p['pins']['VDD']['original'] is not None)
    result=dict(status='passed scoped decap domain no-merge' if not errors and not merges else 'failed scoped decap domain no-merge',
                script_sha256=sha(Path(__file__)),placement_manifest_sha256=sha(manifest),
                baseline_sha256=sha(original),placed_sha256=sha(placed),KLayout=pya.__version__,
                decaps=len(probes),metal_backed_pin_probes=2*len(probes)-sum(e.get('error')=='off-metal probe' for e in errors),
                errors=errors,distinct_original_net_merges=merges,
                original_supply_cluster_counts=[dict(net=list(k),decaps=v) for k,v in sorted(old_groups.items())],
                method='Seven drawing metals and six via cuts only; no text/global-name/virtual connections. Preserve actual original-net identities, not inferred voltage labels.',
                not_run=['all macro signal and power connectivity','decap source domain voltage/name assignment',
                         'row feeds/currentIR','stockDRC/LVS','fullchip assembly and electrical qualification'],probes=probes)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='probes'},indent=2))
    raise SystemExit(bool(errors or merges))


if __name__=='__main__':
    main()
