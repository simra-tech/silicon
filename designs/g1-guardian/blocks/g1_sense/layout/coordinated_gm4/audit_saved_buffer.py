#!/usr/bin/env python3
"""Read-only saved-buffer polygon and source audit, without generator replay."""
import argparse,collections,copy,hashlib,json,os,re
from pathlib import Path
from build_source_faithful_buffer import pya,snapshot,full_nets
from audit_junction_defaults import default

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def contains(box,point):return box.contains(pya.DPoint(*point).to_itype(.001))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--buffer',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and os.sched_getaffinity(0)=={7}
    source=Path(__file__).resolve().parents[2]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    m=json.loads((a.buffer/'manifest.json').read_text());gds=a.buffer/'g1_ota_source_faithful.gds'
    assert sha(gds)==m['GDS_sha256']=='320df90ee046c73b628005da9384c80fbd21a715a39b0e8b96b10923726fc500'
    result=dict(status='running',GDS_sha256=sha(gds),source_sha256=sha(source),manifest_sha256=sha(a.buffer/'manifest.json'),script_sha256=sha(Path(__file__)))
    try:
        block=re.search(r'(?ms)^\.subckt g1_ota .*?^\.ends',source.read_text()).group(0)
        specs={line.split()[0]:line for line in block.splitlines() if line.startswith('XM') or line.startswith('XMB') or line.startswith('XMT')}
        assert len(specs)==19
        ly=pya.Layout();ly.read(str(gds));cell=ly.cell('g1_ota_source_faithful');active=snapshot(cell,1);poly=snapshot(cell,5)
        probes=copy.deepcopy(m['independent_audit']['terminal_audit']['probes']);terminal=full_nets(cell,probes);assert terminal['status']=='passed'
        gate_probes=[q for q in probes if q['terminal']=='gate'];diff_probes=[q for q in probes if q['layer']==501]
        gates=[];owners=collections.defaultdict(list)
        for polygon in (active&poly).each():
            box=polygon.bbox();assert polygon.area()==box.area()
            candidates=[q for q in gate_probes if contains(box,q['point_um'])];assert len(candidates)==1
            q=candidates[0];owner=q['device'];assert q['net']==specs[owner].split()[2]
            gates.append((box,owner));owners[owner].append(box)
        assert len(gates)==len(gate_probes)
        allocated={n:dict(as_um2=0.,ad_um2=0.,ps_um=0.,pd_um=0.) for n in specs};strips=[]
        for polygon in (active-poly).each():
            box=polygon.bbox()
            adjacent=[(b,n) for b,n in gates if b.bottom==box.bottom and b.top==box.top and (b.left==box.right or b.right==box.left)]
            if not adjacent:continue # body/guard Activ, not a transistor diffusion strip
            assert 1<=len(adjacent)<=2 and polygon.area()==box.area()
            matches=[q for q in diff_probes if contains(box,q['point_um'])];assert len(matches)==1
            net=matches[0]['net'];weights=collections.Counter(n for b,n in adjacent)
            terms={}
            for owner,count in weights.items():
                words=specs[owner].split();possible=[field for field,index in [('d',1),('s',3)] if words[index]==net];assert len(possible)==1
                field=possible[0];weight=count/len(adjacent);terms[owner]=dict(terminal=field,weight=weight)
                allocated[owner]['a'+field+'_um2']+=weight*polygon.area()*1e-6
                allocated[owner]['p'+field+'_um']+=weight*polygon.perimeter()*.001
            strips.append(dict(bbox_um=[v*.001 for v in (box.left,box.bottom,box.right,box.top)],net=net,allocation=terms))
        assert len(strips)==len(diff_probes)
        rows=[]
        for name,line in specs.items():
            params=dict(re.findall(r'(\w+)=([^\s]+)',line));ng=int(params['ng']);w=float(params['w'].rstrip('u'));length=float(params['l'].rstrip('u'));boxes=owners[name]
            assert len(boxes)==ng and all(abs(b.width()*.001-length)<1e-8 for b in boxes)
            assert abs(sum(b.height()*.001 for b in boxes)-w)<1e-8
            expected=default(w,ng);assert all(abs(expected[k]-allocated[name][k])<1e-8 for k in expected)
            rows.append(dict(device=name,source_line=line,actual_ng=ng,W_um=w,L_um=length,allocated_junction=allocated[name],default_junction=expected,
                             gate_centroid_um=[sum((b.center().x if axis==0 else b.center().y)*.001 for b in boxes)/ng for axis in (0,1)]))
        pair=[r for r in rows if r['device'] in ('XM1','XM2')];assert all(abs(pair[0]['gate_centroid_um'][i]-pair[1]['gate_centroid_um'][i])<1e-8 for i in (0,1))
        resistor=snapshot(cell,128);capacitor=snapshot(cell,36);rb=resistor.bbox();cb=capacitor.bbox()
        assert resistor.count()==capacitor.count()==1 and (rb.width(),rb.height(),resistor.area())==(1000,6200,6200000)
        assert (cb.width(),cb.height(),capacitor.area())==(23000,23000,529000000)
        bbox=cell.bbox();assert bbox.width()<=110000 and bbox.height()<=65000
        result.update(status='passed saved-buffer source/native/terminal audit',devices=rows,strips=strips,terminal_audit=terminal,
                      width_um=bbox.width()*.001,height_um=bbox.height()*.001,RZ_dimensions='passed1x6.2um',CC_dimensions='passed23x23um',
                      source_unchanged=sha(source)==m['source_sha256'],GDS_unchanged=sha(gds)==m['GDS_sha256'],
                      shared_source_allocation='Adjacent-gate bookkeeping only; intrinsic mismatch/junction applicability not run',
                      R_C_terminal_LVS='not run',well_substrate_isolation='not run',stock_checks='not run',new_GDS_saved=False)
    except Exception as exc:
        result.update(status='failed saved-buffer audit',exception_type=type(exc).__name__,detail=str(exc))
        a.output.write_text(json.dumps(result,indent=2)+'\n');raise
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('devices','strips','terminal_audit')},indent=2))
if __name__=='__main__':main()
