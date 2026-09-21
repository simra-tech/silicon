#!/usr/bin/env python3
"""Read-only geometry audit. Run from repository root using flow/run.sh python3.

This is neither LVS nor extraction. Logical group assignments are explicit
generator-derived hypotheses, checked against the delivered GDS geometry.
DEF centerline coverage does not establish wire width, connectivity or RC.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import pya

ROOT = Path(__file__).resolve().parents[4]
DESIGN = ROOT / 'designs/g1-guardian'
BLOCKS = DESIGN / 'blocks'
GDS = BLOCKS / 'g1_padring/layout/g1_chip_top.gds'
DEF = BLOCKS / 'g1_padring/flow/runs/assembly-1350/final/def/g1_chip_top.def'
METALS = {'Metal1': 8, 'Metal2': 10, 'Metal3': 30, 'Metal4': 50,
          'Metal5': 67, 'TopMetal1': 126, 'TopMetal2': 134}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve old evidence: choose a new output path')
    ly = pya.Layout()
    ly.read(str(GDS))
    dbu = ly.dbu
    top = ly.cell('g1_chip_top')

    def reg(cell, layer, datatype=0):
        return pya.Region(cell.begin_shapes_rec(ly.layer(layer, datatype))).merged()

    def boxlist(box):
        return [round(x * dbu, 6) for x in (box.left, box.bottom, box.right, box.top)]

    def groups(records):
        out = {}
        for name in sorted(set(r['group'] for r in records)):
            rows = [r for r in records if r['group'] == name]
            out[name] = {'count': len(rows), 'centroid_um': [
                round(sum(r['center_um'][j] for r in rows) / len(rows), 6) for j in (0, 1)]}
        return out

    placements = []
    for inst in top.each_inst():
        if inst.cell.name.startswith('g1_'):
            placements.append({'cell': inst.cell.name, 'transform': str(inst.dcplx_trans),
                               'bbox_um': boxlist(inst.bbox())})

    # Inspect actual PCell origins/bounding boxes; use source row/column mapping.
    sense = ly.cell('g1_sense')
    resistors = []
    for i in sense.each_inst():
        if not i.cell.name.startswith('rppd'):
            continue
        x, y = i.dcplx_trans.disp.x, i.dcplx_trans.disp.y
        col = round((x - 113.66) / 2.5)
        row = round((y - 13.0) / 83.92)
        assert abs(x - (113.66 + col * 2.5)) < 1e-5
        assert abs(y - (13 + row * 83.92)) < 1e-5
        group = 'RD2'
        if row == 0 and col == 25: group = 'R1N'
        elif row == 0 and col == 26: group = 'R1P'
        elif (row == 0 and 15 <= col <= 24) or (row == 1 and 27 <= col <= 36): group = 'R2N'
        elif (row == 0 and 27 <= col <= 36) or (row == 1 and 15 <= col <= 24): group = 'R2P'
        elif row == 1 and col in (25, 26): group = 'RD1'
        b = i.bbox()
        resistors.append({'group': group, 'row': row, 'column': col, 'cell': i.cell.name,
                         'orientation': str(i.dcplx_trans).split(' *')[0],
                         'center_um': [b.center().x * dbu, b.center().y * dbu],
                         'bbox_um': boxlist(b),
                         'contact_cuts_per_unit': reg(i.cell, 6).count()})
    assert len(resistors) == 95

    ota = ly.cell('g1_ota')
    active = reg(ota, 1)
    poly = reg(ota, 5)
    row_window = pya.Region(pya.DBox(-1, 25, 80, 31).to_itype(dbu))
    gates = sorted((active & poly & row_window).each(), key=lambda p: p.bbox().left)
    assert len(gates) == 32, f'Expected 32 input fingers, got {len(gates)}'
    fingers = []
    contacts = reg(ota, 6)
    for n, gate in enumerate(gates):
        b = gate.bbox()
        island = poly.interacting(pya.Region(gate))
        fingers.append({'finger': n, 'group': 'ABBAABBAABBAABBA'[n // 2],
                        'center_um': [b.center().x * dbu, b.center().y * dbu],
                        'gate_length_um': b.width() * dbu,
                        'gate_width_um': b.height() * dbu,
                        'poly_island_contact_cuts': contacts.interacting(island).count()})

    # HBT PCell centers are origins in these two macros.
    hbt = {}
    for cname, yline, xstart, labels in [
        ('g1_bgr', 77.31, 10.55, ['D', 'Q2', 'Q2', 'Q2', 'Q2', 'Q1', 'Q2', 'Q2', 'Q2', 'Q2', 'D']),
        ('g1_t2f', 70.0, 9.0, ['D', 'QA', 'QB', 'QB', 'QA', 'D'])]:
        records = []
        for i in ly.cell(cname).each_inst():
            if not i.cell.name.startswith('npn13G2'):
                continue
            x, y = i.dcplx_trans.disp.x, i.dcplx_trans.disp.y
            if abs(y - yline) > 1e-5:
                continue
            col = round((x - xstart) / 6.3)
            assert abs(x - (xstart + col * 6.3)) < 1e-5
            records.append({'group': labels[col], 'column': col, 'cell': i.cell.name,
                            'orientation': str(i.dcplx_trans).split(' *')[0],
                            'center_um': [x, y], 'bbox_um': boxlist(i.bbox()),
                            'contact_cuts_per_pcell': reg(i.cell, 6).count()})
        assert len(records) == len(labels), (cname, len(records))
        hbt[cname] = {'devices': records, 'groups': groups(records)}

    bgr_r = []
    for i in ly.cell('g1_bgr').each_inst():
        if not i.cell.name.startswith('rppd'): continue
        b = i.bbox()
        length = round(b.height() * dbu - 1.22, 3)
        if length not in (51.5, 52.5): continue
        bgr_r.append({'group': 'R1' if length == 51.5 else 'R2', 'body_length_um': length,
                      'center_um': [b.center().x * dbu, b.center().y * dbu],
                      'bbox_um': boxlist(b), 'contact_cuts_per_unit': reg(i.cell, 6).count()})
    assert len(bgr_r) == 7

    # DEF routes + actual delivered GDS: check every segment centerline is covered.
    # Exclude macro interior (not represented by DEF); include hierarchy in GDS.
    dt = DEF.read_text()
    units = int(re.search(r'UNITS DISTANCE MICRONS (\d+)', dt)[1])
    nets_section = re.search(r'^NETS \d+ ;(.*?)^END NETS', dt, re.M | re.S)[1]
    wanted = {'i_core.sense_n', 'i_core.sense_p', 'i_core.isense', 'i_core.vref',
              'i_core.vref_buf', 'i_core.iptat', 'i_core.osc_clk', 'i_core.gate_core',
              'i_core.cmp_clk', 'i_core.hard_cmp', 'i_core.cmp_hard', 'i_core.cmp_soft', 'gate_o'}
    regions = {}
    nets = []
    for entry in re.findall(r'^\s*- (.*?) ;', nets_section, re.M | re.S):
        name = entry.split()[0]
        if name not in wanted: continue
        segments, vias = [], []
        totals = collections.defaultdict(float)
        for route in re.split(r'(?:\+ ROUTED|\bNEW)\s+', entry)[1:]:
            layer = route.split()[0]
            coords = list(re.finditer(r'\(\s+([*\d-]+)\s+([*\d-]+)(?:\s+\d+)?\s+\)', route))
            points = []
            for p in coords:
                xy = [points[-1][j] if p[j + 1] == '*' else int(p[j + 1]) / units for j in (0, 1)]
                points.append(xy)
            for a, b in zip(points, points[1:]):
                assert a[0] == b[0] or a[1] == b[1], 'Non-Manhattan route unsupported'
                length = abs(a[0] - b[0]) + abs(a[1] - b[1])
                totals[layer] += length
                if layer not in regions: regions[layer] = reg(top, METALS[layer])
                narrow = pya.Region(pya.DPath([pya.DPoint(*a), pya.DPoint(*b)], 2 * dbu).to_itype(dbu))
                missing = narrow - regions[layer]
                segments.append({'layer': layer, 'a_um': a, 'b_um': b, 'length_um': round(length, 6),
                                 'centerline_covered_in_gds': missing.is_empty(),
                                 'missing_area_um2': missing.area() * dbu ** 2})
            if coords:
                tail = route[coords[-1].end():].strip().split()
                if tail and ('Via' in tail[0] or 'via' in tail[0]):
                    vias.append({'name': tail[0], 'at_um': points[-1]})
        nets.append({'net': name, 'length_by_layer_um': dict(totals),
                     'total_route_length_um': round(sum(totals.values()), 6),
                     'via_instances': vias, 'segments': segments,
                     'centerline_coverage_status': 'passed' if segments and all(s['centerline_covered_in_gds'] for s in segments) else 'failed'})

    inputs = [GDS, DEF, BLOCKS / 'g1_sense/layout/g1_ota_layout.py',
              BLOCKS / 'g1_sense/layout/g1_sense_layout.py',
              BLOCKS / 'g1_bgr/layout/g1_bgr_layout.py', BLOCKS / 'g1_t2f/layout/g1_t2f_layout.py']
    reports = BLOCKS / 'g1_padring/reports/assembly-1350'
    prior = {}
    for name in ('drc.klayout.json', 'density.klayout.json', 'antenna.klayout.json'):
        path = reports / name
        content = json.loads(path.read_text())
        prior[name] = {k: v for k, v in content.items() if v or k == 'total'}
        inputs.append(path)
    result = {'tool': f'KLayout Python {pya.__version__}', 'dbu_um': dbu,
              'pdk_commit_observed': Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip(),
              'pdk_commit_method': 'Read installed PDK COMMIT stamp; image has no PDK .git directory.',
              'command': 'flow/run.sh python3 designs/g1-guardian/review/audits/audit_physical.py --output ' + str(args.output),
              'inputs': {str(p.relative_to(ROOT)): sha(p) for p in inputs},
              'macro_placements': placements, 'sense_resistors': {'units': resistors, 'groups': groups(resistors)},
              'sense_ota_input_fingers': {'fingers': fingers, 'groups': groups(fingers)},
              'hbt_pairs': hbt, 'bgr_resistors': {'units': bgr_r, 'groups': groups(bgr_r)},
              'critical_chip_routes': nets, 'prior_reports_read_not_rerun': prior,
              'not_run': ['New DRC/LVS/antenna/density', 'IO-inclusive LVS closure',
                          'Wire and contact resistance extraction', 'Clock/substrate/fill coupling extraction',
                          'Electrical mismatch or gradient simulation', 'Guard/well distance qualification'],
              'limitations': ['GDS group labels use generator mapping, not new transistor LVS.',
                              'Wire centerline coverage is a geometry consistency test, not connectivity or route-width signoff.',
                              'Contacts counted per PCell exclude external route contact/via stacks.',
                              'Route lengths exclude IO-cell and macro-internal conductors. No length-to-performance inference.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), 'gds_sha256': sha(GDS),
                      'nets': [(n['net'], n['total_route_length_um'], n['centerline_coverage_status']) for n in nets]}, indent=2))


if __name__ == '__main__':
    main()
