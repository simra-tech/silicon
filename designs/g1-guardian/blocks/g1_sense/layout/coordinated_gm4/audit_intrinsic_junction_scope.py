#!/usr/bin/env python3
"""Bind existing native geometry and combiner controls; no extraction or simulation."""
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('junction','reference','combiner','output'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists()
    j=json.loads(a.junction.read_text())
    r=json.loads(a.reference.read_text())
    c=json.loads(a.combiner.read_text())
    assert j['reference_manifest_sha256']==sha(a.reference)
    assert r['GDS_sha256']=='9559f0d309f0c14d2f226e56138dfd0283cf2b847f0b536929565e4a739b9b02'
    assert r['source_sha256']==j['source_sha256']=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    assert c['controls'][0]['per_net_AP_conserved'] and not c['controls'][1]['per_net_AP_conserved']
    rows=[]
    for row in j['rows']:
        n=int(re.search(r'\bng=(\d+)',row['source_line'])[1])
        expected=row['source_default']
        actual=row['source_node_actual']
        avgA=(expected['as_um2']+expected['ad_um2'])/2
        avgP=(expected['ps_um']+expected['pd_um'])/2
        predicted=dict(as_um2=avgA,ad_um2=avgA,ps_um=avgP,pd_um=avgP)
        assert all(abs(actual[k]-predicted[k])<1e-8 for k in actual)
        assert row['status']==('failed' if n%2==0 else 'passed')
        rows.append(dict(device=row['device'],ng=n,stock_status=row['status'],
                         predicted_averaged_annotation=predicted,actual=actual,
                         complete_annotation_formula_match=True))
    shared=[s for s in r['strips'] if len(s['adjacent_owners'])>1]
    assert len(shared)==48
    groups=collections.defaultdict(list)
    for strip in shared:
        owners=tuple(sorted(strip['adjacent_owners']))
        assert len(owners)==2 and all(v==1 for v in strip['adjacent_owners'].values())
        groups[owners].append(strip)
    assert {owners:len(strips) for owners,strips in groups.items()}=={
        ('XOTA/XM1','XOTA/XM2'):32,('XBUF/XM1','XBUF/XM2'):8,('XREF/XM1','XREF/XM2'):8}
    owners={owner for group in groups for owner in group}
    isolated=sorted(d['device'] for d in r['devices'] if d['device'] not in owners)
    assert len(owners)==6 and len(isolated)==52
    shared_rows=[]
    for group,strips in sorted(groups.items()):
        records=[d for d in r['devices'] if d['device'] in group]
        assert len(records)==2 and records[0]['ng']==records[1]['ng']
        w,l,n=records[0]['W_um'],records[0]['L_um'],records[0]['ng']
        shared_rows.append(dict(devices=group,shared_strips=len(strips),
            physical_shared_area_um2=sum(s['area_um2'] for s in strips),
            physical_shared_perimeter_um=sum(s['perimeter_um'] for s in strips),
            nets=sorted({s['net'] for s in strips}),W_um=w,L_um=l,ng=n,
            nominal_model_RJUNSO_ohm=5000*l/w,nominal_model_RJUNS_scaled_ohm=n*5000*l/w,
            resistance_scope='Source-level parameter arithmetic; distributed physical resistance and executable internal-node voltage not measured',
            intrinsic_equivalence='not established; shared physical junction has no unique device ownership'))
    result=dict(status='passed representational failure localization; shared intrinsic equivalence not established',
        script_sha256=sha(Path(__file__)),source_sha256=r['source_sha256'],GDS_sha256=r['GDS_sha256'],
        input_sha256={k:sha(getattr(a,k)) for k in ('junction','reference','combiner')},
        averaged_annotation_matches=58,even_ng_failed_annotations=51,odd_ng_symmetric_passes=7,
        rows=rows,shared_intrinsic_groups=shared_rows,single_owner_native_devices=isolated,
        proof_scope='All native geometry/default allocation and source identities inherited from hash-bound independent saved-polygon audit. This analysis does not alter extraction or source parameters.',
        complete_PEX='not qualified',model_change='not run',simulation='not run',adoption='not run')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','single_owner_native_devices')},indent=2))


if __name__=='__main__':
    main()
