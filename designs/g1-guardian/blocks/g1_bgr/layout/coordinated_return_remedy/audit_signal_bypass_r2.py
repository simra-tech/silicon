#!/usr/bin/env python3
"""R2 signal preflight: VBE east dogleg and narrower c2 escape resolve retained conflicts."""
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
    for net,left,tap,y,middle,right,port,top in [
        ('vbe',204250,137800,150000,286000,415700,141600,342430),
        ('c2',202050,136600,153000,271000,404450,132600,339230)]:
        half=300 if net=='c2' else 400
        rect('M5',net,[left-half,tap,left+half,y+1000],'HBT_same_column_extension')
        if net=='vbe':
            original_right=right
            right=414500
            rect('M4',net,[right-140,port-140,original_right+140,port+140],'east_VBE_dogleg_below_supply_landings')
        rect('M5',net,[left-400,y-1000,right+150,y+1000],'current_signal_bypass')
        rect('M4',net,[middle-360,port-150,middle+360,top],'MOS_same_column_widening')
        rect('M4',net,[right-140,port,right+140,y+780],'east_same_port_riser')
        for metal in ('M4','M5'):
            rect(metal,net,[middle-360,y-780,middle+360,y+780],'MOS_eight_Via4_landing')
            rect(metal,net,[right-150,y-780,right+150,y+780],'east_four_Via4_landing')
        for dx in (-210,210):
            for dy in (-630,-210,210,630):
                rect('Via4',net,[middle+dx-95,y+dy-95,middle+dx+95,y+dy+95],'MOS_eight_Via4')
        for dy in (-630,-210,210,630):
            rect('Via4',net,[right-95,y+dy-95,right+95,y+dy+95],'east_four_Via4')
    return rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--gds',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert sha(a.gds)=='e9b6653d74ae841beb831bebdbbc9942cdfba064e13d4d00c49751b83a77111c'
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
    mutual=[]
    for left in rows:
        for right in rows:
            if left['net']==right['net'] or left['layer']!=right['layer']:continue
            clearance=220 if left['layer'] in CUTS else 250
            conflict=pya.Region(pya.Box(*left['bbox_dbu'])).sized(clearance)&pya.Region(pya.Box(*right['bbox_dbu']))
            if not conflict.is_empty():mutual.append(dict(left=left,right=right,area_um2=conflict.area()*1e-6))
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
    result=dict(status='passed preflight' if all(c['passed'] for c in checks) and not mutual else 'failed preflight',
        inputs={str(p):sha(p) for p in (a.gds,route,Path(__file__))},ledger=rows,checks=checks,mutual_added_net_clearance_findings=mutual,
        layer_domain=['M2','M3','M4','M5','Via3','Via4'],TopMetal1_TopMetal2='not applicable; unchanged absent',
        proposed_nine_pin_markers='unchanged',native_devices='unchanged',
        analytical_path_estimates=[
            dict(net=net,nominal_current_A=current,
                prior_dominant_M4_crossing_ohm=old,
                new_HBT_column_extension_plus_M5_to_MOS_plus8Via4_ohm=(dy/width+dx/2)*.088+9/8,
                scope='Optimistic KPEX-table path only; excludes junction spreading/access and remaining routes; not a full network result')
            for net,dy,dx,width,old,current in [('vbe',12.2,81.75,.8,61.98133333333334,9.921922876e-5),
                                              ('c2',16.4,68.95,.6,59.32666666666666,9.921826987e-5)]],
        actual_candidate_seven_star_graph='not run',stock_DRC_LVS_AP='not run',electrical_field_IR_qualification='not run')
    dump(a.output,result)
    print(json.dumps(dict(status=result['status'],shapes=len(rows),failures=[r for r in checks if not r['passed']]),indent=2))


if __name__=='__main__':main()



