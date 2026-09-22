#!/usr/bin/env python3
"""Exact completed design-control evidence inventory, excluding active proposals."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
def main():
    paths=[HERE/name for name in ['prepare_coordinated_candidate.py','run_coordinated_probe.py',
           'analyze_coordinated_stage.py','inventory_coordinated_stage.py',
           'COORDINATED_DESIGN_CONTROL_20260922.md','coordinated_design_control_20260922_r1.json',
           'coordinated_design_control_20260922_r2.json']]
    for name in ['candidates/bgr_loop24_qref4_r253p465','runs/bgr_loop24q4_nominal_20260922_r1','runs/bgr_loop24q4_probe_20260922_r1']:
        paths.extend(p for p in (HERE/name).rglob('*') if p.is_file())
    rows=[{'path':str(p.relative_to(HERE)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]
    out=HERE/'coordinated_stage_evidence_20260922_r1.json'
    assert not out.exists()
    result={'status':'completed evidence inventory, candidate unadopted','file_count':len(rows),
            'total_bytes':sum(r['bytes'] for r in rows),'files':rows,
            'excluded':'Active BGR remedy/floorplan/next-stage proposals; no private notes or machine-specific host paths.',
            'dependencies':['Existing run_campaign.py and original baseline source hashes are retained in run/candidate snapshots.',
                            'VOLTAGE_MODEL_SCOPE_20260922.md identifies pinned public process/model guidance.',
                            'Root owns flow runtime/image qualification; physical fit and further campaigns not run.']}
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'file_count':len(rows),'total_bytes':result['total_bytes']}))
if __name__=='__main__':main()
