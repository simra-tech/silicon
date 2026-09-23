#!/usr/bin/env python3
"""Source134-bound extraction views; no extraction or model composition claim."""
import argparse,copy,json,os,re
from pathlib import Path
from inspect_passive_sites import pya,sha,regions
PARENT='cec94187d33b60a654cb12213cfb7e0904fc2a0b5d70a3763fd9d223f44d34f7'
SOURCE='bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782'
from build_power_revision import full_nets_upper

OLD_SOURCE='b8912a862b61554266239634dd388ed0ffad229c0b0e48819ad129d589352e97'
NEW_GDS='450a49062d17f65be1046736c2ebeff219b4c4d4b22fac0998940c158741a637'
PORTS=['sense_p','sense_n','vref','iptat','isense','vped','vref_buf','vdd','vss']

def mapping(nets):
    assert len(nets)==len(set(nets))==134 and set(PORTS)<=set(nets)
    result={n:n if n in PORTS else 'n__'+re.sub('[^a-z0-9_]','__',n.lower()) for n in nets}
    assert len(set(result.values()))==134
    return result

def tests():
    nets=PORTS+['internal'+str(n) for n in range(125)]
    assert len(mapping(nets))==134
    for bad in [nets[:-1],nets[:-1]+[nets[0]],nets[:-2]+['case','CASE']]:
        try:mapping(bad)
        except AssertionError:continue
        raise AssertionError('bad source-label identity accepted')
    return 'passed count/missing/duplicate/case-collision controls'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['before','after','output']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and os.sched_getaffinity(0)=={0}
    assert pya.__version__=='0.30.9';a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    report=dict(status='running',controls=tests(),extraction='not run',annotation='not run',
        complete_field_coverage='failed prior pinned-method coverage; no waiver',
        substrate_binding='not assigned; no implicit VSUBS-to-VSS',physical_adoption='not run')
    frozen={};identities=[]
    try:
        for label,folder,gh,sh in [('before',a.before,PARENT,OLD_SOURCE),('after',a.after,NEW_GDS,SOURCE)]:
            gds=folder/'g1_sense_physical.gds';m=json.loads((folder/'manifest.json').read_text())
            assert sha(gds)==m['GDS_sha256']==gh and m['source_sha256']==sh
            old=pya.Layout();old.read(str(gds));original=old.cell('g1_sense_physical')
            original_regions=regions(original);frozen[label]=original_regions
            ly=pya.Layout();ly.dbu=.001;cell=ly.create_cell('g1_sense_physical')
            for key,reg in original_regions.items():
                if key[1] in [2,25]:continue
                for poly in reg.each():cell.shapes(ly.layer(*key)).insert(pya.Polygon(poly))
            probes=copy.deepcopy(m['terminal_audit']['probes']);graph=full_nets_upper(cell,probes)
            assert graph['status']=='passed' and graph['source_net_count']==134
            nets=sorted({q['net'] for q in probes});names=mapping(nets);labels=[]
            for net in nets:
                selected=None
                for q in sorted([q for q in probes if q['net']==net],key=lambda q:(q['layer'],q['device'],q['terminal'])):
                    layer=8 if q['layer']==501 else q['layer']
                    if layer not in [8,10,30,50,67,126,134]:continue
                    point=pya.DPoint(*q['point_um']).to_itype(.001)
                    witness=pya.Region(pya.Box(point.x-1,point.y-1,point.x+1,point.y+1))
                    if not original_regions.get((layer,0),pya.Region()).interacting(witness).is_empty():
                        selected=q,layer,point;break
                assert selected is not None,net
                q,layer,point=selected;assert point.x%5==point.y%5==0
                cell.shapes(ly.layer(layer,25)).insert(pya.Text(names[net],pya.Trans(point.x,point.y)))
                labels.append(dict(source_net=net,pex_label=names[net],layer=layer,point_dbu=[point.x,point.y],witness=q))
            out=a.output/label;out.mkdir();path=out/'g1_sense_pex_view.gds';ly.write(str(path))
            saved=pya.Layout();saved.read(str(path));sc=saved.cell(cell.name);sr=regions(sc)
            keys={k for k in original_regions if k[1] not in [2,25]}
            assert keys==set(sr) and all((sr[k]^original_regions[k]).is_empty() for k in keys)
            actual=[s.text.string for li in saved.layer_indexes() for s in sc.shapes(li).each() if s.is_text()]
            assert sorted(actual)==sorted(names.values())
            savedgraph=full_nets_upper(sc,copy.deepcopy(probes));assert savedgraph['status']=='passed'
            state=dict(status='passed source134 native-polygon-preserving diagnostic view',source_sha256=sh,
                parent_GDS_sha256=gh,GDS_sha256=sha(path),parent_manifest_sha256=sha(folder/'manifest.json'),
                labels=labels,native_nonannotation_XOR_um2=0,source_net_count=134,
                scope='Only extraction hierarchy/annotations changed. Not electrical terminal-plane selection or complete PEX.')
            (out/'manifest.json').write_text(json.dumps(state,indent=2)+'\n');identities.append(state)
        delta=[]
        for key in sorted(set(frozen['before'])|set(frozen['after'])):
            if key[1] in [2,25]:continue
            old=frozen['before'].get(key,pya.Region());new=frozen['after'].get(key,pya.Region())
            removed=old-new;added=new-old
            if removed.is_empty() and added.is_empty():continue
            delta.append(dict(layer=list(key),removed_um2=removed.area()*1e-6,added_um2=added.area()*1e-6,
                removed_bbox=str(removed.bbox()),added_bbox=str(added.bbox()),
                classification='requires native primitive/extrinsic ownership review; area is not capacitance'))
        assert {r['source_net'] for r in identities[0]['labels']}=={r['source_net'] for r in identities[1]['labels']}
        report.update(status='passed paired extraction-view preparation only',views=identities,changed_material=delta,
            full_MIM_model_boundary='unresolved: blackbox excludes plate fields; whitebox has no supported intrinsic/extrinsic ownership partition',
            conditional_partial_C_stability='not run; cannot certify full fast-PM acceptance')
    except Exception as exc:
        report.update(status='failed paired view preparation',error=repr(exc));raise
    finally:(a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
