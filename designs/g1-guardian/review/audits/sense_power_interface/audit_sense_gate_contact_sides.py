#!/usr/bin/env python3
"""Audit native contact-side evidence; do not infer a changed compact model."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
GM4=HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contacts',type=Path,required=True)
    p.add_argument('--semantics',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    c=json.loads(a.contacts.read_text());s=json.loads(a.semantics.read_text())
    refpath=GM4/'ring-r8-evidence-20260922-r1/sense-ring-reference-20260922-r8a/manifest.json'
    ref=json.loads(refpath.read_text());assert sha(refpath)==c['reference_manifest_sha256']
    assert c['status'].startswith('passed')and s['status'].startswith('passed')
    specs={d['device']:d for d in ref['devices']}
    gp=[r for r in ref['terminal_audit']['probes']if r['terminal']=='gate']
    components=[];channels=[]
    for row in c['rows']:
        if row['kind']!='gate_poly_component':continue
        b=row['native_bbox_dbu']
        qs=[q for q in gp if q['device']in row['owners'] and b[0]<=round(q['point_um'][0]*1000)<=b[2]
            and b[1]<=round(q['point_um'][1]*1000)<=b[3]]
        assert len(qs)==sum(row['owners'].values())
        ys={round(q['point_um'][1]*1000)for q in qs};assert len(ys)==1
        y=next(iter(ys));d=specs[qs[0]['device']];hw=round(d['W_um']/d['ng']*500)
        sides={'south'if cut['bbox_dbu'][3]<y-hw else'north'if cut['bbox_dbu'][1]>y+hw else'overlap'
               for cut in row['contacts']}
        assert len(sides)==1 and 'overlap'not in sides
        components.append(dict(owners=row['owners'],native_bbox_dbu=b,
            all_component_contacts_on_side=next(iter(sides)),contact_count=len(row['contacts'])))
        for q in qs:
            x=round(q['point_um'][0]*1000);hl=round(specs[q['device']]['L_um']*500)
            aligned=[]
            for cut in row['contacts']:
                l,bottom,r,top=cut['bbox_dbu'];cx=(l+r)/2;cy=(bottom+top)/2
                if x-hl<=cx<=x+hl and hw<abs(cy-y)<=hw+1000:
                    aligned.append(dict(side='north'if cy>y else'south',
                        active_edge_center_offset_dbu=abs(cy-y)-hw,contact_bbox_dbu=cut['bbox_dbu']))
            assert len(aligned)==1 and aligned[0]['active_edge_center_offset_dbu']==330
            channels.append(dict(device=q['device'],gate_witness_um=q['point_um'],contact=aligned[0]))
    assert len(channels)==835 and len(components)==244
    assert len({(r['device'],tuple(r['gate_witness_um']))for r in channels})==835
    wrapper=s['excerpts']['libs.tech/ngspice/models/sg13g2_moshv_mod.lib']
    ngcon=[r for r in wrapper if 'ngcon=2'in r['text']];assert ngcon
    result=dict(status='passed native one-sided contact inventory; model NGCON applicability unresolved',
        GDS_sha256=c['GDS_sha256'],source_sha256=c['source_sha256'],
        contacts_sha256=sha(a.contacts),semantics_sha256=sha(a.semantics),reference_sha256=sha(refpath),
        script_sha256=sha(Path(__file__)),channels=channels,components=components,
        channel_sides=dict(collections.Counter(r['contact']['side']for r in channels)),
        component_sides=dict(collections.Counter(r['all_component_contacts_on_side']for r in components)),
        source_wrapper_ngcon=2,wrapper_ngcon_lines=ngcon,
        interpretation='Native contacts are one-sided, whereas source wrapper NGCON=2 enters finite gate resistance. Physical correspondence and any remedy require review; no model change inferred automatically.',
        no_geometry_source_cards_modified=True,
        not_run=['Native gate-sheet electrical equivalence','Changed NGCON simulation','Double-ended geometry remedy','Distributed terminal adoption'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in('channels','components','wrapper_ngcon_lines')},indent=2))


if __name__=='__main__':main()
