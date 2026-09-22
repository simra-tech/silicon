#!/usr/bin/env python3
"""Independent delivered gate/diffusion-to-metal net partition, no label-based merging."""
import argparse,hashlib,json,os
from pathlib import Path
import pya

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--gds',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    inv=json.loads(a.inventory.read_text());assert sha(a.gds)==inv['delivered_sha256']
    ly=pya.Layout();ly.read(str(a.gds));old=ly.cell('g1_ota')
    flat=pya.Layout();flat.dbu=.001;top=flat.create_cell('audit_ota')
    # Materialized polygon copies make this snapshot independent of all later mutation.
    regions={}
    for layer in (1,5,6,8,10,19,29,30,49,50,66,67,125,126):
        reg=pya.Region()
        for poly in pya.Region(old.begin_shapes_rec(ly.layer(layer,0))).each():reg.insert(pya.Polygon(poly))
        regions[layer]=reg.merged()
    regions[501]=regions[1]-regions[5]
    for layer,reg in regions.items():
        if layer==1:continue
        for poly in reg.each():top.shapes(flat.layer(layer,0)).insert(poly)
    net=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,top,[]));layers={}
    for layer in (5,501,8,10,30,50,67,126):
        layers[layer]=net.make_layer(flat.layer(layer,0),'L'+str(layer));net.connect(layers[layer])
    for layer,joins in {6:(5,501,8),19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126)}.items():
        cut=net.make_layer(flat.layer(layer,0),'V'+str(layer));net.connect(cut)
        for target in joins:net.connect(cut,layers[target])
    net.extract_netlist();probes=[]
    def probe(device,terminal,expected,layer,x,y):
        found=net.probe_net(layers[layer],pya.Point(round(x*1000),round(y*1000)))
        probes.append(dict(device=device,terminal=terminal,expected_net=expected,layer=layer,point_um=[x,y],
                           actual_net=None if found is None else found.cluster_id))
    seen=set()
    for row in inv['devices']:
        name=row['device'];words=row['source_comparisons']['g1_ota']['source']['line'].split();drain,gate,source,bulk=words[1:5]
        strips=row['physical']['diffusion_strips'];is_pair=row['native_group']=='PAIR'
        pattern='ABBAABBAABBAABBA'
        for f in range(len(strips)-1):
            if is_pair and (pattern[f//2]=='A')!=(name=='XM1'):continue
            left=strips[f]['bbox_um'];right=strips[f+1]['bbox_um']
            probe(name,'gate',gate,5,(left[2]+right[0])/2,(left[1]+left[3])/2)
        for k,strip in enumerate(strips):
            if is_pair and k%2 and (pattern[k//2]=='A')!=(name=='XM1'):continue
            if is_pair and k%2==0 and ('pair',k) in seen:continue
            if is_pair and k%2==0:seen.add(('pair',k))
            b=strip['bbox_um'];probe(name,'source' if k%2==0 else 'drain',source if k%2==0 else drain,501,(b[0]+b[2])/2,(b[1]+b[3])/2)
    # Physical labels are only independent probe locations; never extraction connectivity.
    labels=[]
    for metal in (8,10,30,50,67,126):
        it=old.begin_shapes_rec(ly.layer(metal,25))
        while not it.at_end():
            shape=it.shape()
            if shape.is_text():
                text=shape.text;pt=it.trans()*text.trans.disp
                labels.append(text.string);probe('pin','label_anchor',text.string,metal,pt.x*.001,pt.y*.001)
            it.next()
    expected={};actual={}
    for q in probes:
        expected.setdefault(q['expected_net'],set()).add(q['actual_net'])
        actual.setdefault(q['actual_net'],set()).add(q['expected_net'])
    opens={k:sorted(v,key=str) for k,v in expected.items() if None in v or len(v)!=1}
    shorts={str(k):sorted(v) for k,v in actual.items() if len(v)>1}
    result={'status':'passed' if not opens and not shorts else 'failed','source_sha256':inv['source_sha256'],'GDS_sha256':sha(a.gds),
            'inventory_sha256':sha(a.inventory),'script_sha256':sha(Path(__file__)),'probes':probes,'probe_count':len(probes),
            'opens':opens,'shorts':shorts,'expected_to_actual':{k:sorted(v,key=str) for k,v in expected.items()},'label_anchors':labels,
            'scope':'Actual gate and channel-subtracted diffusion polygons connected through contacts and six metal levels. No labels used for merging; labels only sampled as independent terminal anchors. PAIR source strips counted once. Confirms gate/source/drain mapping, not finger/default junction equivalence or well/substrate isolation.',
            'GDS_saved':False,'not_run':['bulk well/substrate isolation','new routed candidate','stock LVS/DRC for new geometry']}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='probes'},indent=2))
if __name__=='__main__':main()
