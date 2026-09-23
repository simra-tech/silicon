#!/usr/bin/env python3
"""Bind every declared external DEF port rectangle to actual native pad metal."""
import argparse
import collections
import json
import os
from pathlib import Path
import re
import pya
from audit_native_terminal_connectivity import LAYERS
from audit_placed_decap_domains import physical,identity
from place_closed_analog import region,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('candidate','prepared','observations','output'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--flat-physical',action='store_true')
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    source=a.candidate/'signal_routed_native.gds';m=json.loads((a.candidate/'analysis.json').read_text())
    obs=json.loads(a.observations.read_text());prepared=json.loads((a.prepared/'analysis.json').read_text())
    deffile=a.prepared/'g1_chip_top_unrouted.def'
    assert m['status'].startswith('passed') and sha(source)==m['GDS_sha256']==obs['GDS_sha256']
    assert sha(deffile)==prepared['DEF_sha256']
    block,=re.findall(r'^PINS 22 ;\n(.*?)^END PINS$',deffile.read_text(),re.M|re.S)
    records=re.findall(r'^\s*-\s+(\S+)\s+\+ NET (\S+)(.*?);',block,re.M|re.S)
    assert len(records)==22 and len({x[0]for x in records})==22
    declared={(x['net'],x['pin'])for x in obs['external_BTerms_not_probed']}
    assert declared=={(net,name)for name,net,body in records}
    # These identities belong to one prior extraction and cannot be compared
    # numerically to a fresh extraction. Re-probe recorded real ITerm points.
    iterms=collections.defaultdict(list)
    for row in obs['observations']:
        if row['instance'].startswith('IO_BOND_'):
            assert row['pin']=='pad'
            iterms[row['net']].append(row)
    assert sum(map(len,iterms.values()))==24
    ly=pya.Layout();ly.read(str(source));top=ly.top_cell()
    if a.flat_physical:
        from flat_metal_connectivity import flat_physical
        netlist,metal,flat_layout_held=flat_physical(ly,top)
    else:
        netlist,metal=physical(ly,top)
    actual={layer:region(ly,top,pya.LayerInfo(layer,0))for layer in set(LAYERS.values())}
    ports=[];errors=[]
    for name,logical,body in records:
        assert '+ PORT' in body and not re.search(r'\b(?:POLYGON|VIA)\b',body)
        matching=set()
        for iterm in iterms[logical]:
            for window in iterm['windows']:
                layer=window['layer']
                if layer not in metal:continue
                for polygon in (actual[layer]&pya.Region(pya.Box(*window['bbox']))).each():
                    v=next(polygon.each_point_hull());key=identity(netlist,metal[layer],[v.x,v.y])
                    if key is not None:matching.add(key)
        chunks=body.split('+ PORT')[1:]
        for index,chunk in enumerate(chunks):
            rects=re.findall(r'\+ LAYER (\S+) \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \)',chunk)
            fixed=re.findall(r'\+ FIXED \( (-?\d+) (-?\d+) \) (\S+)',chunk)
            assert len(rects)==len(fixed)==1 and fixed[0][2]=='N'
            layername,x1,y1,x2,y2=rects[0];layer=LAYERS[layername]
            x,y=map(int,fixed[0][:2]);box=pya.Box(int(x1)+x,int(y1)+y,int(x2)+x,int(y2)+y)
            assert layer in metal and box.area()>0
            overlap=actual[layer]&pya.Region(box);missing=pya.Region(box)-actual[layer]
            parts=set()
            for polygon in overlap.each():
                v=next(polygon.each_point_hull());key=identity(netlist,metal[layer],[v.x,v.y])
                if key is not None:parts.add(key)
            passed=missing.is_empty() and len(parts)==1 and parts<=matching
            row=dict(pin=name,net=logical,port=index,layer=layer,bbox_dbu=[box.left,box.bottom,box.right,box.top],
                     declared_area_um2=box.area()*1e-6,uncovered_area_um2=missing.area()*1e-6,
                     actual_components=[list(v)for v in sorted(parts)],same_net_ITerm_components=[list(v)for v in sorted(matching)],
                     status='passed'if passed else'failed')
            ports.append(row)
            if not passed:errors.append(row)
    assert len(ports)==24
    result=dict(status='passed all external BTerm metal bindings'if not errors else'failed external BTerm metal binding',
        GDS_sha256=sha(source),DEF_sha256=sha(deffile),observations_sha256=sha(a.observations),script_sha256=sha(Path(__file__)),
        logical_BTerms=22,physical_ports=24,ports=ports,errors=errors,
        extraction_scope='flat instance-resolved geometry'if a.flat_physical else'hierarchical geometry',
        flat_helper_sha256=sha(Path(__file__).with_name('flat_metal_connectivity.py'))if a.flat_physical else None,
        scope='Exact entire port rectangle coverage and connection to its same-logical-net native bondpad ITerm; no label joining',
        not_run=['all supply terminals joined','device-aware fullchip LVS','currentIR/EM','bonding or measured continuity'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if not errors else 1)


if __name__=='__main__':main()
