#!/usr/bin/env python3
"""Read-only actual native cell-name/placement binding to the source ODB graph."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import traceback
import pya


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, d):
    p.write_text(json.dumps(d, indent=2) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gds', type=Path, required=True)
    ap.add_argument('--roundtrip', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running native name/interface audit')
    try:
        assert len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
        assert sha(a.gds) == '226c5aad876b9aea1ec2cd5874c828b2ae87ffb80a3efded7f8d9a2389cd8e05'
        assert sha(a.roundtrip) == '43be000677b631983ae7f159d988cc6d1654679caa436e6ab3da62b1df2452fd'
        layout = pya.Layout()
        layout.read(str(a.gds))
        top, = layout.top_cells()
        assert top.name == 'placed_core_NOT_CONNECTED_FULLCHIP' and layout.dbu == .001
        actual = []
        for inst in top.each_inst():
            assert not inst.is_regular_array()
            actual.append(dict(cell=inst.cell.name, transform=str(inst.trans),
                               bbox_dbu=[inst.bbox().left, inst.bbox().bottom, inst.bbox().right, inst.bbox().top],
                               local_bbox_dbu=[inst.cell.bbox().left, inst.cell.bbox().bottom, inst.cell.bbox().right, inst.cell.bbox().top]))
        # Save actual observation before interpreting any names or placements.
        dump(a.output / 'actual_top_instances.json', actual)
        expected = []
        orientation = dict(R0=pya.Trans.R0, R90=pya.Trans.R90, R180=pya.Trans.R180, R270=pya.Trans.R270,
                           MX=pya.Trans.M0, MY=pya.Trans.M90, MXR90=pya.Trans.M45, MYR90=pya.Trans.M135)
        for line in a.roundtrip.read_text().splitlines():
            f = line.split('\t')
            if f[0] != 'INST':
                continue
            x1, y1, x2, y2 = map(int, f[4:8])
            width, height = x2 - x1, y2 - y1
            if f[3] in ('R90', 'R270', 'MXR90', 'MYR90'):
                width, height = height, width
            linear = pya.Trans(orientation[f[3]])
            rotated = linear * pya.Box(0, 0, width, height)
            transform = pya.Trans(x1 - rotated.left, y1 - rotated.bottom) * linear
            expected.append(dict(instance=f[1], master=f[2], transform=str(transform), ODB_bbox_dbu=[x1, y1, x2, y2]))
        assert len(expected) == 4904
        known = {r['master'] for r in expected}
        aliases = {}
        for cell in {r['cell'] for r in actual}:
            if cell in ('g1_bgr_candidate', 'g1_sense_candidate'):
                aliases[cell] = cell.removesuffix('_candidate')
            elif cell.startswith('retained_fullchip_') and cell[len('retained_fullchip_'):] in known:
                aliases[cell] = cell[len('retained_fullchip_'):]
            elif cell.startswith('retained_') and cell[len('retained_'):] in known:
                aliases[cell] = cell[len('retained_'):]
            elif cell in known:
                aliases[cell] = cell
        native = [r for r in actual if r['cell'] in aliases]
        route_only = [r for r in actual if r['cell'] not in aliases]
        assert len(native) == 4904, dict(native=len(native), other_cells=Counter(r['cell'] for r in route_only))
        lookup = {}
        for r in native:
            key = (aliases[r['cell']], r['transform'])
            assert key not in lookup, key
            lookup[key] = r
        matched, missing = [], []
        for e in expected:
            found = lookup.get((e['master'], e['transform']))
            if found is None:
                missing.append(e)
            else:
                matched.append(dict(e, native=found))
        result.update(GDS_sha256=sha(a.gds), roundtrip_sha256=sha(a.roundtrip),
                      top_layout_name=top.name, top_source_name='g1_chip_top',
                      cell_aliases=aliases, native_instances=len(native), route_only_cells=route_only,
                      matched=matched, unmatched=missing)
        assert not missing, dict(missing_count=len(missing), first=missing[:5])
        assert len(matched) == len(lookup) == 4904
        result.update(status='passed exact native instance/master/name/transform correspondence; not LVS',
                      checks=dict(native4904_source_master_transform_binding='passed',
                                  geometry_renames_or_edits='not run', hierarchy_name_LVS_binding='not run',
                                  new_fullchip_LVS='not run', physical_device_matching='not run',
                                  current_IO_tap_strict_result='failed prior result', stochastic_seed='not applicable'),
                      script_sha256=sha(Path(__file__)))
    except BaseException as exc:
        result.update(status='failed native name/interface audit', exception_type=type(exc).__name__,
                      detail=str(exc), traceback=traceback.format_exc())
        dump(a.output / 'failure.json', result)
        dump(a.output / 'summary.json', result)
        raise
    dump(a.output / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('matched', 'unmatched')}, indent=2))


if __name__ == '__main__':
    main()
