#!/usr/bin/env python3
"""Independent physical conductor probes, with no same-name/virtual connections."""
import argparse,hashlib,json
from pathlib import Path
import pya
p=argparse.ArgumentParser();p.add_argument('gds');p.add_argument('output');a=p.parse_args()
ly=pya.Layout();ly.read(a.gds);top=ly.cell('g1_chip_top')
l2n=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,top,[]))
metals=[('M1',8),('M2',10),('M3',30),('M4',50),('M5',67),('TM1',126),('TM2',134)];L={}
for name,gl in metals:
    L[name]=l2n.make_layer(ly.layer(gl,0),name);l2n.connect(L[name])
for name,gl,i,j in [('V1',19,0,1),('V2',29,1,2),('V3',49,2,3),('V4',66,3,4),('TV1',125,4,5),('TV2',133,5,6)]:
    v=l2n.make_layer(ly.layer(gl,0),name);l2n.connect(v);l2n.connect(L[metals[i][0]],v);l2n.connect(L[metals[j][0]],v)
l2n.extract_netlist()
points=[('bondpad_old_center','TM2',1244,395),('bondpad_new_center','TM2',1248,395),('pad_feed','M3',1029.1,389),('feed_strap','M5',980,389.34),('bgr_supply','TM1',719.22,984.65),('sense_supply','TM1',946.02,624.75),('t2f_supply','TM1',568.02,984.15),('trip_supply','TM1',946.02,850.75),('gate_supply','TM1',946.02,909.65),('ls_supply','M2',568.02,871.4)]
points += [('reported_pad_stub',layer,1207.5,395) for layer in ['M2','M3','M4','M5','TM1','TM2']]
rows=[]
for name,layer,x,y in points:
    net=l2n.probe_net(L[layer],pya.Point(round(x/ly.dbu),round(y/ly.dbu)))
    rows.append(dict(name=name,layer=layer,point_um=[x,y],net=None if net is None else dict(circuit=net.circuit().name,cluster_id=net.cluster_id,qname=net.qname())))
ids={(r['net']['circuit'],r['net']['cluster_id']) for r in rows if r['net']}
result=dict(input=a.gds,sha256=hashlib.sha256(Path(a.gds).read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),klayout=pya.__version__,scope='Metal1 through TopMetal2 with six physical via layers; no labels, devices, virtual/global connections, or same-name merging. Probes do not prove every transistor terminal.',probes=rows,all_probes_same_physical_cluster=all(r['net'] for r in rows) and len(ids)==1)
Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
