#!/usr/bin/env python3
"""Read-only native CMIM terminal-layer and installed-interface audit."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tempfile

import klayout.db as kdb
import klayout_pex.klayout.lvsdb_extractor as extractor


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def area(region):
    return region.area() / 1e6


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lvsdb', type=Path, required=True)
    p.add_argument('--kpex-lvsdb-gz', type=Path, required=True)
    p.add_argument('--gds', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    assert Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    pdk = Path('/foss/pdks/ihp-sg13g2')
    deriv = pdk / 'libs.tech/klayout/tech/lvs/rule_decks/cap_derivations.lvs'
    connects = pdk / 'libs.tech/klayout/tech/lvs/rule_decks/cap_connections.lvs'
    native = pdk / 'libs.tech/ngspice/models/capacitors_mod.lib'
    corners = pdk / 'libs.tech/ngspice/models/cornerCAP.lib'
    extraction_source = Path(extractor.__file__)
    s = deriv.read_text()
    assert 'cmim_top = mim_top.not(mimcap_exclude)' in s
    assert 'cmim_btm = mim_btm.covering(cmim_top)' in s
    assert 'mim_top = mim_drw.overlapping(topmetal1_con)' in s
    assert 'mim_btm = mim_drw.and(metal5_con)' in s
    assert 'mim_via = vmim_drw.join(topvia1_drw).and(mim_drw)' in s
    s = connects.read_text()
    assert 'connect(cmim_btm, metal5_con)' in s
    assert 'connect(cmim_top, mim_via)' in s
    assert 'connect(mim_via, topmetal1_con)' in s
    s = native.read_text()
    assert 'R1 PLUS 1 r=55m' in s
    assert 'C1 1 MINUS cmim_core l=l/sf w=w/sf scale=1' in s
    assert '.model cmim_core C (TC1=3.6E-6 TC2=2E-9 TNOM=27 CJ=cap_carea CJSW=40E-18)' in s
    assert 'top/bottom plate parasitic capacitance is included by parasiticC extraction' in s
    assert '.param cap_carea_norm = 1.5E-15' in corners.read_text()
    s = extraction_source.read_text()
    assert 'if computed_layer_info and blackbox_devices:' in s
    assert 'case tech_pb2.ComputedLayerInfo.Kind.KIND_DEVICE_CAPACITOR:' in s
    assert 'if lyr_idx is None:' in s
    ly = kdb.Layout()
    ly.read(str(a.gds))
    top = ly.cell('sense_mim_method_control')
    assert top is not None and ly.dbu == .001
    drw = {name: kdb.Region(top.begin_shapes_rec(ly.layer(num, 0)))
           for name, num in [('mim_drw', 36), ('metal5_drw', 67),
                             ('topmetal1_drw', 126), ('mim_via', 129)]}
    db = kdb.LayoutVsSchematic()
    with tempfile.TemporaryDirectory(dir=a.output.parent) as temporary:
        copied = Path(temporary) / 'diagnostic.lvsdb'
        copied.write_bytes(gzip.decompress(a.kpex_lvsdb_gz.read_bytes()))
        db.read(str(copied))
    layer_info = {i: db.layer_name(i) for i in db.layer_indexes()}
    derived = {name: db.layer_by_index(i) for i, name in layer_info.items()
               if name in ('cmim_top', 'cmim_btm', 'mim_via', 'metal5_n_cap',
                           'topmetal1_con')}
    assert all(name in derived for name in ('cmim_top', 'cmim_btm', 'mim_via',
                                            'metal5_n_cap', 'topmetal1_con'))
    assert (derived['cmim_top'] ^ drw['mim_drw']).is_empty()
    assert (derived['cmim_btm'] ^ drw['mim_drw']).is_empty()
    intersections = dict(
        top_plate_vs_TopMetal1_um2=area(derived['cmim_top'] & derived['topmetal1_con']),
        top_plate_vs_MIM_via_um2=area(derived['cmim_top'] & derived['mim_via']),
        bottom_plate_vs_external_Metal5_um2=area(derived['cmim_btm'] & derived['metal5_n_cap']))
    assert intersections['bottom_plate_vs_external_Metal5_um2'] == 0
    devices = []
    for dev in db.netlist().top_circuit().each_device():
        terminals = []
        for td in dev.device_class().terminal_definitions():
            net = dev.net_for_terminal(td.id())
            matches = [ref for ref in net.each_terminal()
                       if ref.device().expanded_name() == dev.expanded_name()
                       and ref.terminal_id() == td.id()]
            assert len(matches) == 1
            shapes = db.shapes_of_terminal(matches[0])
            terminals.append(dict(name=td.name, net=net.name,
                                  regions=[dict(layer_index=i, layer_name=layer_info[i],
                                                area_um2=area(r), bbox_dbu=str(r.bbox()))
                                           for i, r in shapes.items()]))
        devices.append(dict(name=dev.expanded_name(), class_name=dev.device_class().name,
                            terminals=terminals))
    out = dict(status='read-only terminal composition audit',
               gds_sha256=sha(a.gds), strict_lvsdb_sha256=sha(a.lvsdb),
               kpex_lvsdb_gz_sha256=sha(a.kpex_lvsdb_gz),
               installed_sources_sha256={str(q.relative_to(pdk)) if q.is_relative_to(pdk) else
                   'klayout_pex/klayout/lvsdb_extractor.py': sha(q)
                   for q in (deriv, connects, native, corners, extraction_source)},
               native_model=dict(series_resistor_ohm=.055,
                                 cmim_core_CJ_F_per_um2=1.5e-15,
                                 cmim_core_CJSW_F_per_um=40e-18,
                                 seven_by_seven_nominal_intrinsic_C_F=(49*1.5e-15+28*40e-18),
                                 plate_parasitic_C='specified by model comment as PEX-owned; not supplied by model'),
               drawn={name: dict(area_um2=area(r), bbox_dbu=str(r.bbox()))
                      for name, r in drw.items()},
               derived={name: dict(area_um2=area(r), bbox_dbu=str(r.bbox()),
                                   xor_vs_drawn_mim_um2=area(r ^ drw['mim_drw']))
                        for name, r in derived.items()},
               intersections=intersections,
               exact_lvs_device_terminals=devices,
               extracted_layer_names=layer_info,
               blackbox_KPEX_skips_computed_capacitor_layers=True,
               project_local_terminal_alias='not established; geometry/conductor/via ownership differ')
    a.output.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({k: out[k] for k in ('status', 'native_model', 'drawn', 'derived')}))


if __name__ == '__main__':
    main()
