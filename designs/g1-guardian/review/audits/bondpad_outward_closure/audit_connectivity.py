#!/usr/bin/env python3
"""Re-probe all actual terminal windows and moved pad ports in one fresh graph."""
import argparse
import collections
import json
import os
from pathlib import Path
import sys
import pya

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flat_metal_connectivity import flat_physical
from audit_placed_decap_domains import identity
from audit_native_terminal_connectivity import CUTS, LAYERS, SUPPLIES
from place_closed_analog import region, sha

OLD_OBS_SHA = '6204e7d681e4d01eb916ae6616edc9573467c7c38cdbc60ddb108b54bd25737c'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('candidate', 'observations', 'old-odb', 'new-odb', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
    assert sha(a.observations) == OLD_OBS_SHA
    old = json.loads(a.observations.read_text())
    meta = json.loads((a.candidate / 'analysis.json').read_text())
    odb = json.loads((a.new_odb / 'analysis.json').read_text())
    old_odb = json.loads((a.old_odb / 'analysis.json').read_text())
    assert old['LEF_binding_sha256'] == sha(a.old_odb / 'analysis.json')
    assert odb['LEFs'] == old_odb['LEFs']
    assert odb['status'].startswith('passed') and odb['source_DEF_sha256'] == meta['derived_DEF_sha256']
    source = a.candidate / 'pad_outward_native.gds'
    assert meta['status'].startswith('passed') and sha(source) == meta['GDS_sha256']
    moves = {r['instance']: r for r in meta['pad_moves']}
    old_lines = (a.old_odb / 'roundtrip.tsv').read_text().splitlines()
    new_lines = (a.new_odb / 'roundtrip.tsv').read_text().splitlines()
    old_conn = sorted(s for s in old_lines if not s.startswith('INST\t'))
    new_conn = sorted(s for s in new_lines if not s.startswith('INST\t'))
    assert old_conn == new_conn
    instances = {r.split('\t')[1]: r.split('\t') for r in new_lines if r.startswith('INST\t')}
    for line in old_lines:
        f = line.split('\t')
        if f[0] != 'INST':
            continue
        wanted = list(f)
        if f[1] in moves:
            wanted[4:8] = list(map(str, moves[f[1]]['new_bbox_dbu']))
        assert instances[f[1]] == wanted
    expected = {(r.split('\t')[1], r.split('\t')[2], r.split('\t')[3])
                for r in new_lines if r.startswith('CONN\t') and r.split('\t')[2] != 'PIN'}
    assert expected == {(r['net'], r['instance'], r['pin']) for r in old['observations']}
    assert len(expected) == 10222 and not old['errors'] and not old['split_components']
    ly = pya.Layout(); ly.read(str(source)); top = ly.top_cell()
    net, metal, held = flat_physical(ly, top)
    actual = {layer: region(ly, top, pya.LayerInfo(layer, 0)) for layer in LAYERS.values()}
    observations = []; errors = []; by_logical = collections.defaultdict(set)
    by_physical = collections.defaultdict(set)
    for row in old['observations']:
        clusters = set(); windows = []
        shift = moves[row['instance']]['shift_dbu'] if row['instance'] in moves else (0, 0)
        for window in row['windows']:
            layer = window['layer']; box = pya.Box(*window['bbox']).transformed(pya.Trans(*shift))
            overlap = actual[layer] & pya.Region(box); found = set()
            for polygon in overlap.each():
                point = next(polygon.each_point_hull())
                for probe_layer in CUTS.get(layer, (layer,)):
                    key = identity(net, metal[probe_layer], [point.x, point.y])
                    if key is None:
                        errors.append(dict(instance=row['instance'], pin=row['pin'], error='off-metal', layer=probe_layer))
                    else:
                        found.add(key)
            clusters.update(found)
            windows.append(dict(layer=layer, bbox=[box.left, box.bottom, box.right, box.top],
                                native_area_um2=overlap.area() * 1e-6,
                                clusters=[list(v) for v in sorted(found)]))
        if not clusters:
            errors.append(dict(instance=row['instance'], pin=row['pin'], error='empty terminal'))
        observations.append(dict(net=row['net'], instance=row['instance'], pin=row['pin'],
                                 clusters=[list(v) for v in sorted(clusters)], windows=windows))
        by_logical[row['net']].update(clusters)
        for key in clusters:
            by_physical[key].add(row['net'])
    shorts = [dict(component=list(k), logical_nets=sorted(v)) for k, v in by_physical.items() if len(v) > 1]
    splits = {k: len(v) for k, v in by_logical.items() if len(v) != 1}
    ports = []; port_errors = []
    obym = {r['instance']: r for r in observations if r['instance'] in moves}
    for name, move in sorted(moves.items()):
        box = pya.Box(*move['new_bbox_dbu']); overlap = actual[134] & pya.Region(box)
        parts = set()
        for polygon in overlap.each():
            point = next(polygon.each_point_hull())
            key = identity(net, metal[134], [point.x, point.y])
            if key is not None:
                parts.add(key)
        matching = {tuple(v) for v in obym[name]['clusters']}
        passed = (pya.Region(box) - actual[134]).is_empty() and len(parts) == 1 and parts == matching
        port = dict(instance=name, pin=move['logical_net'], bbox_dbu=move['new_bbox_dbu'],
                    opening_center_um=move['new_opening_center_um'],
                    components=[list(v) for v in sorted(parts)], status='passed' if passed else 'failed')
        ports.append(port)
        if not passed:
            port_errors.append(port)
    a.output.mkdir(parents=True); (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='failed raw connectivity' if errors or shorts or splits else 'passed raw connectivity',
                  GDS_sha256=sha(source), script_sha256=sha(Path(__file__)), LEF_binding_sha256=sha(a.new_odb / 'analysis.json'),
                  old_observations_sha256=OLD_OBS_SHA, logical_nets=len(by_logical),
                  source_roundtrip_sha256=sha(a.new_odb / 'roundtrip.tsv'),
                  exact_old_source_connections='passed', exact_only_24_placement_changes='passed',
                  unchanged_LEF_inputs='passed', extraction_scope='fresh flat instance-resolved geometry; no label joining',
                  terminal_observations=len(observations), errors=errors, unexpected_net_merges=shorts,
                  split_components=splits, signal_splits={k: v for k, v in splits.items() if k not in SUPPLIES},
                  supply_distinct_roots=len({next(iter(by_logical[k])) for k in SUPPLIES if len(by_logical[k]) == 1}),
                  external_BTerms_not_probed=old['external_BTerms_not_probed'], observations=observations,
                  physical_ports=ports, physical_port_errors=port_errors,
                  not_run=['source alias disposition in separate audit', 'device-aware fullchip LVS', 'currentIR/EM', 'pad RC'],
                  not_applicable=['virtual/name-based net joins'])
    (a.output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'observations'}, indent=2))
    # Raw eight expected analog aliases deliberately remain FAILED here.
    assert not errors and not splits and not port_errors and result['supply_distinct_roots'] == 5
    assert len(shorts) == 8 and len(ports) == 24 and len({r['pin'] for r in ports}) == 22


if __name__ == '__main__':
    main()
