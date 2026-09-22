#!/usr/bin/env python3
"""Flatten and uniquely label an extraction-only view, retaining native polygons."""
import argparse,copy,hashlib,json,os,re
from pathlib import Path
from build_native_prototypes import pya,snapshot
from build_source_faithful_buffer import full_nets

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def materialize(region):
    result=pya.Region()
    for polygon in region.each():result.insert(pya.Polygon(polygon))
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('candidate','reference','stock','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    ref=json.loads((a.reference/'manifest.json').read_text());stock=json.loads((a.stock/'summary.json').read_text());assert stock['status']=='passed' and stock['checks'][-1]['nine_source_pin_gate']
    gds=a.candidate/'g1_sense_physical.gds';assert sha(gds)==stock['GDS_sha256']==ref['GDS_sha256']=='6609a77884a0009924422bf9871ea699e2393c8988412e1b000057cf3448beda'
    source=Path(__file__).resolve().parents[2]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)==ref['source_sha256']=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    a.output.mkdir(parents=True);(a.output/'builder_snapshot.py').write_bytes(Path(__file__).read_bytes());result=dict(source_sha256=sha(source),candidate_GDS_sha256=sha(gds),reference_manifest_sha256=sha(a.reference/'manifest.json'),stock_summary_sha256=sha(a.stock/'summary.json'),script_sha256=sha(Path(__file__)),PEX='not run',source_preserving_electrical_netlist='not run',adoption='not run')
    try:
        old=pya.Layout();old.read(str(gds));original=old.cell('g1_sense_physical');ly=pya.Layout();ly.dbu=.001;cell=ly.create_cell('g1_sense_physical');layers=[]
        for li in old.layer_indexes():
            info=old.get_info(li)
            if info.datatype in(2,25):continue
            dest=ly.layer(info);before=materialize(pya.Region(original.begin_shapes_rec(li))).merged()
            for polygon in before.each():cell.shapes(dest).insert(pya.Polygon(polygon))
            delta=materialize(before^materialize(pya.Region(cell.begin_shapes_rec(dest))));assert delta.is_empty();layers.append(dict(layer=info.layer,datatype=info.datatype,XOR_um2=0.))
        assert(snapshot(cell,1)&snapshot(cell,5)).count()==835 and snapshot(cell,128).count()==98 and snapshot(cell,36).count()==3
        probes=copy.deepcopy(ref['terminal_audit']['probes']);graph=full_nets(cell,probes);assert graph['status']=='passed'
        nets=sorted({q['net']for q in probes});ports=ref['ports'];mapping={n:(n if n in ports else'n__'+re.sub(r'[^a-z0-9_]','__',n.lower()))for n in nets};assert len(set(mapping.values()))==len(nets)
        metals={layer:snapshot(cell,layer)for layer in(8,10,30,50,67,126)};rank={layer:i for i,layer in enumerate((126,67,50,30,10,8,501,5))};labels=[]
        for net in nets:
            candidates=sorted((q for q in probes if q['net']==net),key=lambda q:rank[q['layer']]);picked=None
            for q in candidates:
                layer=8 if q['layer']==501 else q['layer']
                if layer not in metals:continue
                pt=pya.DPoint(*q['point_um']).to_itype(.001)
                if not metals[layer].interacting(pya.Region(pya.Box(pt.x-1,pt.y-1,pt.x+1,pt.y+1))).is_empty():picked=(q,layer,pt);break
            assert picked is not None,net
            q,layer,pt=picked;assert pt.x%5==pt.y%5==0
            cell.shapes(ly.layer(layer,25)).insert(pya.Text(mapping[net],pya.Trans(pt.x,pt.y)))
            labels.append(dict(source_net=net,pex_label=mapping[net],layer=layer,point_um=[pt.x*.001,pt.y*.001],witness_device=q['device'],witness_terminal=q['terminal'],original_physical_net=q['physical_net']))
        graph2=full_nets(cell,copy.deepcopy(probes));assert graph2['status']=='passed'
        output=a.output/'g1_sense_pex_view.gds';ly.write(str(output));saved=pya.Layout();saved.read(str(output));check=saved.cell('g1_sense_physical');actual=[s.text.string for li in saved.layer_indexes()for s in check.shapes(li).each()if s.is_text()];assert sorted(actual)==sorted(mapping.values())
        for row in layers:
            lo=old.layer(row['layer'],row['datatype']);ls=saved.layer(row['layer'],row['datatype']);assert materialize(materialize(pya.Region(original.begin_shapes_rec(lo)))^materialize(pya.Region(check.begin_shapes_rec(ls)))).is_empty()
        result.update(status='passed extraction-only flat label view',GDS_sha256=sha(output),source_net_count=len(nets),labels=labels,nonannotation_layer_XOR=layers,channel_count=835,resistor_count=98,MIM_count=3,native_MIM_layers_retained=True,terminal_audit=graph2,scope='Full original unfilled native/conductive geometry retained. Only hierarchy and pin annotations differ; all source nets uniquely named on verified connected metal. This is an extraction diagnostic view, not a changed production pin interface. No MIM/device layer removed or model/card/deck changed.',blackbox_method='Prospective unchanged KPEX --blackbox true; coverage/excluded-device audit and extraction not run here')
    except Exception as exc:
        result.update(status='failed PEX-view preparation',exception_type=type(exc).__name__,detail=str(exc));(a.output/'failure.json').write_text(json.dumps(result,indent=2)+'\n');raise
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('labels','nonannotation_layer_XOR','terminal_audit')},indent=2))
if __name__=='__main__':main()
