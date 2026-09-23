#!/usr/bin/env python3
"""Read-only native terminal-plane audit and isolated positive-metal controls.

No canonical geometry, device model, source or existing network is edited.
The isolated coupon solves are geometric diagnostics, not calibration evidence.
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import klayout.db as kdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(HERE.parent / 'coordinated_return_remedy'))
import extract_metal_r as metal


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def reg(cell, pair):
    r = kdb.Region(cell.begin_shapes_rec(cell.layout().layer(*pair)))
    r.flatten()
    return r.merged()


def bbox(b):
    return [b.left, b.bottom, b.right, b.top]


def walk(cell, trans):
    if not list(cell.each_inst()):
        yield cell, trans
    else:
        for inst in cell.each_inst():
            for local in inst.each_trans():
                yield from walk(inst.cell, trans * local)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bulk', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    args = ap.parse_args()
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in (0, 1)
    assert kdb.__version__ == '0.30.9'
    args.output.mkdir(exist_ok=False)
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    start = time.monotonic()
    summary = dict(status='running', adoption='not run', source_changes='not applicable', seed='not applicable')
    inputs = {}

    def bind(path):
        inputs[str(path)] = sha(path)
        return path

    try:
        pdk = Path('/foss/pdks/ihp-sg13g2')
        assert (pdk / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
        gds = bind(args.bulk / 'bgr-assembly-signalbypass-20260922-r1/bank.gds')
        assert sha(gds) == '6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04'
        pack = json.loads(bind(ROOT / 'designs/g1-guardian/review/audits/coordinated-bbox-pack-586-20260922-r1.json').read_text())
        source = bind(HERE.parent.parent / 'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice')
        assert sha(source) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
        points = json.loads(bind(HERE.parent / 'coordinated_return_remedy/evidence/globalrouting-20260922-r1/metal_preparation/signalbypass/points.json').read_text())
        byterm = {(s['source_id'], s['terminal']): p for p in points for s in p['sources']}
        snippets = {}
        specs = {
            'libs.tech/ngspice/models/sg13g2_hbt_mod.lib': [(20, 57), (110, 130), (150, 160)],
            'libs.tech/ngspice/models/resistors_mod.lib': [(106, 148), (168, 208)],
            'libs.tech/ngspice/models/cornerHBT.lib': [(1, 100)],
            'libs.tech/ngspice/models/cornerRES.lib': [(1, 100)],
            'libs.tech/verilog-a/r3_cmc/r3_cmc-patched.va': [(65, 101), (179, 184), (485, 498), (749, 764)],
            'libs.tech/klayout/python/sg13g2_pycell_lib/ihp/npn13G2_code.py': [(142, 181), (310, 346), (387, 396)],
            'libs.tech/klayout/python/sg13g2_pycell_lib/ihp/rhigh_code.py': [(325, 343), (477, 496)],
            'libs.tech/klayout/python/sg13g2_pycell_lib/ihp/rppd_code.py': [(290, 320), (447, 461)],
        }
        for relative, spans in specs.items():
            path = bind(pdk / relative)
            lines = path.read_text(errors='replace').splitlines()
            snippets[relative] = dict(sha256=sha(path), excerpts=[dict(first=a, last=b,
                lines=[dict(line=i, text=lines[i-1]) for i in range(a, min(b, len(lines))+1)]) for a, b in spans])
        dump(args.output / 'pinned_evidence.json', snippets)
        layout = kdb.Layout()
        layout.read(str(gds))
        matched = {}
        leaves = list(walk(layout.top_cell(), kdb.Trans()))
        rows = [d for d in pack['BGR_devices'] if d['name'].startswith(('XQ', 'XR'))]
        lookup = {tuple(round(v * 1000) for v in d['bbox_um']): d for d in rows}
        assert len(lookup) == len(rows) == 700
        details = []
        coupons = {}
        for cell, trans in leaves:
            if not cell.name.startswith(('npn13G2', 'rhigh', 'rppd')):
                continue
            d = lookup[tuple(bbox(cell.bbox().transformed(trans)))]
            assert d['name'] not in matched
            matched[d['name']] = cell.name
            m1 = reg(cell, (8, 0))
            m2 = reg(cell, (10, 0))
            pin1 = reg(cell, (8, 2))
            pin2 = reg(cell, (10, 2))
            via = reg(cell, (19, 0))
            row = dict(source_id=d['name'], source_line=d['source_line'], native_cell=cell.name,
                       native_bbox_dbu=bbox(cell.bbox().transformed(trans)), transform=str(trans),
                       pin1_native_bboxes=[bbox(p.bbox()) for p in pin1.each()],
                       pin2_native_bboxes=[bbox(p.bbox()) for p in pin2.each()],
                       native_Via1_count=via.count(), native_Via1_area_um2=via.area()*1e-6)
            if d['name'].startswith('XQ'):
                probe = byterm[(d['name'], 'E')]
                local = trans.inverted() * kdb.Point(*probe['point_dbu'])
                assert probe['layer'] == 'M1'
                assert pin2.count() == 1 and via.count() == 8
                contains1 = not (kdb.Region(kdb.Box(local.x-1, local.y-1, local.x+1, local.y+1)) & m1).is_empty()
                contains2 = not (kdb.Region(kdb.Box(local.x-1, local.y-1, local.x+1, local.y+1)) & pin2).is_empty()
                assert contains1 and contains2
                row.update(conditional_injection_layer='M1', native_E_pin_layer='M2', same_xy_within_native_M2_pin=True,
                           conditional_local_point_dbu=[local.x, local.y], native_access_crossed_below_pin=True)
                # Isolate exactly native emitter-connected M1 plus native M2 and all eight native Via1.
                emitter = kdb.Region()
                for p in m1.each():
                    if p.bbox().contains(local):
                        emitter.insert(p)
                assert emitter.count() == 1 and m2.count() == 1
                regions = {metal.IDS['M1']: emitter, metal.IDS['M2']: m2, metal.IDS['Via1']: via}
                key = 'HBT_E_M1_to_M2'
            else:
                assert m1.count() == pin1.count() == 2 and via.is_empty()
                assert (m1 ^ pin1).is_empty()
                heads = sorted(m1.each(), key=lambda p: p.bbox().center().y)
                ownership = []
                for i, head in enumerate(heads):
                    probe = byterm[(d['name'], str(i+1))]
                    local = trans.inverted() * kdb.Point(*probe['point_dbu'])
                    assert local == head.bbox().center() and probe['layer'] == 'M1'
                    ownership.append(dict(terminal=str(i+1), local_point_dbu=[local.x, local.y],
                                          probe_at_native_pin_center=True, native_head_bbox_dbu=bbox(head.bbox())))
                row.update(terminal_controls=ownership, native_M1_pin_equals_whole_head=True,
                           added_routing_Via1_outside_native_cell=True)
                # Existing external via is offset +/-0.30um in X from native head center.
                head = heads[0]
                local = head.bbox().center()
                regions = {metal.IDS['M1']: kdb.Region(head)}
                key = d['kind'] + '_native_head_center_to_offset'
            details.append(row)
            if key not in coupons:
                coupons[key] = (regions, local, d['name'])
        assert len(matched) == 700
        dump(args.output / 'native_terminal_planes.json', details)
        controls = []
        bind(Path(metal.__file__))
        scenarios = {'KPEX': dict(sheet_ohm={'M1': .110, 'M2': .088}, cut_ohm={'Via1': 9.}),
                     'LEF': dict(sheet_ohm={'M1': .135, 'M2': .103}, cut_ohm={'Via1': 20.})}
        for name, (regions, local, device) in coupons.items():
            for scenario, values in scenarios.items():
                # This tiny native coupon is not a replacement extracted source.
                e = name.startswith('HBT')
                head_box = next(regions[metal.IDS['M1']].each()).bbox()
                offset = min(300, local.x-head_box.left-5)
                assert offset > 0
                ports = [dict(id=0, layer='M1', point_dbu=[local.x, local.y], source_net='coupon',
                              injection_A=1., reference_ports=[]),
                         dict(id=1, layer='M2' if e else 'M1',
                              point_dbu=[local.x if e else local.x-offset, local.y], source_net='coupon',
                              injection_A=-1., reference_ports=['reference'])]
                raw = metal.extract(regions, ports, values)
                solved, _ = metal.solve(raw, ports, 1)
                resistance = abs(solved['points'][0]['delta_V'])
                assert resistance > 0
                item = dict(name=name, scenario=scenario, representative_source_id=device,
                            effective_R_ohm=resistance, geometry_only=True,
                            lateral_offset_dbu=0 if e else offset,
                            physical_model_ownership='not qualified', raw=raw, solved=solved)
                if e:
                    item['ideal_equipotential_eight_cut_only_R_ohm'] = values['cut_ohm']['Via1']/8
                    assert resistance >= values['cut_ohm']['Via1']/8
                controls.append(item)
        dump(args.output / 'isolated_native_metal_controls.json', controls)
        unchanged = all(sha(Path(p)) == h for p, h in inputs.items())
        assert unchanged
        summary.update(status='passed read-only geometric/model inventory; physical partition unresolved',
            native_HBTs=301, native_resistors=399, HBT_M1_vs_M2_pin_discrepancies=301,
            native_HBT_Via1_cuts=301*8, resistor_pin_center_controls=798,
            coupon_controls=[{k:v for k,v in c.items() if k not in ('raw','solved')} for c in controls],
            all_bound_inputs_unchanged=True, physical_reference_plane_qualification='failed to establish',
            no_double_count_qualification='not run', modified_network_or_source='not run')
    except Exception as error:
        summary.update(status='failed read-only audit', error=repr(error))
        raise
    finally:
        summary.update(wall_s=time.monotonic()-start, inputs=inputs, script_sha256=sha(Path(__file__)))
        dump(args.output / 'summary.json', summary)
        print(json.dumps({k:v for k,v in summary.items() if k != 'inputs'}, indent=2))


if __name__ == '__main__':
    main()
