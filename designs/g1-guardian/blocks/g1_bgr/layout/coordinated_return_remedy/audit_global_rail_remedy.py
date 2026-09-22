#!/usr/bin/env python3
"""Read-only geometric context for remaining same-domain supply bottlenecks."""
import argparse
import json
import os
from pathlib import Path
import sys
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'coordinated_full_closure'))
from build_assembly import PAIRS,CUTS,region,sha,dump


def ledger():
    rows=[]
    def rect(layer,net,bbox,role):rows.append(dict(layer=layer,net=net,bbox_dbu=bbox,role=role))
    rect('M3','vss',[18000,5460,417950,15460],'wider_general_collector')
    rect('M3','vss',[18000,15860,403000,17060],'precision_rail_upper_only')
    for x,y0,y1,name in [(1200,15860,345710,'XQ56'),(2600,14660,256830,'XQ60'),
                         (4000,13460,334600,'XQ67'),(5400,12260,346910,'XQ62')]:
        rect('M2','vss',[x-550,y0,x+550,y1],'return_'+name+'_same_column')
    for y in (15060,143400):
        for metal in ('M3','M4','M5'):
            rect(metal,'vss',[415070,y-150,418310,y+150],'east_VSS_eight_cut_landing')
        for cut in ('Via3','Via4'):
            for i in range(1,7):
                x=417740-420*i
                rect(cut,'vss',[x-95,y-95,x+95,y+95],'east_VSS_six_added_cuts')
    # New route remains entirely M3/M4/M5, below the coordinator's TM1/TM2.
    rect('M5','vdd',[286640,145000,419360,147000],'VDD_parallel_bridge')
    rect('M4','vdd',[418640,142200,419360,146840],'VDD_east_riser')
    for metal in ('M3','M4'):
        rect(metal,'vdd',[415900,142050,419140,142350],'VDD_east_eight_Via3_landing')
    for i in range(8):
        x=416050+420*i
        rect('Via3','vdd',[x-95,142105,x+95,142295],'VDD_east_eight_Via3')
    for x in (287000,419000):
        for metal in ('M4','M5'):
            rect(metal,'vdd',[x-360,145160,x+360,146840],'VDD_eight_Via4_landing')
        for dx in (-210,210):
            for dy in (-630,-210,210,630):
                rect('Via4','vdd',[x+dx-95,146000+dy-95,x+dx+95,146000+dy+95],'VDD_eight_Via4')
    return rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--gds',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert sha(a.gds)=='4b5a92c08ba56d44d558f962c48330b6edcb89f8fcc53e54e2108da0cb8b239f'
    ly=pya.Layout();ly.read(str(a.gds));top=ly.top_cell()
    ltn=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,top,[]))
    layers={k:ltn.make_layer(ly.layer(*v),k) for k,v in PAIRS.items()}
    for k in PAIRS:ltn.connect(layers[k])
    for cut,ends in CUTS.items():
        for end in ends:ltn.connect(layers[cut],layers[end])
    ltn.extract_netlist()
    route=Path(os.environ['G1_RESULTS_ROOT'])/'bgr-assembly-20260922-r5/routing.json'
    nets={}
    for p in json.loads(route.read_text())['source_probes']:
        node=ltn.probe_net(layers[p['layer']],pya.Point(*p['point']))
        assert node is not None
        if p['net'] in nets:assert nets[p['net']].cluster_id==node.cluster_id
        nets[p['net']]=node
    assert len(nets)==55
    additions={k:pya.Region() for k in PAIRS};rows=ledger()
    base={k:region(top,ly.layer(*pair)) for k,pair in PAIRS.items()}
    for r in rows:additions[r['layer']].insert(pya.Box(*r['bbox_dbu']))
    checks=[]
    for r in rows:
        own=ltn.shapes_of_net(nets[r['net']],layers[r['layer']],True)
        other=base[r['layer']]-own
        proposed=pya.Region(pya.Box(*r['bbox_dbu']))
        clearance=220 if r['layer'] in CUTS else 250
        conflict=proposed.sized(clearance)&other
        enclosed=True
        if r['layer'] in CUTS:
            enclosed=all((proposed.sized(55)-(base[m]+additions[m])).is_empty() for m in CUTS[r['layer']])
        checks.append(dict(r,clearance_nm=clearance,crossnet_clearance_area_um2=conflict.area()*1e-6,
            conflict_bboxes_dbu=[[p.bbox().left,p.bbox().bottom,p.bbox().right,p.bbox().top] for p in conflict.each()],
            via_enclosure=enclosed,passed=conflict.is_empty() and enclosed))
    result=dict(status='passed preflight' if all(c['passed'] for c in checks) else 'failed preflight',
        inputs={str(p):sha(p) for p in (a.gds,route,Path(__file__))},ledger=rows,checks=checks,
        layer_domain=['M2','M3','M4','M5','Via3','Via4'],TopMetal1_TopMetal2='not applicable; unchanged absent',
        proposed_nine_pin_markers='unchanged',native_devices='unchanged',
        actual_candidate_seven_star_graph='not run',stock_DRC_LVS_AP='not run',electrical_field_IR_qualification='not run')
    dump(a.output,result)
    print(json.dumps(dict(status=result['status'],shapes=len(rows),failures=[r for r in checks if not r['passed']]),indent=2))


if __name__=='__main__':main()
