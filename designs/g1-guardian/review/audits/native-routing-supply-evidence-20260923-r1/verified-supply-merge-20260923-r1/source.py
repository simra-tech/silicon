#!/usr/bin/env python3
"""Integrate independently checked feeds with instance-resolved contact gates."""
import argparse
import collections
import faulthandler
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region, text_records, sha
from audit_placed_decap_domains import identity
from flat_metal_connectivity import flat_physical
from build_native_decap_pdn import METALS, CUTS, point

BASE='e1dfbc73cd380282766b6576298fb3df7c356b1f84744dca1474bfc2fcefda5f'
POINTS={
    'VDD':{'root':(134,[395000,354660]),'digital':(126,[388760,376000])},
    'VSS':{'root':(134,[507000,334660]),'digital':(126,[394960,376000]),
           'dut':(30,[736800,401000]),'dose':(30,[736800,451000])},
    'VDDA':{'pad':(30,[1093145,395000]),'bgr':(134,[743400,922000]),
            'sense':(134,[813000,714000])}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('native','shared','shared-proof','digital','digital-proof','dut','dut-proof','dose','dose-proof','output'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert pya.__version__=='0.30.9'
    source=a.native/'power_connected_native.gds';meta=json.loads((a.native/'analysis.json').read_text())
    assert meta['status'].startswith('passed') and sha(source)==meta['GDS_sha256']==BASE
    assert meta['native_instances_retained']==4904 and meta['decap_pin_pairs_held']==9324
    bindings=[];overlays=[]
    for name in ('shared','digital','dut','dose'):
        folder=getattr(a,name);proof=getattr(a,name+'_proof')
        m=json.loads((folder/'analysis.json').read_text());s=json.loads((proof/'summary.json').read_text())
        ogds=folder/'power_overlay.gds'
        assert m['status'].startswith('passed') and sha(ogds)==m['overlay_sha256']
        assert s['GDS_sha256']==m['GDS_sha256'] and s['inputs_rules_unchanged']
        if name=='shared':
            comparison=json.loads((proof/'marker_comparison.json').read_text())
            assert comparison['status'].startswith('passed')
            assert not comparison['added'] and not comparison['removed']
            assert len(s['decks'])==1 and s['decks'][0]['returncode']==0
        else:
            assert s['status']=='passed scoped main and maximal DRC'
            assert {r['name'] for r in s['decks']}=={'main','maximal'}
            assert all(r['status']=='passed' and len(r['reports'])==1 and r['reports'][0]['markers']==0 for r in s['decks'])
        for deck in s['decks']:
            for report in deck['reports']:assert sha(proof/report['path'])==report['sha256']
        ol=pya.Layout();ol.read(str(ogds));ot=ol.top_cell();assert ol.dbu==.001
        assert not text_records(ol,ot)
        overlays.append((name,ol,ot))
        bindings.append(dict(name=name,overlay_sha256=sha(ogds),metadata_sha256=sha(folder/'analysis.json'),
                             stock_summary_sha256=sha(proof/'summary.json'),candidate_GDS_sha256=m['GDS_sha256']))
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',source_GDS_sha256=sha(source),script_sha256=sha(Path(__file__)),overlays=bindings)
    receipt=a.output/'analysis.json'
    faulthandler.dump_traceback_later(60,repeat=True)
    try:
        ly=pya.Layout();ly.read(str(source));top=ly.top_cell()
        net,ml,held=flat_physical(ly,top)
        oldpoints={n:{key:identity(net,ml[layer],xy) for key,(layer,xy) in group.items()} for n,group in POINTS.items()}
        allowed={n:set(group.values()) for n,group in oldpoints.items()}
        assert all(None not in keys for keys in allowed.values())
        assert all(not (allowed[n]&allowed[m]) for n in allowed for m in allowed if n!=m)
        numbers=METALS+tuple(c[0] for c in CUTS)
        routes={n:{layer:pya.Region() for layer in numbers} for n in allowed}
        for name,ol,ot in overlays:
            on,om,oh=flat_physical(ol,ot)
            keys=('VDDA',) if name=='shared' else ('VDD','VSS') if name=='digital' else ('VSS',)
            mapping={}
            for n in keys:
                key='pad' if name=='shared' else name
                layer,xy=POINTS[n][key];cluster=identity(on,om[layer],xy)
                assert cluster is not None and cluster not in mapping
                mapping[cluster]=n
            for info in ol.layer_infos():
                polys=region(ol,ot,info)
                if polys.is_empty():continue
                assert info.datatype==0 and info.layer in numbers
                layer=info.layer;probe=layer if layer in METALS else next(lo for cut,lo,hi in CUTS if cut==layer)
                for poly in polys.each():
                    cluster=identity(on,om[probe],point(poly));assert cluster in mapping,(name,layer,cluster)
                    routes[mapping[cluster]][layer].insert(poly)
        old={layer:region(ly,top,pya.LayerInfo(layer,0)) for layer in numbers}
        errors=[];counts=collections.Counter()
        def check(n,layer,polys,why):
            for poly in polys.each():
                xy=point(poly);actual=identity(net,ml[layer],xy);counts[why]+=1
                if actual not in allowed[n]:errors.append(dict(net=n,layer=layer,point=xy,actual=actual,reason=why))
        for n,added in routes.items():
            for layer in METALS:
                check(n,layer,old[layer].interacting(added[layer]),'new metal touches native metal')
                for other in routes:
                    if other!=n:assert added[layer].interacting(routes[other][layer]).is_empty(),(n,other,layer)
            for cut,lo,hi in CUTS:
                for layer,opposite in ((lo,hi),(hi,lo)):
                    check(n,opposite,old[opposite].interacting(old[cut].interacting(added[layer])),'new metal touches old cut')
                    check(n,layer,old[layer].interacting(added[cut]),'new cut touches native metal')
                    assert (added[cut]-(old[layer]+added[layer])).is_empty()
                    for other in routes:
                        if other!=n:assert added[cut].interacting(routes[other][layer]).is_empty(),(n,other,cut)
        (a.output/'contact_gate.json').write_text(json.dumps(dict(status='failed' if errors else 'passed',
            errors=errors,counts=dict(counts),source_probes=oldpoints),indent=2)+'\n')
        assert not errors,errors[:10]
        before={str(i):region(ly,top,i) for i in ly.layer_infos()};texts=text_records(ly,top)
        instances=sorted((i.cell.name,str(i.trans)) for i in top.each_inst());assert len(instances)==4904
        for added in routes.values():
            for layer,polys in added.items():top.shapes(ly.layer(layer,0)).insert(polys)
        output=a.output/'power_connected_native.gds';ly.write(str(output))
        saved=pya.Layout();saved.read(str(output));st=saved.top_cell()
        assert text_records(saved,st)==texts
        assert sorted((i.cell.name,str(i.trans)) for i in st.each_inst())==instances
        for info in saved.layer_infos():
            expected=before.get(str(info),pya.Region())
            if info.datatype==0 and info.layer in numbers:
                for added in routes.values():expected+=added[info.layer]
            assert (region(saved,st,info)^expected).is_empty(),str(info)
        nn,nm,nh=flat_physical(saved,st)
        probes={n:{key:identity(nn,nm[layer],xy) for key,(layer,xy) in group.items()} for n,group in POINTS.items()}
        assert all(None not in group.values() and len(set(group.values()))==1 for group in probes.values())
        assert len({next(iter(group.values())) for group in probes.values()})==3
        result.update(status='passed additive shared digital DUT DOSE supply integration',GDS_sha256=sha(output),
            native_instances_retained=4904,decap_pin_pairs_held=9324,
            source_geometry_texts_instances_saved_roundtrip='passed',flat_actual_joining='passed',probes=probes,
            no_foreign_contact='passed',not_run=['new-context stock DRC','core-to-IO VDD/VSS joins','LS/TRIP feeds',
                'remaining VDDA branches','final signal routing','complete LVS/PEX/currentIR/EM/electrical adoption'])
    except Exception as exc:
        result.update(status='failed supply integration',error=repr(exc));raise
    finally:
        receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
        faulthandler.cancel_dump_traceback_later()


if __name__=='__main__':main()
