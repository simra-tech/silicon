#!/usr/bin/env python3
"""Integrate only two source-intended PolyRes marker recipes into ab02."""
import argparse
import collections
import json
import os
from pathlib import Path
import re
import sys
import pya

HERE = Path(__file__).resolve().parent
AUDITS = HERE.parents[2]
sys.path.insert(0, str(AUDITS))
sys.path.insert(0, str(AUDITS / 'bondpad_outward_closure'))
from place_closed_analog import region, sha, text_records
from build_candidate import signature

PARENT = 'ab02b653c6b0e29e7693bed55e097081e6e41f67e24c59102494e6fbc1724541'
PIN = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
PDK = Path('/foss/pdks/ihp-sg13g2')
SPECS = [
    ('sg13g2_SecondaryProtection', 'g1_io_secondary_polyres_r1', 'secondary.gds',
     'e27b4ff2c64db4b6f36b099beba76d93158325577c1f7c712ab5cb5d9b9eb975', 1, 2, 14),
    ('sg13g2_RCClampResistor', 'g1_io_rc_polyres_r1', 'rc.gds',
     '3ad63f1c38efea55bdd73b0ec45fa883858e7d5ed7f60cd67df5e3ec9a22447c', 26, 20, 2)]


def paths(top, targets):
    found = collections.defaultdict(list)
    def visit(cell, transform, ancestry):
        assert cell.name not in ancestry
        if cell.name in targets:
            found[cell.name].append(transform)
        for inst in cell.each_inst():
            for trans in inst.cell_inst.each_cplx_trans():
                visit(inst.cell, transform * trans, ancestry + (cell.name,))
    visit(top, pya.ICplxTrans(), ())
    return found


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('parent', 'isolated', 'alias-audit', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0)) == {1}
    assert pya.__version__ == '0.30.9' and (PDK / 'COMMIT').read_text().strip() == PIN
    assert sha(a.parent) == PARENT
    library = PDK / 'libs.ref/sg13g2_io/gds/sg13g2_io.gds'
    cdl = PDK / 'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl'
    assert sha(library) == '4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825'
    assert sha(cdl) == '7a30e902099e8a8f85e0ae853167904df3793357a793a7b4dc82237b72b3eec4'
    a.output.mkdir(parents=True); (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    ly = pya.Layout(); ly.read(str(a.parent)); top = ly.top_cell()
    assert top.name == 'placed_core_NOT_CONNECTED_FULLCHIP' and top.bbox() == pya.Box(0, 0, 1414000, 1414000)
    original_signature = signature(ly); original_texts = text_records(ly, top)
    library_layout = pya.Layout(); library_layout.read(str(library))
    alias_audit = json.loads(a.alias_audit.read_text())
    assert alias_audit['status'] == 'passed' and alias_audit['parent_sha256'] == PARENT
    target_names = {c.name for c in ly.each_cell() if any(re.search(re.escape(s[0]) + r'(?:\$\d+)?$', c.name) for s in SPECS)}
    occurrences = paths(top, target_names)
    assert len(occurrences) == 4
    expanded = []
    for spec in SPECS:
        names = sorted(n for n in occurrences if re.search(re.escape(spec[0]) + r'(?:\$\d+)?$', n))
        assert sum(len(occurrences[n]) for n in names) == spec[-1]
        for index, name in enumerate(names):
            audit_row, = [r for r in alias_audit['geometry_aliases'] if r['alias'] == name]
            assert not audit_row['differences'] and audit_row['text_equal']
            assert audit_row['transforms'] == [str(t) for t in occurrences[name]]
            expanded.append((spec, name, spec[1] + ('_alias' + str(index) if index else '')))
    original_128 = region(ly, top, pya.LayerInfo(128, 0))
    added = pya.Region(); mutations = []; ledger = []
    text = cdl.read_text()
    for spec, old_name, new_name in expanded:
        original, unit_top_name, unit_name, unit_hash, per_cell, length, expected_count = spec
        cell = ly.cell(old_name); reference = library_layout.cell(original)
        assert cell and reference and not ly.cell(new_name)
        transforms = occurrences[old_name]
        unit_file = a.isolated / unit_name; assert sha(unit_file) == unit_hash
        unit_layout = pya.Layout(); unit_layout.read(str(unit_file)); unit = unit_layout.top_cell()
        assert unit.name == unit_top_name
        layers = {(q.layer, q.datatype) for source in (ly, library_layout, unit_layout) for q in source.layer_infos()}
        for layer in sorted(layers):
            native = region(ly, cell, pya.LayerInfo(*layer))
            stock = region(library_layout, reference, pya.LayerInfo(*layer))
            assert (native ^ stock).is_empty(), (old_name, layer, 'original native/library mismatch')
            if layer != (128, 0):
                assert (native ^ region(unit_layout, unit, pya.LayerInfo(*layer))).is_empty()
        assert text_records(ly, cell) == text_records(library_layout, reference) == text_records(unit_layout, unit)
        local = lambda layer: region(ly, cell, pya.LayerInfo(layer, 0))
        intended = local(5) & local(28) & local(111) & local(14)
        assert local(128).is_empty() and intended.count() == per_cell
        assert (intended ^ region(unit_layout, unit, pya.LayerInfo(128, 0))).is_empty()
        assert (intended & local(6)).is_empty()
        for polygon in intended.each():
            box = polygon.bbox()
            assert polygon.area() == box.area() and box.width() == 1000 and box.height() == length * 1000
        match = re.search(r'(?im)^\.SUBCKT ' + re.escape(original) + r'\b.*?^\.ENDS\b[^\n]*', text, re.S)
        assert match
        # Source records are retained literally, not parameterized from GDS.
        body = match.group(0); (a.output / (original + '_original.cdl')).write_text(body + '\n')
        for transform in transforms:
            added.insert(intended.transformed(transform))
        cell.shapes(ly.layer(128, 0)).insert(intended); cell.name = new_name
        mutations.append((cell, old_name))
        ledger.append(dict(original_alias=old_name, stock_cell=original, candidate_cell=new_name,
                           stock_source_sha256=sha(a.output / (original + '_original.cdl')),
                           isolated_GDS_sha256=unit_hash, instances=len(transforms),
                           transforms=[str(t) for t in transforms], markers_per_instance=per_cell,
                           marker_area_per_instance_um2=intended.area() * 1e-6,
                           source_pins=body.splitlines()[0].split()[2:],
                           source_records=body.splitlines()[1:-1]))
    assert added.count() == 66 and added.area() == 1068000000
    assert (added & original_128).is_empty()
    assert (region(ly, top, pya.LayerInfo(128, 0)) ^ (original_128 | added)).is_empty()
    assert text_records(ly, top) == original_texts
    target = a.output / 'io_marker_native.gds'; ly.write(str(target))
    for cell, old_name in mutations:
        cell.shapes(ly.layer(128, 0)).clear(); cell.name = old_name
    assert signature(ly) == original_signature
    fresh = pya.Layout(); fresh.read(str(target)); ft = fresh.top_cell()
    assert ft.name == top.name and ft.bbox() == top.bbox()
    assert text_records(fresh, ft) == original_texts
    assert (region(fresh, ft, pya.LayerInfo(128, 0)) ^ (original_128 | added)).is_empty()
    # Apply the inverse to the actual saved file as a separate lifecycle check.
    for row in ledger:
        cell = fresh.cell(row['candidate_cell']); assert cell
        cell.shapes(fresh.layer(128, 0)).clear(); cell.name = row['original_alias']
    assert signature(fresh) == original_signature
    result = dict(status='passed isolated full-chip IO marker integration geometry',
                  GDS_sha256=sha(target), parent_GDS_sha256=PARENT, script_sha256=sha(Path(__file__)),
                  signature_helper_sha256=sha(AUDITS / 'bondpad_outward_closure/build_candidate.py'),
                  PDK_commit=PIN, KLayout=pya.__version__, native_IO_GDS_sha256=sha(library),
                  alias_audit_sha256=sha(a.alias_audit),
                  reachable_source_instances=alias_audit['reachable_source_instances'],
                  source_IO_CDL_sha256=sha(cdl), targets=ledger,
                  marker_polygons=66, added_area_um2=1068.0, changed_layer=[128, 0],
                  checks=dict(original_native_library_all_layer_XOR='passed', isolated_recipe_parity='passed',
                              source_records_held='passed', exact_serialized_inverse='passed',
                              all_text_and_other_layers_held='passed', all_24_moved_pads_held='passed'),
                  not_run=['full-chip stock main/maximal', 'strict device-aware LVS',
                           'density/antenna applicability and checks', 'electrical/ESD qualification', 'adoption'],
                  not_applicable=['canonical source/card/rule changes', 'A/P golden tailoring', 'global SUB! forcing'])
    (a.output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
