#!/usr/bin/env python3
"""Actual native emitter, precision-head and shared-star access inventory."""
import argparse
import collections
import json
import os
from pathlib import Path
import sys
import pya

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(HERE.parent / 'coordinated_full_closure'))
from export_cc_api import sha, dump, plain


def coords(box):
    return [box.left, box.bottom, box.right, box.top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gds', type=Path, required=True)
    ap.add_argument('--currents', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1
    assert sha(args.gds) == '943fa1787490571ebf0120c303b9326ac9290b49c70df9a73b5bea7014093f7a'
    args.output.mkdir(exist_ok=False)
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    ledger_path = ROOT / 'build/scratch/bgr-hbt-fullbank-20260922-r2/route_ledger.json'
    resistor_path = ROOT / 'build/scratch/bgr-resistor-bank-pilot-20260922-r2/manifest.json'
    pdk = Path('/foss/pdks/ihp-sg13g2')
    definitions = pdk / 'libs.tech/klayout/tech/lvs/rule_decks/layers_definitions.lvs'
    connections = pdk / 'libs.tech/klayout/tech/lvs/rule_decks/bjt_connections.lvs'
    assert 'emwind_drw = get_polygons(33, 0)' in definitions.read_text()
    assert 'connect(npn13G2_e_pin, emwind_drw)' in connections.read_text()
    assert 'connect(emwind_drw, metal1_con)' in connections.read_text()
    ledger = json.loads(ledger_path.read_text())
    resistor = json.loads(resistor_path.read_text())
    currents = json.loads(args.currents.read_text())
    current_by_id = {r['source_id']: r for r in currents['devices']}
    ly = pya.Layout()
    ly.read(str(args.gds))
    top = ly.top_cell()
    layers = {name: plain(pya.Region(top.begin_shapes_rec(ly.layer(number, 0)))) for name, number in
              [('M1', 8), ('M2', 10), ('M3', 30), ('M4', 50), ('Via1', 19), ('Via2', 29), ('Cont', 6), ('EmWind', 33)]}
    polys = {name: list(region.each()) for name, region in layers.items()}
    def containing(layer, xy):
        hits = [p for p in polys[layer] if p.inside(pya.Point(*xy))]
        assert len(hits) == 1, (layer, xy, len(hits))
        return hits[0]
    def within(layer, region):
        result = []
        for polygon in polys[layer]:
            overlap = plain(pya.Region(polygon) & region)
            if not overlap.is_empty():
                assert plain(pya.Region(polygon) - region).is_empty(), (layer, str(polygon))
                result.append(polygon)
        return result
    receipt = dict(status='running', numerical_full_R='not run', adoption='not run', seed='not applicable')
    dump(args.output / 'summary.json', receipt)
    try:
        emitters = []
        selected = [p for p in ledger['probes'] if p['terminal'] == 'E' and p['role'].startswith('return_')]
        assert len(selected) == 76
        for probe in selected:
            xy = probe['point_dbu']
            m1, m2 = containing('M1', xy), containing('M2', xy)
            emitter = containing('EmWind', xy)
            assert emitter.area() == 63000
            access = plain(pya.Region(m1) & pya.Region(m2))
            cuts = within('Via1', access)
            assert len(cuts) == 8 and all(p.area() == 190 * 190 for p in cuts)
            cont = plain(layers['Cont'] & pya.Region(m1))
            assert cont.is_empty()
            injection = current_by_id[probe['instance']]['inferred_injection_into_wire_A']['E']
            emitters.append(dict(source=probe['instance'], role=probe['role'], probe_dbu=xy,
                M1_electrode_bbox_dbu=coords(m1.bbox()), M1_electrode_area_um2=m1.area() * 1e-6,
                M2_access_bbox_dbu=coords(m2.bbox()), EmWind_bbox_dbu=coords(emitter.bbox()),
                native_Via1_boxes_dbu=[coords(p.bbox()) for p in cuts], native_Via1_count=8,
                emitter_Cont_area_um2=0, injection_A=injection,
                LEF_parallel_Via1_ohm=20 / 8, KPEX_parallel_Via1_ohm=9 / 8,
                LEF_parallel_Via1_drop_V=injection * 20 / 8, KPEX_parallel_Via1_drop_V=injection * 9 / 8))
        heads = []
        for probe in resistor['terminal_probes']:
            name = probe['instance']
            if (name == 'XR16' or name.startswith('XR16_')) and probe['net'] == 'vss':
                assert probe['terminal'] == 0
                xy = [round(v * 1000) for v in probe['point_um']]
                m1 = containing('M1', xy)
                cuts = within('Via1', pya.Region(m1))
                contacts = within('Cont', pya.Region(m1))
                assert len(cuts) == 2 and contacts
                heads.append(dict(source=name, M1_probe_dbu=xy, M1_head_bbox_dbu=coords(m1.bbox()),
                    Via1_boxes_dbu=[coords(p.bbox()) for p in cuts], Cont_boxes_dbu=[coords(p.bbox()) for p in contacts],
                    injection_A=current_by_id[name]['inferred_injection_into_wire_A']['1']))
        assert len(heads) == 24
        common = []
        for y in (15060, 16260):
            expected = [[15905, y + d - 95, 16095, y + d + 95] for d in (-210, 210)]
            for box in expected:
                assert (pya.Region(pya.Box(*box)) - layers['Via2']).is_empty()
            neighborhood = pya.Region(pya.Box(15600, y - 420, 16400, y + 420))
            cuts = within('Via2', neighborhood)
            assert sorted(coords(p.bbox()) for p in cuts) == expected
            common.append(dict(center_dbu=[16000, y], actual_union_cuts=2, boxes_dbu=expected))
        stem = pya.Region(pya.Box(15850, 15060, 16150, 16260))
        assert (stem - layers['M2']).is_empty()
        # Whole stem is single precision/general interface; inherited seven-cut proof
        # establishes branch separation, not an ideal equipotential star.
        iq56 = sum(r['injection_A'] for r in emitters if r['role'] == 'return_XQ56')
        ir16 = sum(r['injection_A'] for r in heads)
        current = iq56 + ir16
        receipt.update(status='passed actual access inventory; full R qualification not run', emitters=emitters,
            resistor_precision_heads=heads, precision_stem=dict(M2_bbox_dbu=[15850, 15060, 16150, 16260],
                Via2_interfaces=common, Q56_injection_A=iq56, XR16_injection_A=ir16, combined_injection_A=current,
                LEF_partial_resistance_ohm=20 + .103 * 1.2 / .3,
                KPEX_partial_resistance_ohm=9 + .088 * 1.2 / .3,
                LEF_partial_drop_V=current * (20 + .103 * 1.2 / .3),
                KPEX_partial_drop_V=current * (9 + .088 * 1.2 / .3)),
            emitter_contact_interpretation='No Cont cut intersects native E M1; pinned LVS connects E via EmWind directly to M1. Generic Cont resistance is not applicable there; model/electrode boundary and M1 spreading remain unresolved.',
            omitted=['native emitter M1 distributed spreading and model boundary', 'XR16 native head/contact model boundary',
                     'full XR16 rail and access network', 'finite general hub/all other VSS injections',
                     'well/substrate resistance', 'PVT and selfconsistent redistribution'])
    except Exception as error:
        receipt.update(status='failed actual access inventory', error=repr(error))
        raise
    finally:
        receipt['inputs'] = {str(p): sha(p) for p in (args.gds, args.currents, ledger_path, resistor_path, definitions, connections, Path(__file__))}
        dump(args.output / 'summary.json', receipt)
        print(json.dumps({k: v for k, v in receipt.items() if k not in ('emitters', 'resistor_precision_heads')}, indent=2))


if __name__ == '__main__':
    main()
