#!/usr/bin/env python3
"""Read-only source-pinned ownership of untyped contacts outside tap regions."""
import argparse
import json
import os
from pathlib import Path
import klayout.db as kdb
from export_cc_api import plain, sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--database', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    assert sha(args.database) == '6bc87673405b26f4cbc9f23c7ddf77d49c35b2ae12ec70dc0c0786f8d797856f'
    pack = Path(__file__).resolve().parents[4] / 'review/audits/coordinated-bbox-pack-586-20260922-r1.json'
    assert sha(pack) == '2663805a5180a1961850c1068b0c1c3615c010cd2ec47d38a228d65dde4800cb'
    db = kdb.LayoutVsSchematic()
    db.read(str(args.database))
    raw = {db.layer_name(i): plain(db.layer_by_index(i)) for i in db.layer_indexes()}
    typed = plain(raw['cont_poly_con'] + raw['cont_nsd_con'] + raw['cont_psd_con'])
    missing = plain(raw['cont_drw'] - typed)
    taps = plain(raw['ntap'] + raw['ptap'])
    outside = plain(missing - taps)
    rows = []
    covered = kdb.Region()
    data = json.loads(pack.read_text())
    for device in data['BGR_devices']:
        if device['kind'] != 'npn13G2':
            continue
        box = kdb.DBox(*device['bbox_um']).to_itype(.001)
        region = plain(outside & kdb.Region(box))
        assert plain(covered & region).is_empty()
        covered += region
        rows.append(dict(name=device['name'], source_line=device['source_line'],
                         bbox_um=device['bbox_um'], outside_tap_contact_area_um2=region.area() * 1e-6,
                         polygon_count=region.count()))
    assert len(rows) == 301 and plain(covered ^ outside).is_empty()
    assert all(abs(r['outside_tap_contact_area_um2'] - .5072) < 1e-12 for r in rows)
    args.output.mkdir(exist_ok=False)
    report = dict(status='passed native-bbox contact ownership; model coverage not qualified',
                  inputs={str(p): sha(p) for p in (args.database, pack, Path(__file__))},
                  outside_taps_um2=outside.area() * 1e-6, classified_HBTs=301,
                  per_HBT_area_um2=.5072, unclassified_um2=plain(outside - covered).area() * 1e-6,
                  all_native_terminal_semantics='not inferred from bounding-box ownership',
                  extraction='not run', electrical='not run', HBTs=rows)
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'HBTs'}, indent=2))


if __name__ == '__main__':
    main()
