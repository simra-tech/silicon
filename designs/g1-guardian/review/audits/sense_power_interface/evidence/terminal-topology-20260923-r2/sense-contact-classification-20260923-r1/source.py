#!/usr/bin/env python3
"""Classify actual native contact geometry without assigning model currents."""
import argparse
import collections
import gzip
import json
import os
from pathlib import Path
import time
import klayout.db as kdb
import extract_sense_contact_topology as mesh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('footprints', 'ledger', 'topology', 'output'):
        parser.add_argument('--'+key, required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert kdb.__version__ == '0.30.9'
    sha, dump = mesh.engine.base.sha, mesh.engine.base.dump
    ledger = json.loads(args.ledger.read_text()); known = json.loads(args.footprints.read_text())
    prior = json.loads((args.topology/'summary.json').read_text())
    observations = json.loads((args.topology/'topology.json').read_text())['observations']
    assert prior['status'] == 'passed geometry-only all-contact metal-R topology'
    assert prior['footprint_sha256'] == sha(args.footprints)
    assert known['ledger_sha256'] == sha(args.ledger)
    gds = mesh.GM4/'ring-r8-evidence-20260922-r1/sense-ring-routing-20260922-r8a/g1_sense_physical.gds'
    assert sha(gds) == prior['GDS_sha256'] == ledger['GDS_sha256']
    source = mesh.GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source) == prior['source_sha256'] == ledger['source_sha256']
    args.output.mkdir(parents=True)
    (args.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running native remaining-contact classification', source_sha256=sha(source),
                  GDS_sha256=sha(gds), script_sha256=sha(Path(__file__)), ledger_sha256=sha(args.ledger),
                  topology_summary_sha256=sha(args.topology/'summary.json'),
                  compact_model_applicability='not run', current_assignment='not run', adoption='not run')
    start = time.monotonic()
    try:
        layout = kdb.Layout(); layout.read(str(gds)); cell = layout.cell('g1_sense_physical')
        regions = {name: mesh.materialize(cell, pair) for name, pair in mesh.engine.PAIRS.items()}
        hold = mesh.native_graph(regions); native, layers = hold[1:]
        names = collections.defaultdict(set)
        for row in observations:
            if row.get('source_net') is not None: names[row['native_component']].add(row['source_net'])
        # Rebind exact physical witnesses; do not depend on prior cluster numbering.
        current_names = collections.defaultdict(set)
        for slot in ledger['slots']:
            for witness in slot.get('witnesses', []):
                layer = next((n for n, p in mesh.engine.PAIRS.items() if p[0] == witness['layer']), None)
                if layer is None: continue
                point = kdb.Point(*(round(v*1000) for v in witness['point_um']))
                net = native.probe_net(layers[layer], point); assert net is not None
                current_names[net.cluster_id].add(slot['source_net'])
        for row in known['footprints']:
            net = native.probe_net(layers['M1'], kdb.Box(*row['bbox_dbu']).center()); assert net is not None
            current_names[net.cluster_id].add(row['source_net'])
        assert len(current_names) == 134 and all(len(v) == 1 for v in current_names.values())
        active = mesh.materialize(cell, (1, 0)); poly = mesh.materialize(cell, (5, 0))
        cont = mesh.materialize(cell, (6, 0)); resbody = mesh.materialize(cell, (128, 0))
        heads = list((poly-resbody).each()); diffusions = list((active-poly).each())
        resslots = [s for s in ledger['slots'] if s['model'] == 'rppd' and s['terminal'] != 'BN']
        head_owners = collections.defaultdict(list)
        for slot in resslots:
            assert len(slot['witnesses']) == 1
            p = kdb.Point(*(round(v*1000) for v in slot['witnesses'][0]['point_um']))
            matched = [i for i, shape in enumerate(heads) if shape.inside(p)]
            assert len(matched) == 1, ('Resistor metal witness does not prove unique poly head', slot['device'], slot['terminal'], matched)
            head_owners[matched[0]].append(dict(device=slot['device'], terminal=slot['terminal'], source_net=slot['source_net']))
        tap_witnesses = {}
        for slot in ledger['slots']:
            for witness in slot.get('shared_tap_witnesses', []):
                key = (witness['device'], witness['terminal'], witness['net'], tuple(witness['point_um']))
                tap_witnesses[key] = witness
        tap_owners = collections.defaultdict(list)
        for witness in tap_witnesses.values():
            p = kdb.Point(*(round(v*1000) for v in witness['point_um']))
            matched = [i for i, shape in enumerate(diffusions) if shape.inside(p)]
            assert len(matched) == 1, ('Tap witness not on unique native diffusion', witness, matched)
            tap_owners[matched[0]].append(witness)
        known_by_box = {tuple(r['bbox_dbu']): r for r in known['footprints']}
        rows = []; unclassified = []; rescovered = set(); known_count = 0
        for cut in cont.each():
            box = cut.bbox(); coords = [box.left, box.bottom, box.right, box.top]
            assert (kdb.Region(cut)-regions['M1']).is_empty(), ('Cont not fully covered by M1', coords)
            point = mesh.inside_point(cut); net = native.probe_net(layers['M1'], point); assert net is not None
            assert net.cluster_id in current_names
            source_net = next(iter(current_names[net.cluster_id]))
            row = dict(bbox_dbu=coords, polygon_dbu=[[p.x, p.y] for p in cut.each_point_hull()],
                       area_dbu2=cut.area(), source_net=source_net, model_attachment='not qualified')
            if tuple(coords) in known_by_box:
                original = known_by_box[tuple(coords)]; assert source_net == original['source_net']
                row.update(classification='catalogued MOS contact', owners=original['owners']); known_count += 1
            else:
                h = [i for i, shape in enumerate(heads) if shape.inside(point)]
                d = [i for i, shape in enumerate(diffusions) if shape.inside(point)]
                assert not (h and d), ('Cont on both active and poly', coords)
                if len(h) == 1 and head_owners[h[0]]:
                    owners = head_owners[h[0]]; assert len(owners) == 1
                    assert owners[0]['source_net'] == source_net
                    assert (kdb.Region(cut)-kdb.Region(heads[h[0]])).is_empty()
                    row.update(classification='source-bound resistor poly head', owners=owners)
                    rescovered.add((owners[0]['device'], owners[0]['terminal']))
                elif len(d) == 1 and tap_owners[d[0]]:
                    witnesses = tap_owners[d[0]]; assert all(w['net'] == source_net for w in witnesses)
                    assert (kdb.Region(cut)-kdb.Region(diffusions[d[0]])).is_empty()
                    row.update(classification='source-net-bound shared tap conductor; no per-device body or BN assignment',
                               tap_witnesses=witnesses)
                else:
                    row.update(classification='unassigned native contact', poly_component_count=len(h), active_component_count=len(d))
                    unclassified.append(coords)
            rows.append(row)
        assert known_count == len(known['footprints']) == 19384
        assert len(rows) == cont.count()
        payload = gzip.compress(json.dumps(rows, allow_nan=False).encode(), mtime=0)
        (args.output/'contacts.json.gz').write_bytes(payload)
        result.update(status='passed geometry classification; unresolved model boundaries retained',
                      contacts=len(rows), known_MOS_contacts=known_count,
                      counts=dict(collections.Counter(r['classification'] for r in rows)),
                      resistor_head_slots_covered=len(rescovered), resistor_head_slots_total=len(resslots),
                      unclassified_count=len(unclassified), unclassified_bboxes_dbu=unclassified,
                      contact_ledger_sha256=sha(args.output/'contacts.json.gz'),
                      not_run=['Per-device body/BN spreading attachment', 'MIM electrode resistance ownership',
                               'Contact material resistance allocation', 'Compact-model weights/current injection',
                               'ZeroR parameter and waveform parity', 'Electrical/IR/EM/adoption'])
        assert sha(gds) == result['GDS_sha256'] and sha(source) == result['source_sha256']
    except Exception as exc:
        result.update(status='failed contact classification', error=repr(exc)); raise
    finally:
        result['wall_s'] = time.monotonic()-start
        dump(args.output/'summary.json', result); print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
