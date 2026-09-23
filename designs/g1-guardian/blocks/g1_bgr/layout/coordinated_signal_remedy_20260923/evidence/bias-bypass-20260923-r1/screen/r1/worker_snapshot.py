#!/usr/bin/env python3
"""Isolated additive bias-route screen; no candidate GDS or source edits."""
import argparse
import datetime
import json
import os
from pathlib import Path
import sys
import time
import pya

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'coordinated_full_closure'))
from build_assembly import PAIRS, CUTS, region, sha, dump


def ledger():
    rows = []
    def rect(layer, net, box, role):
        rows.append(dict(layer=layer, net=net, bbox_dbu=box, role=role))
    # Existing MOS M4 columns and eastern route columns; all pin markers held.
    for net, left, right, port_y, y in (
        ('pbias',281210,411740,138600,156000),
        ('pcasc',282210,412490,139200,159000),
        ('vb2',285210,414740,141000,162000)):
        rect('M5',net,[left-360,y-1000,right+150,y+1000],'bias_parallel_bypass')
        for x, half, cuts in ((left,360,(-210,210)),(right,150,(0,))):
            rect('M4',net,[x-half,port_y-150,x+half,y+780],'same_net_riser')
            for layer in ('M4','M5'):
                rect(layer,net,[x-half,y-780,x+half,y+780],'Via4_landing')
            for dx in cuts:
                for dy in (-630,-210,210,630):
                    rect('Via4',net,[x+dx-95,y+dy-95,x+dx+95,y+dy+95],'redundant_Via4')
    return rows


def main():
    ap = argparse.ArgumentParser()
    for name in ('gds','output','resource-gate'):
        ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args()
    gate=json.loads(a.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800
    assert set(os.sched_getaffinity(0))=={1}
    assert sha(a.gds)=='6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04'
    a.output.mkdir(exist_ok=False)
    start=time.monotonic()
    (a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    try:
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
        base={k:region(top,ly.layer(*v)) for k,v in PAIRS.items()}
        rows=ledger();added={k:pya.Region() for k in PAIRS}
        for r in rows:added[r['layer']].insert(pya.Box(*r['bbox_dbu']))
        checks=[]
        for r in rows:
            own=ltn.shapes_of_net(nets[r['net']],layers[r['layer']],True)
            other=base[r['layer']]-own
            shape=pya.Region(pya.Box(*r['bbox_dbu']))
            distance=220 if r['layer'] in CUTS else 250
            conflict=shape.sized(distance)&other
            enclose=True
            if r['layer'] in CUTS:
                enclose=all((shape.sized(55)-(base[k]+added[k])).is_empty() for k in CUTS[r['layer']])
            checks.append(dict(r,passed=conflict.is_empty() and enclose,
                foreign_clearance_nm=distance,via_enclosure=enclose,
                conflict_bboxes_dbu=[[p.bbox().left,p.bbox().bottom,p.bbox().right,p.bbox().top] for p in conflict.each()]))
        mutual=[]
        for i,left in enumerate(rows):
            for right in rows[i+1:]:
                if left['net']==right['net'] or left['layer']!=right['layer']:continue
                distance=220 if left['layer'] in CUTS else 250
                hit=pya.Region(pya.Box(*left['bbox_dbu'])).sized(distance)&pya.Region(pya.Box(*right['bbox_dbu']))
                if not hit.is_empty():mutual.append(dict(left=left,right=right))
        result=dict(status='passed geometric screen' if all(r['passed'] for r in checks) and not mutual else 'failed geometric screen',
            inputs={str(p):sha(p) for p in (a.gds,route,Path(__file__),a.resource_gate)},
            ledger=rows,checks=checks,mutual_foreign_clearance=mutual,
            unchanged_native='passed; read-only input',new_geometry='not run',
            all_overlay_attachment_and_cross_layer_contact_graph='not run',
            stock_DRC_LVS='not run',metal_network_and_OP='not run',adoption='not run')
        dump(a.output/'analysis.json',result)
        print(json.dumps(dict(status=result['status'],failed_shapes=[r for r in checks if not r['passed']],mutual=len(mutual)),indent=2))
    except Exception as e:
        dump(a.output/'failure.json',dict(status='failed',error=repr(e)))
        raise
    finally:
        dump(a.output/'timing.json',dict(wall_s=time.monotonic()-start))


if __name__=='__main__':main()
