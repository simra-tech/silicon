#!/usr/bin/env python3
"""Join core VDD/VSS to corresponding native IO rails, preserving IOVDD/IOVSS."""
import argparse
import collections
import faulthandler
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region,text_records,sha
from audit_placed_decap_domains import identity
from flat_metal_connectivity import flat_physical
from build_native_decap_pdn import METALS,CUTS,point

POINTS={'VDD_root':(134,[395000,354660]),'VSS_root':(134,[507000,334660]),
        'VDD_pad':(134,[395000,106000]),'VSS_pad':(134,[507000,106000]),
        'IOVDD':(134,[619000,106000]),'IOVSS':(134,[731000,106000]),
        'VDDA':(134,[1271500,395000]),'VDD_native':(30,[410000,310000]),
        'VSS_native':(126,[520000,310000])}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert pya.__version__=='0.30.9'
    source=a.native/'power_connected_native.gds';meta=json.loads((a.native/'analysis.json').read_text())
    assert meta['status'].startswith('passed') and sha(source)==meta['GDS_sha256']
    assert meta['native_instances_retained']==4904 and meta['decap_pin_pairs_held']==9324
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',source_GDS_sha256=sha(source),source_metadata_sha256=sha(a.native/'analysis.json'),
        script_sha256=sha(Path(__file__)),prospective_branch_mA=10,
        current_scope='Prospective layout sizing only; actual full-chip and native-pad current envelopes unqualified')
    receipt=a.output/'analysis.json';faulthandler.dump_traceback_later(60,repeat=True)
    try:
        ly=pya.Layout();ly.read(str(source));top=ly.top_cell();assert ly.dbu==.001
        numbers=METALS+tuple(c[0]for c in CUTS)
        old={l:region(ly,top,pya.LayerInfo(l,0))for l in numbers}
        assert (pya.Region(pya.Box(355000,301000,435000,319000))-old[30]).is_empty()
        assert (pya.Region(pya.Box(467000,301000,547000,319000))-old[126]).is_empty()
        net,ml,held=flat_physical(ly,top)
        before_points={n:identity(net,ml[l],xy)for n,(l,xy)in POINTS.items()}
        assert None not in before_points.values()
        assert before_points['VDD_pad']==before_points['VDD_native']
        assert before_points['VSS_pad']==before_points['VSS_native']
        assert len(set(before_points.values()))==7
        allowed={n:{before_points[n+'_root'],before_points[n+'_pad']}for n in ('VDD','VSS')}
        routes={n:{l:pya.Region()for l in numbers}for n in allowed};arrays=[]
        def put(n,l,bounds):routes[n][l].insert(pya.Box(*bounds))
        def array(n,cut,x,y,nx,ny):
            _,lo,hi=next(row for row in CUTS if row[0]==cut)
            size,pitch,enc,limit=(190,500,55,.4)if cut<100 else(420,840,120,1.4)if cut==125 else(900,1960,650,10.)
            sx=(nx-1)*pitch+size;sy=(ny-1)*pitch+size;boxes=[]
            for i in range(nx):
                for j in range(ny):
                    cx=x+(2*i-(nx-1))*pitch//2;cy=y+(2*j-(ny-1))*pitch//2
                    box=[cx-size//2,cy-size//2,cx+size//2,cy+size//2]
                    put(n,cut,box);boxes.append(box)
            for l in (lo,hi):
                extra=450 if cut==125 and l==126 else enc
                minimum=1640 if l==126 else 2000 if l==134 else 200
                wx=max(sx+2*extra,minimum);wy=max(sy+2*extra,minimum)
                put(n,l,[x-wx//2,y-wy//2,x+wx//2,y+wy//2])
            arrays.append(dict(net=n,layer=cut,center_dbu=[x,y],cuts=boxes,
                half_table_sum_mA=.5*nx*ny*limit,one_cut_removed_half_sum_mA=.5*(nx*ny-1)*limit))
        # VDD uses M3 across the orthogonal VSS top-metal ring. Its upper stack
        # at x410 avoids the new digital VSS TM1 extension at x394.96.
        put('VDD',30,[404900,304900,415100,359760])
        array('VDD',49,410000,354660,8,8)
        array('VDD',66,410000,354660,8,8)
        array('VDD',125,410000,354660,5,4)
        array('VDD',133,410000,354660,3,2)
        put('VSS',126,[517000,307000,523000,337660])
        array('VSS',133,520000,334660,3,2)
        errors=[];counts=collections.Counter()
        def inspect(n,l,polys,why):
            for poly in polys.each():
                xy=point(poly);found=identity(net,ml[l],xy);counts[why]+=1
                if found not in allowed[n]:errors.append(dict(net=n,layer=l,point=xy,actual=found,reason=why))
        for n,added in routes.items():
            other='VSS'if n=='VDD'else'VDD'
            for l in METALS:
                inspect(n,l,old[l].interacting(added[l]),'new metal touches native metal')
                assert added[l].interacting(routes[other][l]).is_empty()
            for cut,lo,hi in CUTS:
                for l,opposite in ((lo,hi),(hi,lo)):
                    inspect(n,opposite,old[opposite].interacting(old[cut].interacting(added[l])),'new metal touches native cut')
                    inspect(n,l,old[l].interacting(added[cut]),'new cut touches native metal')
                    assert (added[cut]-(old[l]+added[l])).is_empty()
                    assert added[cut].interacting(routes[other][l]).is_empty()
        (a.output/'contact_gate.json').write_text(json.dumps(dict(status='failed'if errors else'passed',
            errors=errors,counts=dict(counts),source_probes=before_points,arrays=arrays),indent=2)+'\n')
        assert not errors,errors[:12]
        before={str(i):region(ly,top,i)for i in ly.layer_infos()};texts=text_records(ly,top)
        instances=sorted((i.cell.name,str(i.trans))for i in top.each_inst());assert len(instances)==4904
        overlay=pya.Layout();overlay.dbu=.001;ot=overlay.create_cell('core_io_power_feeds_NOT_ADOPTED')
        for added in routes.values():
            for l,polys in added.items():
                top.shapes(ly.layer(l,0)).insert(polys);ot.shapes(overlay.layer(l,0)).insert(polys)
        output=a.output/'power_connected_native.gds';ly.write(str(output));overlay.write(str(a.output/'power_overlay.gds'))
        saved=pya.Layout();saved.read(str(output));st=saved.top_cell()
        assert text_records(saved,st)==texts
        assert sorted((i.cell.name,str(i.trans))for i in st.each_inst())==instances
        for info in saved.layer_infos():
            expected=before.get(str(info),pya.Region())
            if info.datatype==0 and info.layer in numbers:
                for added in routes.values():expected+=added[info.layer]
            assert (region(saved,st,info)^expected).is_empty(),str(info)
        nn,nm,nh=flat_physical(saved,st)
        probes={n:identity(nn,nm[l],xy)for n,(l,xy)in POINTS.items()}
        assert None not in probes.values()
        for n in allowed:assert probes[n+'_root']==probes[n+'_pad']==probes[n+'_native']
        assert len(set(probes.values()))==5
        result.update(status='passed additive core-to-IO VDD VSS feeds',GDS_sha256=sha(output),
            overlay_sha256=sha(a.output/'power_overlay.gds'),arrays=arrays,probes=probes,
            native_instances_retained=4904,decap_pin_pairs_held=9324,
            source_geometry_texts_instances_saved_roundtrip='passed',no_foreign_contact='passed',
            flat_actual_native_to_root_joining='passed',
            not_run=['stock DRC and cut-open audit','remaining macro feeds and final signal routing',
                'native IO current distribution','full currentIR EM PVT and electrical adoption'])
    except Exception as exc:
        result.update(status='failed core-to-IO supply feeds',error=repr(exc));raise
    finally:
        receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
        faulthandler.cancel_dump_traceback_later()


if __name__=='__main__':main()
