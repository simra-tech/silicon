#!/usr/bin/env python3
"""Read-only native conductor ownership for prospective remaining power egress."""
import argparse
import json
import os
from pathlib import Path
import sys
import networkx as nx
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from place_closed_analog import sha
HELPERS=HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4'
sys.path.insert(0,str(HELPERS))
from inventory_power_cutpaths import metal_graph

PROPOSED={
    'i_core.u_bgr':{'vdd':[(67,743.4,878.)], 'vss':[(67,749.65,873.)]},
    'i_core.u_trip':{'IOVDD':[(30,x,938.75)for x in (792.,836.,880.,924.,968.)],
                     'VDD':[(30,x,942.)for x in (792.,880.,968.)],
                     'VSS':[(30,x,737.)for x in (792.,880.,968.)]},
    'i_core.u_t2f':{'vdd':[(30,1044.,1054.3)],'vdd12':[(30,1044.,1047.6)],'vss':[(30,1039.2,954.3)]},
    'i_core.u_osc':{'VDD':[(30,772.,1089.57)],'VSS':[(30,774.,954.)]},
    'i_core.u_gate':{'vdda':[(30,734.,600.)],'vdd':[(30,767.32,546.)],'vss':[(30,778.65,600.)]},
}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--final-core',type=Path,required=True)
    p.add_argument('--inventory',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    meta=json.loads((a.final_core/'analysis.json').read_text());inv=json.loads(a.inventory.read_text())
    source=a.final_core/'refreshed_core.gds'
    assert sha(source)==meta['GDS_sha256']==inv['final_core_GDS_sha256']
    assert meta['BGR_source_GDS_sha256']=='6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04'
    assert meta['status'].startswith('passed') and inv['status'].startswith('passed')
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    layout=pya.Layout();layout.read(str(source));top=layout.top_cell();rows=[];errors=[]
    for instance,pinproposals in PROPOSED.items():
        terminals=[r for r in inv['terminals']if r['instance']==instance]
        master=terminals[0]['master'];cellname='g1_bgr_candidate'if master=='g1_bgr'else 'retained_'+master
        assert any(r['name']==cellname for r in meta['copied_native_cells'])
        instances=[i for i in top.each_inst()if i.cell.name==cellname];assert len(instances)==1,(instance,cellname)
        placed=instances[0];cell=placed.cell
        graph,components,cuts,hit=metal_graph(cell)
        owners={}
        for terminal in terminals:
            pin=terminal['pin']
            if instance=='i_core.u_bgr':
                marker=meta['BGR_chip_ports'][pin];layer=marker['layer'];point=pya.Point(*marker['point_dbu'])
            else:
                window=terminal['windows'][0];layer=window['layer'];point=pya.Box(*window['bbox']).center()
            local=placed.trans.inverted()*point;nodes=hit(layer,local)
            assert len(nodes)==1,(instance,pin,local,nodes)
            own=nx.node_connected_component(graph,nodes[0]);owners[pin]=own
            candidates=[]
            for pl,x,y in pinproposals[pin]:
                point=pya.DPoint(x,y).to_itype(.001);local=placed.trans.inverted()*point;found=hit(pl,local)
                passed=len(found)==1 and found[0]in own
                candidates.append(dict(layer=pl,chip_um=[x,y],local_um=[local.x*.001,local.y*.001],same_native_net=passed))
                if not passed:errors.append(dict(instance=instance,pin=pin,candidate=candidates[-1]))
            planes=[]
            for pl in (30,50,67,126,134):
                polygons=[poly for node,poly in components.items()if node in own and graph.nodes[node]['layer']==pl]
                largest=[]
                for poly in sorted(polygons,key=lambda q:q.area(),reverse=True)[:15]:
                    transformed=poly.transformed(placed.trans);box=transformed.bbox()
                    largest.append(dict(area_um2=poly.area()*1e-6,bbox_chip_um=[v*.001 for v in (box.left,box.bottom,box.right,box.top)]))
                planes.append(dict(layer=pl,polygons=len(polygons),total_area_um2=sum(q.area()for q in polygons)*1e-6,
                                   largest15_bbox_previews_not_landing_proof=largest))
            ownedcuts=[cuts[n]for n in own if n in cuts]
            rows.append(dict(instance=instance,pin=pin,net=terminal['net'],cell=cell.name,transform=str(placed.trans),
                             source_native_metal_components=len([n for n in own if n in components]),
                             native_via_shapes=len(ownedcuts),source_pin_probe_passed=True,
                             candidates=candidates,planes=planes,current_capacity='not run; native cut shapes may be noncanonical bars'))
        assert all(not (left&right)for i,left in enumerate(owners.values())for right in list(owners.values())[i+1:]),instance
        (a.output/'analysis.json').write_text(json.dumps(dict(status='running native ownership',rows=rows,errors=errors),indent=2)+'\n')
        print(json.dumps(dict(phase='native ownership complete',instance=instance,metal_components=len(components),cut_shapes=len(cuts))),flush=True)
    assert len(rows)==13
    result=dict(status='passed candidate native egress ownership'if not errors else'failed candidate native egress ownership',
                GDS_sha256=sha(source),inventory_sha256=sha(a.inventory),script_sha256=sha(Path(__file__)),
                BGR_source_GDS_sha256=meta['BGR_source_GDS_sha256'],rows=rows,errors=errors,geometry_mutated=False,
                scope='Actual connected metal/via components, no text-based joins. Point ownership alone does not establish array footprint, current distribution or legal route.',
                not_run=['actual root PDN landing clearance','full-footprint landing validation','remaining feed construction',
                         'internal source-terminal current partition','full PVT/IR/current sharing/EM','stock checks for new feeds','adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        output=Path(sys.argv[sys.argv.index('--output')+1])
        if output.exists():
            receipt=output/'analysis.json'
            data=json.loads(receipt.read_text())if receipt.exists()else{}
            data.update(status='failed native ownership audit',error=repr(exc),script_sha256=sha(Path(__file__)))
            receipt.write_text(json.dumps(data,indent=2)+'\n')
        raise
