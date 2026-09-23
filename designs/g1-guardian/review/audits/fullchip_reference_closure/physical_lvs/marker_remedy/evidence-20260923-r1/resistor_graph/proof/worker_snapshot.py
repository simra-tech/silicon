#!/usr/bin/env python3
"""Independent unsimplified physical head/metal graph for source resistor chain."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import pya


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and set(os.sched_getaffinity(0))=={1}
    a.output.mkdir(parents=True);(a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    prep=json.loads((a.candidate/'summary.json').read_text())
    results=[]
    for info in prep['cells']:
        gds,cdl=Path(info['gds']),Path(info['reference'])
        assert sha(gds)==info['GDS_sha256'] and sha(cdl)==info['CDL_sha256']
        ly=pya.Layout();ly.read(str(gds));top=ly.top_cell()
        reg=lambda layer:pya.Region(top.begin_shapes_rec(ly.layer(layer,0))).merged()
        body=reg(128);poly=reg(5)-body
        raw={'heads':poly,'cont':reg(6)}
        seq=[8,19,10,29,30,49,50,66,67,125,126,133,134]
        raw.update({str(n):reg(n) for n in seq})
        flat=pya.Layout();flat.dbu=.001;c=flat.create_cell('resistor_head_graph')
        for i,(name,r) in enumerate(raw.items()):c.shapes(flat.layer(i+1,0)).insert(r)
        graph=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,c,[]))
        layers={name:graph.make_layer(flat.layer(i+1,0),name) for i,name in enumerate(raw)}
        for layer in layers.values():graph.connect(layer)
        graph.connect(layers['heads'],layers['cont']);graph.connect(layers['cont'],layers['8'])
        for x,y in zip(seq,seq[1:]):graph.connect(layers[str(x)],layers[str(y)])
        graph.extract_netlist()
        edges=[]
        for poly in sorted(body.each(),key=lambda p:p.bbox().left):
            b=poly.bbox();points=[pya.Point(b.center().x,b.bottom-200),pya.Point(b.center().x,b.top+200)]
            nodes=[]
            for p in points:
                n=graph.probe_net(layers['heads'],p);assert n is not None
                nodes.append(n.cluster_id)
            assert nodes[0]!=nodes[1], 'Real conductor shorts a marked resistor'
            edges.append(dict(body_box_dbu=str(b),w_um=b.width()*.001,l_um=b.height()*.001,
                              nodes=nodes,head_points_dbu=[[p.x,p.y] for p in points]))
        degree=Counter(n for e in edges for n in e['nodes'])
        expected=info['marker_count']
        assert len(edges)==expected and len(degree)==expected+1
        assert Counter(degree.values())==Counter({1:2,2:expected-1}) if expected>1 else Counter(degree.values())==Counter({1:2})
        adjacency={n:set() for n in degree}
        for e in edges:
            x,y=e['nodes'];adjacency[x].add(y);adjacency[y].add(x)
        reached=set();todo=[edges[0]['nodes'][0]]
        while todo:
            n=todo.pop()
            if n not in reached:reached.add(n);todo.extend(adjacency[n]-reached)
        assert reached==set(degree)
        source_edges=[]
        for line in cdl.read_text().splitlines():
            if line.startswith('RR') and '$[rppd]' in line:
                t=line.split();source_edges.append(dict(name=t[0],nodes=t[1:3],record=line))
        assert len(source_edges)==expected
        if info['kind']=='rc':
            sd=Counter(n.lower() for e in source_edges for n in e['nodes'])
            assert len(sd)==27 and sd['pin1']==sd['pin2']==1 and all(v==2 for k,v in sd.items() if k not in ('pin1','pin2'))
            pins={}
            for name,x,y in [('pin1',500,150),('pin2',41750,150)]:
                n=graph.probe_net(layers['8'],pya.Point(x,y));assert n is not None and degree[n.cluster_id]==1
                pins[name]=n.cluster_id
            assert pins['pin1']!=pins['pin2']
        else:pins={}
        results.append(dict(cell=info['kind'],GDS_sha256=sha(gds),CDL_sha256=sha(cdl),
                            physical_edges=edges,source_edges=source_edges,
                            physical_node_degrees={str(k):v for k,v in degree.items()},pin_bindings=pins,
                            connected_simple_series_path=True,source_record_count=expected,
                            substrate_model_contract='not qualified by metal/head graph'))
    result=dict(status='passed independent unsimplified source/body/metal series graph',cells=results,
                script_sha256=sha(Path(__file__)),new_extraction='not run',electrical_current='not run')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])


if __name__=='__main__':main()
