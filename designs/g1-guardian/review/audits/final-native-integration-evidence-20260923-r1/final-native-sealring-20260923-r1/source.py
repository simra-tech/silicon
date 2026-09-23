#!/usr/bin/env python3
"""Add the checked native 1414-um sealring without altering chip geometry."""
import argparse
import faulthandler
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region, sha
from streamout_native_signal_routes import text_records
from build_native_decap_pdn import METALS, CUTS


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('candidate', 'sealring', 'sealring-drc', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--gds-name', required=True)
    a = p.parse_args()
    assert not a.output.exists() and Path(a.gds_name).name == a.gds_name
    assert len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
    faulthandler.dump_traceback_later(60, repeat=True)
    meta = json.loads((a.candidate/'analysis.json').read_text())
    ringmeta = json.loads((a.sealring/'analysis.json').read_text())
    proof = json.loads((a.sealring_drc/'summary.json').read_text())
    source = a.candidate/a.gds_name
    ringsource = a.sealring/'sealring.gds'
    assert meta['status'].startswith('passed') and sha(source) == meta['GDS_sha256']
    assert ringmeta['status'].startswith('passed')
    assert sha(ringsource) == ringmeta['GDS_sha256'] == proof['GDS_sha256']
    assert proof['status'] == 'passed scoped main and maximal DRC' and proof['inputs_rules_unchanged']
    assert {r['name'] for r in proof['decks']} == {'main', 'maximal'}
    for deck in proof['decks']:
        assert deck['status'] == 'passed' and len(deck['reports']) == 1
        report = deck['reports'][0]
        assert report['markers'] == 0 and sha(a.sealring_drc/report['path']) == report['sha256']
    ly = pya.Layout(); ly.read(str(source)); top = ly.top_cell()
    ring = pya.Layout(); ring.read(str(ringsource)); rt = ring.top_cell()
    assert ly.dbu == ring.dbu == .001
    die = pya.Region(pya.Box(0, 0, 1414000, 1414000))
    assert rt.bbox() == die.bbox()
    assert (region(ring, rt, pya.LayerInfo(39, 4)) ^ die).is_empty()
    assert region(ly, top, pya.LayerInfo(39, 4)).is_empty()
    assert region(ly, top, pya.LayerInfo(189, 0)).is_empty()
    assert region(ring, rt, pya.LayerInfo(189, 0)).is_empty()
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    layers = { (i.layer, i.datatype) for i in ly.layer_infos()+ring.layer_infos() }
    before = {key: region(ly, top, pya.LayerInfo(*key)) for key in layers}
    added = {key: region(ring, rt, pya.LayerInfo(*key)) for key in layers}
    instances = sorted((i.cell.name, str(i.trans)) for i in top.each_inst())
    texts = text_records(ly, top)
    errors = []
    for metal in METALS:
        if not before.get((metal, 0), pya.Region()).interacting(added.get((metal, 0), pya.Region())).is_empty():
            errors.append(['same metal contact', metal])
    for cut, lo, hi in CUTS:
        for metal in (lo, hi):
            if not before.get((metal, 0), pya.Region()).interacting(added.get((cut, 0), pya.Region())).is_empty():
                errors.append(['ring cut touches chip metal', cut, metal])
            if not added.get((metal, 0), pya.Region()).interacting(before.get((cut, 0), pya.Region())).is_empty():
                errors.append(['chip cut touches ring metal', cut, metal])
    (a.output/'contact_gate.json').write_text(json.dumps(dict(status='failed' if errors else 'passed', errors=errors), indent=2)+'\n')
    assert not errors, errors
    for key, polys in added.items():
        assert (polys-die).is_empty(), key
        for poly in polys.each():
            top.shapes(ly.layer(*key)).insert(poly)
    # Copy annotations at their actual transformed coordinates, without copying
    # or renaming native cells. No new hierarchy or connectivity labels invented.
    for index in ring.layer_indexes():
        info = ring.get_info(index)
        iterator = rt.begin_shapes_rec(index)
        while not iterator.at_end():
            if iterator.shape().is_text():
                top.shapes(ly.layer(info.layer, info.datatype)).insert(
                    iterator.shape().text.transformed(iterator.trans()))
            iterator.next()
    expected_texts = sorted(texts+text_records(ring, rt))
    assert text_records(ly, top) == expected_texts
    assert sorted((i.cell.name, str(i.trans)) for i in top.each_inst()) == instances
    for key in layers:
        assert (region(ly, top, pya.LayerInfo(*key)) ^ (before[key]+added[key])).is_empty(), key
    assert top.bbox() == die.bbox()
    output = a.output/'sealed_native.gds'; ly.write(str(output))
    saved = pya.Layout(); saved.read(str(output)); st = saved.top_cell()
    assert text_records(saved, st) == expected_texts
    assert sorted((i.cell.name, str(i.trans)) for i in st.each_inst()) == instances
    for key in layers:
        assert (region(saved, st, pya.LayerInfo(*key)) ^ region(ly, top, pya.LayerInfo(*key))).is_empty()
    result = dict(status='passed exact additive isolated sealring assembly', GDS_sha256=sha(output),
        native_GDS_sha256=sha(source), sealring_GDS_sha256=sha(ringsource),
        sealring_proof_sha256=sha(a.sealring_drc/'summary.json'), script_sha256=sha(Path(__file__)),
        native_direct_instances_retained=len(instances), topcell=top.name,
        native_geometry_texts_instances_roundtrip='passed', metal_cut_contact_gate='passed',
        density_boundary=dict(source='EdgeSeal.boundary 39/4; prBoundary 189/0 absent',
                              bbox_dbu=[0, 0, 1414000, 1414000], area_um2=1999396),
        not_run=['assembled stock main/maximal DRC', 'density/fill', 'antenna',
                 'complete supply connectivity/LVS/PEX/currentIR/EM', 'electrical adoption'],
        not_applicable=['sealring electrical grounding qualification from geometric isolation'])
    (a.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2)); faulthandler.cancel_dump_traceback_later()


if __name__ == '__main__':
    main()
