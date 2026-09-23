#!/usr/bin/env python3
"""Isolated design-local resistor marking repair; original library held."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import pya

PDK=Path('/foss/pdks/ihp-sg13g2')
PIN='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--gate',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0))=={1}
    gate=json.loads(a.gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and gate['project_cpu_budget']>=44 and 0<=age<1800
    assert pya.__version__=='0.30.9' and (PDK/'COMMIT').read_text().strip()==PIN
    source=PDK/'libs.ref/sg13g2_io/gds/sg13g2_io.gds'
    cdl=PDK/'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl'
    assert sha(source)=='4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825'
    assert sha(cdl)=='7a30e902099e8a8f85e0ae853167904df3793357a793a7b4dc82237b72b3eec4'
    a.output.mkdir(parents=True)
    (a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    text=cdl.read_text(); original=pya.Layout();original.read(str(source))
    results=[]
    for old,suffix,count,length in [('sg13g2_SecondaryProtection','secondary',1,2),('sg13g2_RCClampResistor','rc',26,20)]:
        native=original.cell(old)
        ly=pya.Layout();ly.dbu=original.dbu
        top=ly.create_cell('g1_io_'+suffix+'_polyres_r1');top.copy_tree(native)
        region=lambda layer:pya.Region(top.begin_shapes_rec(ly.layer(layer,0))).merged()
        intended=region(5)&region(28)&region(111)&region(14)
        assert region(128).is_empty() and intended.count()==count
        boxes=[]
        for polygon in intended.each():
            b=polygon.bbox()
            assert polygon.area()==b.area() and b.width()==1000 and b.height()==length*1000
            assert (pya.Region(b)&region(6)).is_empty()
            boxes.append(str(b))
        # Two negative geometry controls: translation into contacts and larger
        # marker extending beyond the independently defined physical body.
        wrong=intended.transformed(pya.Trans(0,430))
        oversized=intended.sized(5)
        assert not (wrong-intended).is_empty() and not (oversized-intended).is_empty()
        top.shapes(ly.layer(128,0)).insert(intended)
        gds=a.output/(suffix+'.gds');ly.write(str(gds))
        fresh=pya.Layout();fresh.read(str(gds));fc=fresh.top_cell()
        assert fc.name==top.name
        changes=[];texts=[]
        for layer in sorted({(i.layer,i.datatype) for l in (original,fresh) for i in l.layer_infos()}):
            oldreg=pya.Region(native.begin_shapes_rec(original.layer(*layer))).merged()
            newreg=pya.Region(fc.begin_shapes_rec(fresh.layer(*layer))).merged()
            delta=oldreg^newreg
            if layer==(128,0):assert (delta^intended).is_empty()
            else:assert delta.is_empty(),str(layer)
            if not delta.is_empty():changes.append(dict(layer=list(layer),area_um2=delta.area()*1e-6))
            def strings(layout,cell):
                values=[];it=cell.begin_shapes_rec(layout.layer(*layer))
                while not it.at_end():
                    if it.shape().is_text():values.append(str(it.trans()*it.shape().text))
                    it.next()
                return sorted(values)
            ta,tb=strings(original,native),strings(fresh,fc)
            assert ta==tb
            if ta:texts.append(dict(layer=list(layer),values=ta))
        match=re.search(r'(?im)^\.SUBCKT '+re.escape(old)+r'\b.*?^\.ENDS\b[^\n]*',text,re.S)
        assert match
        body=match.group(0)
        assert not any(l.lstrip().upper().startswith('XI') for l in body.splitlines()),'Unexpected child hierarchy'
        derivative=body.replace('.SUBCKT '+old,'.SUBCKT '+top.name,1)
        assert derivative.replace('.SUBCKT '+top.name,'.SUBCKT '+old,1)==body
        reference=a.output/(suffix+'.cdl');reference.write_text(derivative+'\n')
        original_copy=a.output/(suffix+'_original.cdl');original_copy.write_text(body+'\n')
        result=dict(kind=suffix,old_cell=old,top=top.name,gds=str(gds),reference=str(reference),
                    GDS_sha256=sha(gds),CDL_sha256=sha(reference),source_body_sha256=sha(original_copy),
                    marker_count=count,marker_boxes_dbu=boxes,changes=changes,texts=texts,
                    expected_pins=body.splitlines()[0].split()[2:],source_reverse_exact=True,
                    no_other_polygon_or_text_change=True,
                    source_parameters_or_model_changes='not applicable',geometry_negative_controls='passed')
        results.append(result)
    summary=dict(status='passed isolated preparation',PDK_commit=PIN,KLayout=pya.__version__,
        inputs={str(p):sha(p) for p in (source,cdl)},cells=results,
        script_sha256=sha(Path(__file__)),resource_gate_sha256=sha(a.gate),
        design_scope='Actual design-layer change; fabrication-mask inertness NOT claimed',
        not_run=['stock DRC','strict LVS','fullchip adoption','electrical/ESD qualification'])
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
