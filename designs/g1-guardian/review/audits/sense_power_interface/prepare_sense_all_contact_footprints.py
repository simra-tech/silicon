#!/usr/bin/env python3
"""Bind classified actual contact footprints; assign no model currents."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('classification', 'footprints', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    original = json.loads(args.footprints.read_text())
    summary = json.loads((args.classification/'summary.json').read_text())
    assert summary['status'] == 'passed geometry classification; unresolved model boundaries retained'
    assert summary['unclassified_count'] == 0, 'Escalate unclassified physical contacts; no invented nodes'
    data = args.classification/'contacts.json.gz'
    assert sha(data) == summary['contact_ledger_sha256']
    rows = json.loads(gzip.decompress(data.read_bytes()).decode())
    old = {tuple(r['bbox_dbu']): r for r in original['footprints']}
    catalog = []; boxes = set(); restored = set(); owner_slots = set()
    for row in rows:
        box = tuple(row['bbox_dbu']); assert box not in boxes; boxes.add(box)
        x1, y1, x2, y2 = box
        assert row['area_dbu2'] == (x2-x1)*(y2-y1)
        assert {tuple(p) for p in row['polygon_dbu']} == {(x1,y1),(x1,y2),(x2,y1),(x2,y2)}, 'Nonrectangular contact cannot be replaced with bbox'
        if box in old:
            item = old[box]; assert item['source_net'] == row['source_net']; restored.add(box)
        else:
            identifier = hashlib.sha256(json.dumps(box).encode()).hexdigest()[:20]
            item = dict(id='remaining_cont_'+identifier, bbox_dbu=list(box), contact_layer=[6,0],
                        covered_metal_layer=[8,0], source_net=row['source_net'], owners=row.get('owners', []),
                        selected_point=None, current_weights=None, equipotential_footprint_assumption=False,
                        geometry_classification=row['classification'], compact_model_attachment='not qualified')
        for owner in item['owners']: owner_slots.add((owner['device'], owner['terminal']))
        catalog.append(item)
    assert restored == set(old) and len(catalog) == summary['contacts'] == 41384
    assert len({r['id'] for r in catalog}) == len(catalog)
    for key in ('source_sha256','GDS_sha256','ledger_sha256'): assert original[key] == summary[key]
    result = dict(status='prepared all actual Cont footprint catalog; model attachment not qualified',
                  source_sha256=original['source_sha256'], GDS_sha256=original['GDS_sha256'],
                  ledger_sha256=original['ledger_sha256'], original_MOS_catalog_sha256=sha(args.footprints),
                  classification_summary_sha256=sha(args.classification/'summary.json'),
                  classification_contacts_sha256=sha(data), script_sha256=sha(Path(__file__)),
                  physical_contact_count=len(catalog), geometry_owner_slots=len(owner_slots),
                  model_attachment_qualified=False, footprints=catalog,
                  not_run=['Per-device body/BN attachment', 'MIM terminal/electrode ownership',
                           'Any compact-model weights or current injection', 'Electrical/IR/EM/adoption'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='footprints'},indent=2))


if __name__ == '__main__': main()
