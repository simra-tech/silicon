#!/usr/bin/env python3
"""Quantify routed-metal overlap of source resistor bodies absent from CC poly.

Geometry only: no capacitance estimate, body-potential assignment or source edit.
"""
import argparse
import json
import os
from pathlib import Path
import re
import klayout.db as kdb
from export_cc_api import plain, sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gds', type=Path, required=True)
    ap.add_argument('--database', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    assert sha(args.gds) == '0083eabb0f730b2cb27eeb0bda1ac8f173a21e03e2aa5a329b01ef5cba21b3ed'
    assert sha(args.database) == '6bc87673405b26f4cbc9f23c7ddf77d49c35b2ae12ec70dc0c0786f8d797856f'
    pack_path = Path(__file__).resolve().parents[4] / 'review/audits/coordinated-bbox-pack-586-20260922-r1.json'
    assert sha(pack_path) == '2663805a5180a1961850c1068b0c1c3615c010cd2ec47d38a228d65dde4800cb'
    pack = json.loads(pack_path.read_text())
    ly = kdb.Layout()
    ly.read(str(args.gds))
    top = ly.top_cell()
    get = lambda pair: plain(kdb.Region(top.begin_shapes_rec(ly.layer(*pair))))
    poly = get((5, 0))
    markers = plain(get((128, 0)) + get((24, 0)))
    # Native rppd/rhigh bodies are drawn on PolyRes 128/0, not GatPoly 5/0.
    # The original pilot/native parity verifies each body's source W and L.
    bodies = get((128, 0))
    db = kdb.LayoutVsSchematic()
    db.read(str(args.database))
    raw = {db.layer_name(i): plain(db.layer_by_index(i)) for i in db.layer_indexes()}
    assert plain(raw['poly_con'] ^ plain(poly - markers)).is_empty()
    assert plain(raw['poly_con'] & bodies).is_empty()
    metals = {name: get(pair) for name, pair in [('M1', (8, 0)), ('M2', (10, 0)), ('M3', (30, 0)),
                                               ('M4', (50, 0)), ('M5', (67, 0))]}
    covered = kdb.Region()
    rows = []
    for device in pack['BGR_devices']:
        if device['kind'] not in ('rppd', 'rhigh'):
            continue
        region = plain(bodies & kdb.Region(kdb.DBox(*device['bbox_um']).to_itype(ly.dbu)))
        assert plain(covered & region).is_empty()
        covered += region
        fields = dict(re.findall(r'\b(w|l)=([0-9.]+)u\b', device['source_line']))
        assert set(fields) == {'w', 'l'} and not region.is_empty()
        rows.append(dict(name=device['name'], source_line=device['source_line'],
                         source_WL_um2=float(fields['w']) * float(fields['l']),
                         marker_body_um2=region.area() * ly.dbu**2,
                         metal_over_body_um2={name: plain(region & metal).area() * ly.dbu**2 for name, metal in metals.items()}))
        assert abs(rows[-1]['source_WL_um2'] - rows[-1]['marker_body_um2']) < 1e-9
    assert len(rows) == 399 and plain(bodies ^ covered).is_empty()
    args.output.mkdir(exist_ok=False)
    totals = {name: plain(bodies & metal).area() * ly.dbu**2 for name, metal in metals.items()}
    receipt = dict(status='passed geometric domain audit; omitted-field electrical effect not qualified',
                   inputs={str(p): sha(p) for p in (args.gds, args.database, pack_path, Path(__file__))},
                   resistor_count=399, body_area_um2=bodies.area() * ly.dbu**2,
                   source_WL_area_um2=sum(r['source_WL_um2'] for r in rows),
                   extracted_poly_body_intersection_um2=0, raw_rule_geometry_XOR_um2=0,
                   metal_over_body_area_um2=totals,
                   affected_resistors={name: sum(r['metal_over_body_um2'][name] > 0 for r in rows) for name in metals},
                   intrinsic_model='unchanged r3_cmc includes substrate area/perimeter capacitance; no external cross-metal port',
                   body_to_crossing_metal_CC='not represented by excluded resistor bodies in current geometric CC inputs',
                   coupled_body_potential='not assigned; distributed resistor potential is not an arbitrary source endpoint',
                   field_magnitude_bound='not run', electrical_effect='not run', adoption='not run', rows=rows)
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (args.output / 'summary.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
