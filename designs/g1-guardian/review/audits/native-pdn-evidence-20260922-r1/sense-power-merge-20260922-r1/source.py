#!/usr/bin/env python3
"""Merge frozen SENSE supply overlay into a new native PDN assembly safely."""
import argparse
import collections
import faulthandler
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region, text_records, sha
from audit_placed_decap_domains import physical, identity
from build_native_decap_pdn import METALS, CUTS, point

POINTS = {'sense_vdda': (134, [813000, 714000]),
          'pad07_bare': (30, [1093145, 395000]),
          'pad07_external': (134, [1271500, 395000]),
          'sense_vss': (126, [805000, 714000]),
          'vss_handoff': (126, [736800, 722000]),
          'core_vdd': (134, [395000, 354660]),
          'core_vss': (134, [507000, 334660])}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--power', type=Path, required=True)
    p.add_argument('--placement', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
    faulthandler.dump_traceback_later(60, repeat=True)
    native = json.loads((a.native/'analysis.json').read_text())
    power = json.loads((a.power/'analysis.json').read_text())
    source = a.native/'fullchip_instances_unrouted.gds'
    overlay = a.power/'power_overlay.gds'
    assert native['status'].startswith('passed') and sha(source) == native['GDS_sha256']
    assert power['status'].startswith('passed') and sha(overlay) == power['overlay_sha256']
    assert sha(overlay) == 'a16aa0d622329a4d5de51b658a3d57f0e7cf1d1be1cdd4228dfead0856f56ca0'
    assert native['instances'] == 4904
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    ly = pya.Layout(); ly.read(str(source)); top = ly.top_cell()
    ol = pya.Layout(); ol.read(str(overlay)); ot = ol.top_cell()
    assert ly.dbu == ol.dbu == .001
    oldnet, oldlayers = physical(ly, top)
    onet, olayers = physical(ol, ot)
    oldprobes = {n: identity(oldnet, oldlayers[l], xy) for n, (l, xy) in POINTS.items()}
    assert None not in oldprobes.values()
    assert oldprobes['core_vss'] == oldprobes['vss_handoff']
    assert oldprobes['pad07_bare'] == oldprobes['pad07_external']
    assert len({oldprobes[n] for n in ('sense_vdda', 'pad07_bare', 'sense_vss', 'core_vss', 'core_vdd')}) == 5
    allowed = {'VDDA': {oldprobes['sense_vdda'], oldprobes['pad07_bare']},
               'VSS': {oldprobes['sense_vss'], oldprobes['core_vss']}}
    overlay_nets = {identity(onet, olayers[134], POINTS['sense_vdda'][1]): 'VDDA',
                    identity(onet, olayers[126], POINTS['sense_vss'][1]): 'VSS'}
    assert None not in overlay_nets and len(overlay_nets) == 2
    numbers = METALS + tuple(c[0] for c in CUTS)
    routes = {n: {l: pya.Region() for l in numbers} for n in allowed}
    for layer in numbers:
        probe_layer = layer if layer in METALS else next(lo for cut, lo, hi in CUTS if cut == layer)
        for poly in region(ol, ot, pya.LayerInfo(layer, 0)).each():
            found = identity(onet, olayers[probe_layer], point(poly))
            assert found in overlay_nets, (layer, str(poly), found)
            routes[overlay_nets[found]][layer].insert(poly)
    before = {str(i): region(ly, top, i) for i in ly.layer_infos()}
    old = {l: region(ly, top, pya.LayerInfo(l, 0)) for l in numbers}
    texts = text_records(ly, top)
    instances = sorted((i.cell.name, str(i.trans)) for i in top.each_inst())
    assert len(instances) == 4904 and not text_records(ol, ot)
    errors = []; checks = collections.Counter()

    def check(net, layer, polygons, reason):
        for poly in polygons.each():
            xy = point(poly); found = identity(oldnet, oldlayers[layer], xy)
            checks[reason] += 1
            if found not in allowed[net]:
                errors.append(dict(net=net, layer=layer, point=xy, actual=found, reason=reason))

    for name, added in routes.items():
        for layer in METALS:
            check(name, layer, old[layer].interacting(added[layer]), 'new metal touches native metal')
        for cut, lo, hi in CUTS:
            for layer, opposite in ((lo, hi), (hi, lo)):
                touched = old[cut].interacting(added[layer])
                check(name, opposite, old[opposite].interacting(touched), 'new metal touches old cut')
                check(name, layer, old[layer].interacting(added[cut]), 'new cut touches native metal')
    (a.output/'foreign_contact_gate.json').write_text(json.dumps(dict(
        status='failed' if errors else 'passed', errors=errors, inspected=dict(checks), old_probes=oldprobes), indent=2)+'\n')
    assert not errors, errors[:10]
    for layer in numbers:
        for name in routes:
            for poly in routes[name][layer].each():
                top.shapes(ly.layer(layer, 0)).insert(poly)
    newnet, newlayers = physical(ly, top)
    probes = {n: identity(newnet, newlayers[l], xy) for n, (l, xy) in POINTS.items()}
    assert None not in probes.values()
    assert probes['sense_vdda'] == probes['pad07_bare'] == probes['pad07_external']
    assert probes['sense_vss'] == probes['vss_handoff'] == probes['core_vss']
    assert len({probes[n] for n in ('sense_vdda', 'sense_vss', 'core_vdd')}) == 3
    decaps = json.loads((a.placement/'analysis.json').read_text())['decaps']
    count = 0
    for row in decaps:
        for name, pin in row['pins'].items():
            target = probes['core_vdd' if name == 'VDD' else 'core_vss']
            assert identity(newnet, newlayers[8], pin['placed_dbu']) == target
            assert identity(newnet, newlayers[10], pin['placed_dbu']) == target
            count += 1
    assert count == 9324
    for info in ly.layer_infos():
        expected = before.get(str(info), pya.Region()) + region(ol, ot, info)
        assert (region(ly, top, info)^expected).is_empty(), str(info)
    assert text_records(ly, top) == texts
    assert sorted((i.cell.name, str(i.trans)) for i in top.each_inst()) == instances
    output = a.output/'power_connected_native.gds'; ly.write(str(output))
    saved = pya.Layout(); saved.read(str(output)); st = saved.top_cell()
    assert text_records(saved, st) == texts
    for info in ly.layer_infos():
        assert (region(ly, top, info)^region(saved, st, info)).is_empty()
    result = dict(status='passed scoped SENSE and decap power integration; not full PDN',
                  GDS_sha256=sha(output), native_GDS_sha256=sha(source), overlay_sha256=sha(overlay),
                  script_sha256=sha(Path(__file__)), native_instances_retained=4904, probes=probes,
                  exact_additive_polygons_texts_saved_roundtrip='passed', no_foreign_contact='passed',
                  decap_pin_pairs_held=9324, placement_sha256=sha(a.placement/'analysis.json'),
                  not_run=['all remaining macro/pad supplies', 'signal routes in this candidate',
                           'stock DRC/LVS/PEX/density/antenna/currentIR/EM', 'electrical adoption'],
                  not_applicable=['complete PDN or chip qualification from scoped SENSE merge'])
    (a.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    faulthandler.cancel_dump_traceback_later()


if __name__ == '__main__':
    main()
