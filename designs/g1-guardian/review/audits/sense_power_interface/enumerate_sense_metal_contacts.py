#!/usr/bin/env python3
"""Read frozen SENSE contacts without selecting a model injection plane."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import pya

HERE=Path(__file__).resolve().parent
GM4=HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ledger',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    ledger=json.loads(a.ledger.read_text())
    base=GM4/'ring-r8-evidence-20260922-r1'
    gds=base/'sense-ring-routing-20260922-r8a/g1_sense_physical.gds'
    refpath=base/'sense-ring-reference-20260922-r8a/manifest.json'
    source=GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(gds)==ledger['GDS_sha256']=='8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7'
    assert sha(refpath)==ledger['reference_manifest_sha256']
    assert sha(source)==ledger['source_sha256']=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    ref=json.loads(refpath.read_text());probes=ref['terminal_audit']['probes']
    devices={r['device']:r for r in ledger['devices']}
    ly=pya.Layout();ly.read(str(gds));top=ly.cell('g1_sense_physical');assert ly.dbu==.001
    def region(layer):
        # Explicit flat polygon copies, never a mutable recursive iterator view.
        result=pya.Region()
        for poly in pya.Region(top.begin_shapes_rec(ly.layer(layer,0))).each():result.insert(poly)
        return result.merged()
    active,poly,cont,m1=region(1),region(5),region(6),region(8)
    def point(q):return pya.DPoint(*q['point_um']).to_itype(.001)
    def bbox(b):return[b.left,b.bottom,b.right,b.top]
    def contacts(shape):
        inside=cont.inside(pya.Region(shape));rows=[]
        for cut in inside.each():
            assert (pya.Region(cut)-m1).is_empty(),'Native contact not fully covered by M1'
            rows.append(dict(bbox_dbu=bbox(cut.bbox()),area_dbu2=cut.area(),
                             external_metal_layer=8,contact_layer=6))
        assert rows,'Owned native terminal has no physical contact'
        return rows
    gp=[q for q in probes if q['terminal']=='gate']
    dp=[q for q in probes if q['layer']==501 and q['terminal']in('source','drain','s','d')]
    gates=[]
    for channel in(active&poly).each():
        b=channel.bbox();qs=[q for q in gp if b.contains(point(q))];assert len(qs)==1
        q=qs[0];assert devices[q['device']]['terminal_nets']['G']==q['net']
        gates.append((b,q['device'],q['net']))
    assert len(gates)==len(gp)==835
    rows=[];gate_channels=0
    for shape in poly.each():
        owned=[(b,name,net)for b,name,net in gates if shape.inside(b.center())]
        if not owned:continue
        nets={net for b,name,net in owned};assert len(nets)==1,'Poly merges source-defined gate nets'
        gate_channels+=len(owned)
        rows.append(dict(kind='gate_poly_component',source_net=next(iter(nets)),
            owners=dict(collections.Counter(name for b,name,net in owned)),
            native_bbox_dbu=bbox(shape.bbox()),contacts=contacts(shape)))
    assert gate_channels==835
    strips=0
    for shape in(active-poly).each():
        b=shape.bbox()
        adjacent=[(g,name)for g,name,net in gates if g.bottom==b.bottom and g.top==b.top and(g.left==b.right or g.right==b.left)]
        if not adjacent:continue
        qs=[q for q in dp if b.contains(point(q))];assert len(qs)==1 and 1<=len(adjacent)<=2
        net=qs[0]['net'];owners=collections.Counter(name for g,name in adjacent);roles={}
        for name in owners:
            role=[r for r in('D','S')if devices[name]['terminal_nets'][r]==net];assert len(role)==1
            roles[name]=role[0]
        rows.append(dict(kind='diffusion_strip',source_net=net,owners=dict(owners),owner_roles=roles,
            native_bbox_dbu=bbox(b),area_dbu2=shape.area(),perimeter_dbu=shape.perimeter(),contacts=contacts(shape)))
        strips+=1
    assert strips==len(dp)==893
    assert sha(gds)==ledger['GDS_sha256'] and sha(source)==ledger['source_sha256']
    result=dict(status='passed read-only native contact enumeration; model attachment not qualified',
        source_sha256=sha(source),GDS_sha256=sha(gds),reference_manifest_sha256=sha(refpath),
        ledger_sha256=sha(a.ledger),script_sha256=sha(Path(__file__)),KLayout=pya.__version__,
        channels=835,diffusion_strips=strips,gate_components=len(rows)-strips,
        physical_contact_records=sum(len(r['contacts'])for r in rows),rows=rows,
        selected_injection_points=[],source_or_geometry_modified=False,
        net_membership_scope='Exact source orientations plus existing independently qualified 134-net witness graph; no new full graph extraction',
        not_run=['Distributed compact-model terminal boundary','Per-device body/BN attachment',
                 'MIM electrode/model series ownership','Metal R extraction','Zero-R waveform parity','Adoption'])
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2))


if __name__=='__main__':main()
