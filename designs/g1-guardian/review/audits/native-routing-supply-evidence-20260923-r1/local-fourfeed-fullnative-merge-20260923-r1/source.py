#!/usr/bin/env python3
"""Merge source-bound local feeds; keep unfinished VDDA branches unpowered."""
import argparse
import collections
import faulthandler
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region, text_records, sha
from audit_placed_decap_domains import physical, identity
from build_native_decap_pdn import METALS, CUTS, point

BASE='4e9f6248652e15b43ff250337e33f9813fdc9761dd3bf3f3b6e3789fc20ea5cc'
PDN='88e5911aeaa4f0ae9c3c4712f4f2430563affa32bae0fe6c6c48c142e9611bdb'
POINTS={'bgr_vdda':(67,[743400,878000]),'bgr_vss':(67,[749650,873000]),
        'osc_vdd':(30,[772000,1089570]),'osc_vss':(30,[774000,954000]),
        'core_vdd':(134,[395000,354660]),'core_vss':(134,[507000,334660]),
        'sense_vdda':(134,[813000,714000]),'sense_vss':(126,[805000,714000]),
        'pad07_external':(134,[1271500,395000])}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('native','bgr','osc','bgr-drc','osc-drc','placement','output'):
        p.add_argument('--'+key,type=Path,required=True)
    for key in ('t2f','gate','t2f-drc','gate-drc'):
        p.add_argument('--'+key,type=Path)
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    faulthandler.dump_traceback_later(60,repeat=True)
    source=a.native/'power_connected_native.gds';meta=json.loads((a.native/'analysis.json').read_text())
    assert meta['status'].startswith('passed') and sha(source)==meta['GDS_sha256']==BASE
    assert meta['native_instances_retained']==4904 and meta['decap_pin_pairs_held']==9324
    overlays=[];bindings=[];points=dict(POINTS)
    cases=[('bgr',a.bgr,a.bgr_drc),('osc',a.osc,a.osc_drc)]
    extra_points={'t2f':{'vdd':(30,[1044000,1047600]),'vss':(30,[1039200,954300]),'vdda':(30,[1044000,1054300])},
                  'gate':{'vdd':(30,[767320,546000]),'vss':(30,[778650,600000]),'vdda':(30,[734000,600000])}}
    extras=[]
    for name in ('t2f','gate'):
        folder=getattr(a,name);proof=getattr(a,name+'_drc')
        assert (folder is None)==(proof is None)
        if folder is not None:
            extras.append(name);cases.append((name,folder,proof))
            points.update({name+'_'+pin:value for pin,value in extra_points[name].items()})
    for name,folder,proof in cases:
        m=json.loads((folder/'analysis.json').read_text());d=json.loads((proof/'summary.json').read_text())
        gds=folder/'power_overlay.gds'
        assert m['status'].startswith('passed') and m['source_GDS_sha256']==PDN
        assert sha(gds)==m['overlay_sha256'] and d['GDS_sha256']==m['GDS_sha256']
        assert d['status']=='passed scoped main and maximal DRC' and d['inputs_rules_unchanged']
        assert {x['name']for x in d['decks']}=={'main','maximal'}
        for deck in d['decks']:
            assert deck['status']=='passed' and len(deck['reports'])==1
            report=deck['reports'][0]
            assert report['markers']==0 and sha(proof/report['path'])==report['sha256']
        ol=pya.Layout();ol.read(str(gds));ot=ol.top_cell()
        assert ol.dbu==.001 and not text_records(ol,ot)
        overlays.append((name,ol,ot))
        bindings.append(dict(macro=name,overlay_sha256=sha(gds),metadata_sha256=sha(folder/'analysis.json'),
                             stock_proof_sha256=sha(proof/'summary.json'),candidate_core_GDS_sha256=m['GDS_sha256']))
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    ly=pya.Layout();ly.read(str(source));top=ly.top_cell();assert ly.dbu==.001
    oldnet,oldlayers=physical(ly,top)
    oldprobes={n:identity(oldnet,oldlayers[l],xy)for n,(l,xy)in points.items()}
    assert None not in oldprobes.values()
    assert oldprobes['sense_vss']==oldprobes['core_vss']
    assert oldprobes['sense_vdda']==oldprobes['pad07_external']
    allowed={'BGR_VDDA':{oldprobes['bgr_vdda']},
             'VDD':{oldprobes['osc_vdd'],oldprobes['core_vdd']},
             'VSS':{oldprobes['bgr_vss'],oldprobes['osc_vss'],oldprobes['core_vss']}}
    for name in extras:
        allowed['VDD'].add(oldprobes[name+'_vdd'])
        allowed['VSS'].add(oldprobes[name+'_vss'])
    for first in allowed:
        for second in allowed:
            if first!=second:assert not (allowed[first]&allowed[second])
        assert oldprobes['sense_vdda'] not in allowed[first]
        for name in extras:assert oldprobes[name+'_vdda'] not in allowed[first]
    numbers=METALS+tuple(c[0]for c in CUTS)
    routes={n:{l:pya.Region()for l in numbers}for n in allowed}
    for name,ol,ot in overlays:
        onet,olayers=physical(ol,ot)
        anchors=[('BGR_VDDA','bgr_vdda'),('VSS','bgr_vss')]if name=='bgr'else[('VDD',name+'_vdd'),('VSS',name+'_vss')]
        mapped={identity(onet,olayers[points[k][0]],points[k][1]):n for n,k in anchors}
        assert None not in mapped and len(mapped)==2
        for info in ol.layer_infos():
            polys=region(ol,ot,info)
            if polys.is_empty():continue
            assert info.datatype==0 and info.layer in numbers
            layer=info.layer;probe_layer=layer if layer in METALS else next(lo for cut,lo,hi in CUTS if cut==layer)
            for poly in polys.each():
                key=identity(onet,olayers[probe_layer],point(poly));assert key in mapped
                routes[mapped[key]][layer].insert(poly)
    old={l:region(ly,top,pya.LayerInfo(l,0))for l in numbers}
    errors=[];checks=collections.Counter()
    def check(name,layer,polys,reason):
        for poly in polys.each():
            xy=point(poly);found=identity(oldnet,oldlayers[layer],xy);checks[reason]+=1
            if found not in allowed[name]:errors.append(dict(net=name,layer=layer,point=xy,actual=found,reason=reason))
    for name,added in routes.items():
        for layer in METALS:check(name,layer,old[layer].interacting(added[layer]),'new metal touches old metal')
        for cut,lo,hi in CUTS:
            for layer,opposite in ((lo,hi),(hi,lo)):
                check(name,opposite,old[opposite].interacting(old[cut].interacting(added[layer])),'new metal touches old cut')
                check(name,layer,old[layer].interacting(added[cut]),'new cut touches old metal')
    (a.output/'foreign_contact_gate.json').write_text(json.dumps(dict(status='failed'if errors else'passed',
        errors=errors,checks=dict(checks),old_probes=oldprobes),indent=2)+'\n')
    assert not errors,errors[:10]
    before={str(i):region(ly,top,i)for i in ly.layer_infos()};texts=text_records(ly,top)
    instances=sorted((i.cell.name,str(i.trans))for i in top.each_inst());assert len(instances)==4904
    for added in routes.values():
        for layer,polys in added.items():
            for poly in polys.each():top.shapes(ly.layer(layer,0)).insert(poly)
    newnet,newlayers=physical(ly,top)
    probes={n:identity(newnet,newlayers[l],xy)for n,(l,xy)in points.items()}
    handoff=identity(newnet,newlayers[134],[743400,922000])
    assert None not in probes.values() and handoff is not None
    assert probes['bgr_vdda']==handoff
    assert probes['osc_vdd']==probes['core_vdd']
    assert probes['bgr_vss']==probes['osc_vss']==probes['sense_vss']==probes['core_vss']
    assert probes['sense_vdda']==probes['pad07_external']
    assert len({probes[n]for n in ('bgr_vdda','sense_vdda','core_vdd','core_vss')})==4
    for name in extras:
        assert probes[name+'_vdd']==probes['core_vdd']
        assert probes[name+'_vss']==probes['core_vss']
    assert len({probes[n]for n in ['bgr_vdda','sense_vdda','core_vdd','core_vss']+[x+'_vdda'for x in extras]})==4+len(extras)
    count=0
    for row in json.loads((a.placement/'analysis.json').read_text())['decaps']:
        for name,pin in row['pins'].items():
            target=probes['core_vdd'if name=='VDD'else'core_vss']
            for layer in (8,10):assert identity(newnet,newlayers[layer],pin['placed_dbu'])==target
            count+=1
    assert count==9324
    for info in ly.layer_infos():
        expected=before.get(str(info),pya.Region())
        for name,ol,ot in overlays:expected+=region(ol,ot,info)
        assert (region(ly,top,info)^expected).is_empty(),str(info)
    assert text_records(ly,top)==texts
    assert sorted((i.cell.name,str(i.trans))for i in top.each_inst())==instances
    output=a.output/'power_connected_native.gds';ly.write(str(output))
    saved=pya.Layout();saved.read(str(output));st=saved.top_cell()
    assert text_records(saved,st)==texts
    assert sorted((i.cell.name,str(i.trans))for i in st.each_inst())==instances
    for info in ly.layer_infos():assert (region(ly,top,info)^region(saved,st,info)).is_empty()
    result=dict(status='passed scoped local core-rail integration; unfinished VDDA branches unpowered',
        GDS_sha256=sha(output),native_GDS_sha256=sha(source),script_sha256=sha(Path(__file__)),overlays=bindings,
        native_instances_retained=4904,decap_pin_pairs_held=count,placement_sha256=sha(a.placement/'analysis.json'),
        exact_additive_native_polygons_texts_roundtrip='passed',no_foreign_contact='passed',probes=probes,
        BGR_VDDA_handoff_unpowered='passed',
        optional_core_rail_macros=extras,optional_VDDA_branches_unpowered='passed',
        not_run=['aggregate VDDA trunk and pad current capacity','other macro feeds','new-context stock DRC/LVS',
                 'signal routing in this candidate','full PEX/density/antenna/currentIR/EM','electrical adoption'],
        not_applicable=['qualified supply current from exploratory 1 mA branch sizing'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    faulthandler.cancel_dump_traceback_later()


if __name__=='__main__':main()
