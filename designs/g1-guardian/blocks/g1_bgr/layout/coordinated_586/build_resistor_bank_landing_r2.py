#!/usr/bin/env python3
"""Materialize one geometry-only derivative, retaining complete r1 evidence."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import pya
from run_second_stock import sha


def snap(cell,index):
    r=pya.Region(cell.begin_shapes_rec(index)).dup();r.flatten();return r


def main():
    root=Path(__file__).resolve().parents[6]
    old=root/'build/scratch/bgr-resistor-bank-pilot-20260922-r1'
    stock=root/'build/scratch/bgr-resistor-bank-stock-20260922-r1'
    new=root/'build/scratch/bgr-resistor-bank-pilot-20260922-r2'
    manifest=json.loads((old/'manifest.json').read_text())
    assert manifest['status']=='passed scoped geometry/terminal gate'
    original=Path(__file__).with_name('build_resistor_bank_pilot.py')
    assert sha(original)==manifest['script_sha256']
    report=stock/'drc/bgr_resistor_bank_pilot_bgr_resistor_bank_pilot_full.lyrdb'
    assert sha(report)=='174e0a8f638a339facf9e97a3b971c3516758005ea0916d9a2377664c93926da'
    items=ET.parse(report).findall('.//items/item');assert len(items)==73
    centers=set();marker_rows=[]
    ledger={(round(v['center_um'][0]*1000),round(v['center_um'][1]*1000)) for v in manifest['via_arrays'] if v['layer'] in ['Via2','Via3']}
    for item in items:
        assert item.findtext('category')=="'M3.b'"
        value=item.findtext('values/value');nums=[round(float(x)*1000) for x in re.findall(r'-?\d+(?:\.\d+)?',value)]
        assert len(nums)==8
        x1,y1,x2,y2,x3,y3,x4,y4=nums
        assert y1==y2 and y3==y4 and sorted([x1,x2])==sorted([x3,x4]) and abs(x2-x1)==300
        low,high=sorted([y1,y3]);assert high-low==160
        cx=(x1+x2)//2;pair=[(cx,low-420),(cx,high+420)]
        assert all(c in ledger for c in pair)
        centers.update(pair);marker_rows.append(dict(marker=value,landing_centers_dbu=pair))
    text=original.read_text()
    replacements=[("bgr-resistor-bank-pilot-20260922-r1'","bgr-resistor-bank-pilot-20260922-r2'"),
                  ("for metal in [lo,hi]:box(metal,x-.15,y-.42,x+.15,y+.42)",
                   "for metal in [lo,hi]:\n            half=.36 if metal=='M3' and (round(x*1000),round(y*1000)) in AFFECTED_CENTERS else .42\n            box(metal,x-.15,y-half,x+.15,y+half)"),
                  ('RESISTOR_BANK_PILOT_CONTRACT_20260922.md','RESISTOR_BANK_LANDING_R2_CONTRACT_20260922.md')]
    for before,after in replacements:
        assert text.count(before)==1,before
        text=text.replace(before,after)
    scope={'__file__':str(Path(__file__).resolve()),'__name__':'isolated_r2','AFFECTED_CENTERS':centers}
    exec(compile(text,str(original),'exec'),scope);scope['main']()
    result=json.loads((new/'manifest.json').read_text())
    assert result['status']=='passed scoped geometry/terminal gate'
    assert result['native_devices']==manifest['native_devices'] and result['tracks_um']==manifest['tracks_um'] and result['via_arrays']==manifest['via_arrays']
    assert (old/'bgr_resistor_bank_pilot.cdl').read_bytes()==(new/'bgr_resistor_bank_pilot.cdl').read_bytes()
    a,b=pya.Layout(),pya.Layout();a.read(str(old/'bgr_resistor_bank_pilot.gds'));b.read(str(new/'bgr_resistor_bank_pilot.gds'))
    assert a.dbu==b.dbu==.001
    regions=[];texts_equal=True;windows=pya.Region()
    for x,y in centers:windows.insert(pya.Box(x-150,y-420,x+150,y+420))
    for layer,datatype in sorted(set((i.layer,i.datatype) for i in a.layer_infos()+b.layer_infos())):
        ra=snap(a.top_cell(),a.layer(layer,datatype));rb=snap(b.top_cell(),b.layer(layer,datatype))
        diff=ra^rb;record=dict(layer=layer,datatype=datatype,xor_um2=diff.area()*1e-6)
        if (layer,datatype)==(30,0):
            assert (rb-ra).is_empty() and not (ra-rb).is_empty() and ((ra-rb)-windows).is_empty()
            record['removed_um2']=(ra-rb).area()*1e-6
        else:assert diff.is_empty(),record
        ts=[]
        for layout in [a,b]:
            it=layout.top_cell().begin_shapes_rec(layout.layer(layer,datatype));found=[]
            while not it.at_end():
                if it.shape().is_text():found.append(str(it.shape().text.transformed(it.trans())))
                it.next()
            ts.append(sorted(found))
        assert ts[0]==ts[1];regions.append(record)
    m3=snap(b.top_cell(),b.layer(30,0));cuts=snap(b.top_cell(),b.layer(29,0))+snap(b.top_cell(),b.layer(49,0))
    assert (cuts.sized(55)-m3).is_empty()
    audit=dict(status='passed scoped M3-only landing reduction',parent_GDS_sha256=manifest['GDS_sha256'],GDS_sha256=result['GDS_sha256'],
               unchanged_CDL_sha256=result['CDL_sha256'],old_report_sha256=sha(report),markers=marker_rows,
               affected_landing_center_count=len(centers),affected_centers_dbu=sorted(centers),layer_changes=regions,
               all_text_exact=True,native_devices_exact=True,tracks_via_centers_cuts_exact=True,
               all_Via2_Via3_M3_55nm_enclosure=True,derived_generator_sha256=hashlib.sha256(text.encode()).hexdigest(),
               replacements=[dict(before=x,after=y) for x,y in replacements],stock_DRC_LVS='not run',r1_DRC='failed73M3.b retained')
    (new/'derived_generator.py').write_text(text)
    (new/'landing_revision_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:audit[k] for k in ['status','affected_landing_center_count','GDS_sha256','all_Via2_Via3_M3_55nm_enclosure']},indent=2))


if __name__=='__main__':main()
