#!/usr/bin/env python3
"""Preparation only: remaining16 local-stage windows and pilot-based cost estimates."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists()
base=Path(__file__).parent;manifest=json.loads(a.manifest.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pilots=base/'priority-via-local-pilots-20260922-r1';phases=json.loads((pilots/'phases.json').read_text());summary=json.loads((pilots/'summary.json').read_text())
completed={2,3,10,4,19};remaining=[i for i in range(21) if i not in completed];assert len(remaining)==16
def inside(b,w):return b[0]>=w[0] and b[1]>=w[1] and b[2]<=w[2] and b[3]<=w[3]
def intersects(b,w):return b[0]<w[2] and b[2]>w[0] and b[1]<w[3] and b[3]>w[1]
rows=[]
for i in remaining:
    stage=manifest['via_patches'][i];x,y=stage['point_um'];window=[x-6,y-6,x+6,y+6];captured=[];partial=[]
    for j,other in enumerate(manifest['via_patches']):
        boxes=[other['added_cut_bbox_um']]+[m['landing_bbox_um'] for m in other['metals']]
        if all(inside(b,window) for b in boxes):captured.append(j)
        elif any(intersects(b,window) for b in boxes):partial.append(j)
    assert i in captured
    rows.append(dict(stage_id=i,net=stage['net'],point_um=stage['point_um'],window_um=window,
        added_cut_bbox_um=stage['added_cut_bbox_um'],landing_rectangles=stage['metals'],
        all_changed_stages_fully_captured=captured,changed_stages_partially_intersected=partial,
        physical_net_membership='not run for proposed window; must re-prove every target piece and every route anchor before extraction',
        status='prepared only; geometry/PEX/matrix/AC not run'))
pilot_bytes=sum(p.stat().st_size for p in pilots.rglob('*') if p.is_file());seconds=sum(r['wall_s'] for r in phases)
result=dict(status='preparation only; no new geometry/extraction launched',candidate_sha256=manifest['candidate_sha256'],
    parent_sha256=manifest['parent_candidate_sha256'],manifest_sha256=sha(a.manifest),script_sha256=sha(Path(__file__)),
    prior_pilot_summary_sha256=sha(pilots/'summary.json'),completed_distinct_stages=sorted(completed),remaining=rows,
    cohorts=[dict(cohort=1,stage_ids=[0,1,5,6]),dict(cohort=2,stage_ids=[7,8,9,16]),
        dict(cohort=3,stage_ids=[11,12,13,14]),dict(cohort=4,stage_ids=[15,17,18,20])],
    measured_two_pilot=dict(bytes=pilot_bytes,bounded_child_seconds=seconds,paired_sites=2,real_AC_checks=16,synthetic_AC_controls=2),
    naive_same_complexity16_estimate=dict(bytes=pilot_bytes*8,bounded_child_seconds=seconds*8,
        scope='scaling estimate only; target-component count, fill density and extraction complexity are not yet inventoried'),
    prospective_staging=dict(proposal='four cohorts of at most4 paired sites, each separately authorized; no automatic expansion',
        max_output_per_cohort_bytes=33554432,existing_extract_KPEX_timeout_s=120,AC_timeout_s=30,
        expected_real_AC_checks_total=128,
        required_gates=['fresh CPU/storage headroom gate for each authorized cohort',
            'freeze all actually intersected changed rectangles, including neighboring stages; reject partial coverage as full-stage evidence',
            'source/candidate GDS hashes unchanged, every exported nontext layer XOR0 versus exact clip',
            'actual7metal physical net membership for every target component and all recorded route anchors, no text joining',
            'unique target/context/fill labels, strict parser, explicit outside-equipotential boundary',
            'finite Schur charge residual<=1e-25F; all8AC comparisons per paired site within1e-25F and explicit completion',
            'stop on timeout, parser, identity, charge, AC or output-limit failure; preserve earlier failures']),
    limitations=['Even16additional localpasses would not establish fullrouteR/C, longitudinal convergence, activity, EM or physical adoption.',
        'Stage9 and16 neighborhoods may capture both changed sites but target different nets; no single-target result may silently count as both net-load checks.'])
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='remaining'},indent=2))
