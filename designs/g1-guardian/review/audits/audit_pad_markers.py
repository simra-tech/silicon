#!/usr/bin/env python3
"""Read retained pad/antenna markers and locate them on the delivered GDS."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import pya

ROOT = Path(__file__).resolve().parents[4]
BLOCK = ROOT/'designs/g1-guardian/blocks/g1_padring'
GDS = BLOCK/'layout/g1_chip_top.gds'
REPORTS = BLOCK/'reports/assembly-1350'
PDK = Path('/foss/pdks/ihp-sg13g2')
DECKS = PDK/'libs.tech/klayout/tech/drc/rule_decks'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def items(path):
    records=[]
    for item in ET.parse(path).findall('.//items/item'):
        vals = [v.text for v in item.findall('./values/value')]
        poly = next(v for v in vals if v.startswith('polygon:'))
        points = [list(map(float,s.split(','))) for s in re.search(r'\((.*)\)',poly)[1].split(';')]
        attributes={}
        for v in vals:
            m=re.match(r'\[#([^]]+)\] float: (.*)',v)
            if m: attributes[m[1]]=float(m[2])
        records.append({'rule':item.findtext('category').strip("'"),'polygon_um':points,'attributes':attributes})
    return records


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    ly=pya.Layout();ly.read(str(GDS));top=ly.cell('g1_chip_top')
    cell=ly.cell('sg13g2_IOPadIn')
    # Poly/contact/metal connectivity only: no diffusion or transistor channel connection.
    l2n=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,cell,[]));layers={}
    sequence=[('poly',5),('cont',6),('m1',8),('v1',19),('m2',10),('v2',29),('m3',30),('v3',49),('m4',50),('v4',66),('m5',67),('tv1',125),('tm1',126),('tv2',133),('tm2',134)]
    for name,gl in sequence:
        layers[name]=l2n.make_layer(ly.layer(gl,0),name);l2n.connect(layers[name])
        if name in ('m1','m2','m3','m4','m5','tm1','tm2'):
            labels=l2n.make_text_layer(ly.layer(gl,25),name+'_txt');l2n.connect(layers[name],labels)
    for a,b in zip(list(layers),list(layers)[1:]):l2n.connect(layers[a],layers[b])
    l2n.extract_netlist()
    net=l2n.probe_net(layers['poly'],pya.Point(round(41.76/ly.dbu),round(164.0/ly.dbu)))
    assert net is not None and net.name=='vdd'
    antenna=items(REPORTS/'antenna.klayout.lyrdb')
    ios=[i for i in top.each_inst() if i.cell.name=='sg13g2_IOPadIn']
    for item in antenna:
        points=item['polygon_um'];center=pya.DPoint(sum(p[0] for p in points)/len(points),sum(p[1] for p in points)/len(points))
        matches=[i for i in ios if i.dbbox().contains(center)]
        assert len(matches)==1
        inst=matches[0];local=inst.dcplx_trans.inverted()*center
        probed=l2n.probe_net(layers['poly'],pya.Point(round(local.x/ly.dbu),round(local.y/ly.dbu)))
        assert probed is not None and probed.name=='vdd'
        item['iopadin_transform']=str(inst.dcplx_trans)
        item['local_gate_center_um']=[local.x,local.y]
        item['traced_net']=probed.name
    pads=items(REPORTS/'drc_recommended/drc_recommended.lyrdb')
    metal={l:pya.Region(top.begin_shapes_rec(ly.layer(l,0))).merged() for l in (126,134)}
    counts=collections.Counter()
    for item in pads:
        layer=126 if item['rule'].endswith('TM1') else 134
        polygon=pya.DPolygon([pya.DPoint(*p) for p in item['polygon_um']]).to_itype(ly.dbu)
        region=pya.Region(polygon)
        bbox=polygon.bbox().to_dtype(ly.dbu)
        item['bbox_um']=[bbox.left,bbox.bottom,bbox.right,bbox.top]
        item['area_um2']=region.area()*ly.dbu**2
        item['existing_same_layer_overlap_um2']=(region&metal[layer]).area()*ly.dbu**2
        item['marker_touches_existing_same_layer_metal']=not region.interacting(metal[layer]).is_empty()
        item['candidate_action']='Extend same-net pad exit into marker polygon; design modification and DRC/connectivity checks not run.'
        counts[(item['rule'],round(bbox.width(),4),round(bbox.height(),4))]+=1
    rules=json.loads((DECKS/'sg13g2_tech_default.json').read_text())
    result={'command':'flow/run.sh python3 designs/g1-guardian/review/audits/audit_pad_markers.py --output '+str(args.output),
            'gds_sha256':sha(GDS),'klayout_version':pya.__version__,'pdk_commit':(PDK/'COMMIT').read_text().strip(),
            'script_sha256':sha(Path(__file__)),
            'retained_reports':{str(p.relative_to(ROOT)):sha(p) for p in [REPORTS/'antenna.klayout.lyrdb',REPORTS/'drc_recommended/drc_recommended.lyrdb']},
            'deck_sha256':{str(p.relative_to(PDK)):sha(p) for p in [DECKS/'antenna.drc',DECKS/'beol/6_9_pad.drc',DECKS/'sg13g2_tech_default.json']},
            'antenna_items':antenna,'pad_items':pads,
            'pad_marker_shapes':[{'rule':k[0],'width_um':k[1],'height_um':k[2],'count':v} for k,v in sorted(counts.items())],
            'not_run':['New antenna or recommended-pad DRC','Pad exit geometry modification','Antenna geometry modification','Full-chip supply-device connectivity and process qualification'],
            'limitations':['Antenna gate trace is cell-local poly/contact/metal connectivity with labels, not full IO transistor LVS.',
                           'Retained marker locations are audited; original decks not altered or waived.',
                           'Candidate exit-extension polygons require same-net connectivity and full DRC checks before adoption.']}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'antenna_markers':len(antenna),'traced_net':net.name,'pad_markers':len(pads),'pad_shapes':result['pad_marker_shapes']},indent=2))


if __name__=='__main__':main()
