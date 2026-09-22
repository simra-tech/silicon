#!/usr/bin/env python3
"""Independent saved-layout check of the Region snapshot-only repair."""
import hashlib
import json
from pathlib import Path
import pya


def main():
    root = Path(__file__).resolve().parents[6]
    old = root/'build/scratch/bgr-mos-contact-prototypes-20260922-r1'
    new = root/'build/scratch/bgr-mos-contact-prototypes-20260922-r2'
    records = []
    for path in sorted(new.glob('*.gds')):
        a, b = pya.Layout(), pya.Layout()
        a.read(str(old/path.name)); b.read(str(path))
        assert a.dbu == b.dbu == .001
        layers = sorted(set((x.layer, x.datatype) for x in a.layer_infos()+b.layer_infos()))
        changes, texts = [], []
        for layer, datatype in layers:
            ra = pya.Region(a.top_cell().begin_shapes_rec(a.layer(layer, datatype)))
            rb = pya.Region(b.top_cell().begin_shapes_rec(b.layer(layer, datatype)))
            changes.append(dict(layer=layer, datatype=datatype, xor_dbu2=(ra^rb).area()))
            inventories = []
            for layout in [a, b]:
                it = layout.top_cell().begin_shapes_rec(layout.layer(layer, datatype))
                found = []
                while not it.at_end():
                    if it.shape().is_text():
                        found.append(str(it.shape().text.transformed(it.trans())))
                    it.next()
                inventories.append(sorted(found))
            texts.append(inventories[0] == inventories[1])
        cdl_equal = (old/path.with_suffix('.cdl').name).read_bytes() == path.with_suffix('.cdl').read_bytes()
        records.append(dict(name=path.stem, layers=changes, texts_equal=all(texts), cdl_equal=cdl_equal,
                            passed=all(x['xor_dbu2'] == 0 for x in changes) and all(texts) and cdl_equal))
    manifest = json.loads((new/'manifest.json').read_text())
    checks = dict(eight_prototypes=len(records)==8, geometry_and_cdl_unchanged=all(x['passed'] for x in records),
                  positive_body_ties=all(x['added_body_Activ_um2'] > 0 for x in manifest['prototypes']),
                  reserved_bbox=manifest['all_contact_bbox_reservations_passed'],
                  original_sources=manifest['original_sources_unchanged'])
    output = dict(status='passed' if all(checks.values()) else 'failed', checks=checks, records=records,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  r1_postmutation_diffusion_audit='failed: live Region snapshot',
                  stock_DRC_LVS='not run', per_source_terminal_mapping='not run')
    target = new/'revision-comparison.json'
    assert not target.exists()
    target.write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output, indent=2))
    assert all(checks.values())


if __name__ == '__main__':
    main()
