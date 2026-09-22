#!/usr/bin/env python3
"""Independent saved channels/terminal attribution, then exact two-device CDL."""
import collections
import copy
import json
import os
from pathlib import Path
import re
from build_source_faithful_buffer import pya, snapshot, full_nets, sha
from audit_junction_defaults import default
from spice2cdl import convert


def main():
    here = Path(__file__).resolve().parent
    base = here / 'stacked-pair-20260922-r2'
    out = here / 'stacked-pair-reference-20260922-r1'
    assert not out.exists() and pya.__version__ == '0.30.9' and os.sched_getaffinity(0) == {7}
    m = json.loads((base / 'manifest.json').read_text())
    assert m['status'] == 'passed isolated stacked pair native/terminal/obstruction scope'
    gds = base / 'g1_main_pair_stacked64.gds'
    assert sha(gds) == m['GDS_sha256'] == '8818ee050f60243b34b8985f9630ed3d9704351d9874ef656a7202bba8290bf3'
    source = here.parents[1] / 'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source) == m['source_sha256'] == 'baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    block = re.search(r'(?ms)^\.subckt g1_ota_main_candidate .*?^\.ends', source.read_text()).group(0)
    specs = {line.split()[0]: line for line in block.splitlines() if line.startswith(('XM1 ', 'XM2 '))}
    assert specs == m['source_lines'] and len(specs) == 2
    layout = pya.Layout()
    layout.read(str(gds))
    cell = layout.cell('g1_main_pair_stacked64')
    active, poly = snapshot(cell, 1), snapshot(cell, 5)
    probes = copy.deepcopy(m['terminal_audit']['probes'])
    terminal = full_nets(cell, probes)
    assert terminal['status'] == 'passed'
    gp = [q for q in probes if q['terminal'] == 'gate']
    dp = [q for q in probes if q['device'] == 'pair' and q['layer'] == 501]
    gates = []
    owners = collections.defaultdict(list)
    def hits(box, records):
        return [q for q in records if box.contains(pya.DPoint(*q['point_um']).to_itype(.001))]
    for polygon in (active & poly).each():
        box = polygon.bbox()
        assert polygon.area() == box.area()
        matches = hits(box, gp)
        assert len(matches) == 1
        name = matches[0]['device']
        gates.append((box, name))
        owners[name].append(box)
    assert len(gates) == len(gp) == 128
    allocated = {name: dict(as_um2=0., ad_um2=0., ps_um=0., pd_um=0.) for name in specs}
    strips = []
    for polygon in (active - poly).each():
        box = polygon.bbox()
        adjacent = [(b, n) for b, n in gates if b.bottom == box.bottom and b.top == box.top and (b.left == box.right or b.right == box.left)]
        if not adjacent:
            continue
        assert 1 <= len(adjacent) <= 2 and polygon.area() == box.area()
        matches = hits(box, dp)
        assert len(matches) == 1
        net = matches[0]['net']
        weights = collections.Counter(n for b, n in adjacent)
        for name, count in weights.items():
            words = specs[name].split()
            fields = [field for field, index in [('s', 3), ('d', 1)] if words[index] == net]
            assert len(fields) == 1
            field, weight = fields[0], count / len(adjacent)
            allocated[name]['a' + field + '_um2'] += weight * polygon.area() * 1e-6
            allocated[name]['p' + field + '_um'] += weight * polygon.perimeter() * .001
        strips.append(dict(net=net, area_um2=polygon.area() * 1e-6, perimeter_um=polygon.perimeter() * .001, adjacent_owners=dict(weights)))
    assert len(strips) == len(dp) == 130
    for name, boxes in owners.items():
        assert len(boxes) == 64 and all(b.width() == 2000 and b.height() == 6000 for b in boxes)
        assert all(abs(allocated[name][key] - value) < 1e-8 for key, value in default(384, 64).items())
        assert [sum((b.center().x if axis == 0 else b.center().y) * .001 for b in boxes) / 64 for axis in (0, 1)] == [115., 59.25]
    bbox = cell.bbox()
    assert bbox.left >= 0 and bbox.bottom >= 0 and bbox.right <= 230000 and bbox.top <= 164000
    offgrid = []
    for index in layout.layer_indices():
        for polygon in pya.Region(cell.begin_shapes_rec(index)).each():
            for point in polygon.each_point_hull():
                if point.x % 5 or point.y % 5:
                    offgrid.append([point.x, point.y])
    assert not offgrid
    out.mkdir()
    lines = ['.subckt g1_main_pair_stacked64 inn inp fn fp tail vdd vss'] + list(specs.values()) + ['.ends g1_main_pair_stacked64']
    cdl = out / 'g1_main_pair_stacked64.cdl'
    cdl.write_text('\n'.join(convert(lines)) + '\n')
    result = dict(status='passed saved-polygon and exact source reference gate', source_sha256=sha(source), GDS_sha256=sha(gds),
                  manifest_sha256=sha(base / 'manifest.json'), script_sha256=sha(Path(__file__)), CDL_sha256=sha(cdl),
                  source_lines=specs, source_W_L_ng='passed two W384 L2 ng64', adjacent_gate_allocation=allocated,
                  terminal_audit=terminal, strip_count=len(strips), strips=strips, grid_5nm='passed',
                  bbox_um=[v * .001 for v in (bbox.left, bbox.bottom, bbox.right, bbox.top)],
                  conversions=['Stock X-to-M conversion; ng/mm_ok omitted, separate native proof retained'],
                  stock_DRC_LVS='not run', intrinsic_junction_applicability='not run', full_main='not run', seed='not applicable')
    (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('terminal_audit', 'strips')}, indent=2))


if __name__ == '__main__':
    main()
