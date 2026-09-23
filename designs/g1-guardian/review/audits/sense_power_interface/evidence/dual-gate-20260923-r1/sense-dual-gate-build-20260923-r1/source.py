#!/usr/bin/env python3
"""Isolated additive opposite-end gate contacts; canonical source stays unchanged."""
import argparse
import copy
import json
import os
from pathlib import Path
import pya
from screen_sense_dual_gate_proposal import GM4, graph, regions, sha

STATUS = 'passed source-held dual-ended gate geometry'


def snapshot(cell):
    result = {}
    for li in cell.layout().layer_indexes():
        info = cell.layout().get_info(li)
        region = pya.Region()
        for polygon in pya.Region(cell.begin_shapes_rec(li)).each():
            region.insert(pya.Polygon(polygon))
        result[(info.layer, info.datatype)] = region.merged()
    return result


def text_snapshot(cell):
    rows = []
    for li in cell.layout().layer_indexes():
        info = cell.layout().get_info(li)
        it = cell.begin_shapes_rec(li)
        while not it.at_end():
            if it.shape().is_text():
                text = it.shape().text.transformed(it.trans())
                rows.append((info.layer, info.datatype, text.to_s()))
            it.next()
    return sorted(rows)


def hierarchy(layout):
    return {c.name: sorted((i.cell.name, i.trans.to_s(), i.a.to_s(), i.b.to_s(),
                           i.na, i.nb) for i in c.each_inst()) for c in layout.each_cell()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposal', type=Path, required=True)
    parser.add_argument('--screen', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    plan = json.loads(args.proposal.read_text())
    screen = json.loads(args.screen.read_text())
    assert screen['status'] == 'passed in-memory contact/source graph screen only'
    assert screen['proposal_sha256'] == sha(args.proposal)
    base = GM4 / 'ring-r8-evidence-20260922-r1'
    parent = base / 'sense-ring-routing-20260922-r8a'
    source = GM4.parents[1] / 'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    gds = parent / 'g1_sense_physical.gds'
    reference = base / 'sense-ring-reference-20260922-r8a/manifest.json'
    assert sha(gds) == plan['GDS_sha256'] == screen['GDS_sha256']
    assert sha(source) == plan['source_sha256'] == screen['source_sha256']
    assert sha(reference) == plan['reference_sha256']
    args.output.mkdir(parents=True)
    for name, path in [('source.py', Path(__file__)), ('proposal.json', args.proposal),
                       ('screen.json', args.screen),
                       ('graph_helper.py', Path(__file__).with_name('screen_sense_dual_gate_proposal.py'))]:
        (args.output / name).write_bytes(path.read_bytes())
    result = dict(status='running isolated geometry build', source_sha256=sha(source),
                  baseline_GDS_sha256=sha(gds), proposal_sha256=sha(args.proposal),
                  screen_sha256=sha(args.screen), script_sha256=sha(Path(__file__)),
                  not_run=['Stock main/maximal/LVS', 'Intrinsic gate resistance applicability',
                           'Zero-R parameter and waveform parity', 'Coupling/current/electrical',
                           'Fullchip adoption'])
    try:
        ly = pya.Layout(); ly.read(str(gds)); top = ly.cell('g1_sense_physical')
        before = snapshot(top); old_text = text_snapshot(top); old_hierarchy = hierarchy(ly)
        old_native = regions(top)
        manifest = json.loads((parent / 'manifest.json').read_text())
        probes = copy.deepcopy(manifest['terminal_audit']['probes'])
        net_names = {(q['device'], tuple(round(v * 1000) for v in q['point_um'])): q['net']
                     for q in probes if q['terminal'] == 'gate'}
        additions = {key: pya.Region() for key in ((5, 0), (6, 0), (8, 0))}
        ledger = []
        for row in plan['rows']:
            box = row['channel_bbox_dbu']; point = ((box[0]+box[2])//2, (box[1]+box[3])//2)
            net = net_names[row['device'], point]
            record = copy.deepcopy(row); record['source_net'] = net; ledger.append(record)
            for item in row['rectangles']:
                key = tuple(item['layer']); assert key in additions
                rectangle = pya.Box(*item['bbox_dbu'])
                additions[key].insert(rectangle); top.shapes(ly.layer(*key)).insert(rectangle)
            contact = next(q['bbox_dbu'] for q in row['rectangles'] if q['layer'] == [6, 0])
            probes.append(dict(device=row['device'], terminal='opposite_gate_M1', net=net,
                               layer=8, point_um=[(contact[0]+contact[2])*.0005,
                                                 (contact[1]+contact[3])*.0005]))
        assert len(ledger) == 835
        for region in additions.values(): region.merge()
        output_gds = args.output / 'g1_sense_physical.gds'; ly.write(str(output_gds))
        saved = pya.Layout(); saved.read(str(output_gds)); cell = saved.cell(top.name)
        after = snapshot(cell); delta = {}
        for key in set(before) | set(after):
            old = before.get(key, pya.Region()); new = after.get(key, pya.Region())
            expected = old + additions.get(key, pya.Region())
            assert (new ^ expected).is_empty(), ('Unexpected saved polygon delta', key)
            assert (old - new).is_empty(), ('Native polygon removed', key)
            delta['%d/%d' % key] = dict(added_area_dbu2=(new-old).area(), removed_area_dbu2=0)
        assert text_snapshot(cell) == old_text and hierarchy(saved) == old_hierarchy
        native = regions(cell)
        assert (native[1] ^ old_native[1]).is_empty()
        assert ((native[1] & native[5]) ^ (old_native[1] & old_native[5])).is_empty()
        assert (native[501] ^ old_native[501]).is_empty()
        hold = graph(native, probes); audit = hold[-1]
        assert audit['status'] == 'passed' and audit['source_net_count'] == 134
        assert audit['all_physical_nets'] == screen['after_graph']['all_physical_nets']
        # Every physical channel now has a fully covered contact on BOTH ends.
        for row in ledger:
            b = row['channel_bbox_dbu']; x = (b[0]+b[2])//2
            for y in (b[1]-330, b[3]+330):
                cut = pya.Region(pya.Box(x-80, y-80, x+80, y+80))
                assert (cut-native[6]).is_empty()
                assert (cut-native[5]).is_empty() and (cut-native[8]).is_empty()
        assert sha(gds) == result['baseline_GDS_sha256'] and sha(source) == result['source_sha256']
        terminal = dict(audit, probes=probes)
        manifest.update(status=STATUS, GDS_sha256=sha(output_gds), baseline_GDS_sha256=sha(gds),
                        terminal_audit=terminal, dual_gate_sites=835, source_unchanged=True,
                        stock_checks='not run', PEX='not run', adoption='not run')
        (args.output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        (args.output/'changed_shapes.json').write_text(json.dumps(ledger, indent=2)+'\n')
        result.update(status=STATUS, GDS_sha256=sha(output_gds), site_count=835,
                      source_net_count=134, physical_net_count=audit['all_physical_nets'],
                      layer_delta=delta, original_polygons_text_hierarchy='passed exact',
                      active_channel_diffusion_XOR='passed zero',
                      dual_end_contacts='passed 835 channels with two covered contact ends',
                      saved_graph=audit, manifest_sha256=sha(args.output/'manifest.json'))
    except Exception as exc:
        result.update(status='failed isolated dual-gate build', error=repr(exc)); raise
    finally:
        (args.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
