#!/usr/bin/env python3
"""Import detailed DEF routes through pinned KLayout; retain native instances."""
import argparse
import collections
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region, text_records as named_text_records, sha

PDK = Path('/foss/pdks/ihp-sg13g2')


def text_records(layout, cell):
    """Physical layer/datatype identity, independent of LEF display aliases."""
    result = []
    for index in layout.layer_indexes():
        info = layout.get_info(index)
        it = cell.begin_shapes_rec(index)
        while not it.at_end():
            if it.shape().is_text():
                text = it.shape().text
                point = it.trans()*pya.Point(text.trans.disp.x, text.trans.disp.y)
                result.append((info.layer, info.datatype, text.string, point.x, point.y))
            it.next()
    return sorted(result)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--gds-name', required=True)
    p.add_argument('--route', type=Path, required=True)
    p.add_argument('--odb-check', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
    assert (PDK/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    native = json.loads((a.native/'analysis.json').read_text())
    routed = json.loads((a.route/'analysis.json').read_text())
    imported = json.loads((a.odb_check/'analysis.json').read_text())
    source = a.native/a.gds_name; deffile = a.route/'detailed.def'
    assert source.name == a.gds_name and native['status'].startswith('passed') and sha(source) == native['GDS_sha256']
    route_ancestor=a.route
    if routed['status']=='passed exact three-segment g_shared_bare spacing repair; stock checks not run':
        from repair_gshared_route_spacing import validate_patch
        route_ancestor,ancestral_route=validate_patch(a.route)
    else:
        assert routed['status'] == 'passed isolated detailed-route candidate with zero router markers'
        ancestral_route=routed
    assert routed['instances_and_terminal_connectivity_held'] == 'passed'
    assert sha(deffile) == routed['detailed.def_sha256']
    # Bind the routed database ancestry to the exact audited LEF/DEF input.
    route_script = (route_ancestor/'route.tcl').read_text()
    global_odb = Path(route_script.split('read_db {', 1)[1].split('}', 1)[0])
    global_meta = json.loads((global_odb.parent/'analysis.json').read_text())
    assert global_meta['inputs'][str(a.odb_check/'unrouted_fullchip.odb')] == imported['ODB_sha256']
    assert sha(global_odb) == ancestral_route['global_ODB_sha256']
    for row in imported['LEFs']:
        assert sha(Path(row['path'])) == row['sha256']
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    techpath = PDK/'libs.tech/klayout/tech/sg13g2.lyt'
    mappath = PDK/'libs.tech/klayout/tech/sg13g2.map'
    tech = pya.Technology(); tech.load(str(techpath)); options = tech.load_layout_options
    options.lefdef_config.read_lef_with_def = False
    options.lefdef_config.lef_files = [r['path'] for r in imported['LEFs']]
    options.lefdef_config.map_file = str(mappath)
    options.lefdef_config.net_property_name = None
    options.lefdef_config.instance_property_name = None
    options.lefdef_config.pin_property_name = None
    route_layout = pya.Layout(); route_layout.read(str(deffile), options)
    rt = route_layout.cell('g1_chip_top'); assert rt is not None and route_layout.dbu == .001
    masters = collections.Counter()
    for line in (a.odb_check/'roundtrip.tsv').read_text().splitlines():
        fields = line.split('\t')
        if fields[0] == 'INST': masters[fields[2]] += 1
    assert sum(masters.values()) == 4904
    removed = collections.Counter(); vias = collections.Counter()
    for instance in list(rt.each_inst()):
        name = instance.cell.name
        if name in masters:
            removed[name] += 1
            instance.delete()
        else:
            assert name.startswith('VIA'), name
            vias[name] += 1
    assert removed == masters and sum(vias.values()) > 0
    # Copy only surviving route hierarchy; discarded LEF cells do not enter
    # the GDS and cannot replace or duplicate a native source macro.
    route_only = pya.Layout(); route_only.dbu = .001
    rtop = route_only.create_cell('g1_signal_routes_only'); rtop.copy_tree(rt)
    allowed = {8, 10, 19, 29, 30, 49, 50, 66, 67, 125, 126, 133, 134, 235}
    layers = []
    for info in route_only.layer_infos():
        shapes = region(route_only, rtop, info)
        if shapes.is_empty(): continue
        if info.layer == 189 and info.datatype == 4:
            assert (shapes ^ pya.Region(pya.Box(0, 0, 1414000, 1414000))).is_empty()
        else:
            assert info.layer in allowed, (str(info), str(shapes.bbox()))
        layers.append(dict(layer=str(info), polygons=shapes.count(), area_um2=shapes.area()*1e-6))
    route_gds = a.output/'signal_routes_only.gds'; route_only.write(str(route_gds))
    layout = pya.Layout(); layout.read(str(source)); top = layout.top_cell()
    before = {str(i): region(layout, top, i) for i in layout.layer_infos()}
    texts = text_records(layout, top)
    instances = sorted((i.cell.name, str(i.trans)) for i in top.each_inst())
    if native['status']=='passed exact old-route removal with all other native definitions held':
        assert len(instances)==native['native_root_instances'] and len(instances)>=4904
        assert native['all_other_instances_and_definitions']=='passed exact'
        assert not any(i.cell.name=='new_signal_routes' for i in top.each_inst())
    else:
        assert len(instances) == 4904
    copied = layout.create_cell('new_signal_routes'); copied.copy_tree(rtop)
    for cell in layout.each_cell():
        if cell.name in vias:
            cell.name = 'new_signal_route_'+cell.name
    top.insert(pya.CellInstArray(copied.cell_index(), pya.Trans()))
    for info in layout.layer_infos():
        expected = before.get(str(info), pya.Region()) + region(route_only, rtop, info)
        assert (region(layout, top, info)^expected).is_empty(), str(info)
    observed_texts = text_records(layout, top)
    expected_texts = sorted(texts+text_records(route_only, rtop))
    if observed_texts != expected_texts:
        (a.output/'text_differences.json').write_text(json.dumps(dict(
            missing=list((collections.Counter(expected_texts)-collections.Counter(observed_texts)).items()),
            extra=list((collections.Counter(observed_texts)-collections.Counter(expected_texts)).items())), indent=2)+'\n')
    assert observed_texts == expected_texts
    assert sorted((i.cell.name, str(i.trans)) for i in top.each_inst() if i.cell_index != copied.cell_index()) == instances
    output = a.output/'signal_routed_native.gds'; layout.write(str(output))
    saved = pya.Layout(); saved.read(str(output)); st = saved.top_cell()
    assert text_records(saved, st) == text_records(layout, top)
    for info in layout.layer_infos():
        assert (region(saved, st, info)^region(layout, top, info)).is_empty()
    result = dict(status='passed native-preserving DEF signal-route streamout and exact geometry roundtrip',
                  GDS_sha256=sha(output), native_GDS_sha256=sha(source), DEF_sha256=sha(deffile),
                  route_only_GDS_sha256=sha(route_gds), script_sha256=sha(Path(__file__)),
                  stock_technology_sha256=sha(techpath), stock_layer_map_sha256=sha(mappath),
                  removed_LEF_instances=sum(removed.values()), native_instances_retained=len(instances),
                  route_via_instances=dict(vias), route_layers=layers, native_geometry_and_texts_held='passed',
                  saved_roundtrip='passed',
                  not_run=['independent OpenDB route-polygon comparison', 'full signal physical connectivity',
                           'stock fullchip DRC/LVS/PEX/density/antenna', 'full PDN/feeds', 'electrical adoption'],
                  not_applicable=['PDK cell and rule-deck modifications'])
    result['route_metadata_sha256']=sha(a.route/'analysis.json')
    result['route_validation_scope']=routed['status']
    (a.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
