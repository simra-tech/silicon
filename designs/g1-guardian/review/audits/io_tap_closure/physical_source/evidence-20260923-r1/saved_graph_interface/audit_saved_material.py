#!/usr/bin/env python3
"""Quantify saved LVS conductor coverage, including floating TM2 filler."""
import argparse
import json
from pathlib import Path
import pya
from prepare_full_marker import sha, region, PDK


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'database', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    gds = a.candidate / 'route_fill_pruned.gds'
    assert sha(gds) == '4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2'
    assert sha(a.database) == '1b2156355d671e31970482eb3ec8f47b5e4b7bb25d7b111155bfb0ea7306460f'
    ly = pya.Layout(); ly.read(str(gds)); top = ly.top_cell()
    drawn, filler, slit = [region(ly, top, pya.LayerInfo(134, d)) for d in (0, 22, 24)]
    full = (drawn + filler - slit).merged(); actual_drawing = (drawn - slit).merged()
    rules = PDK / 'libs.tech/klayout/tech/lvs'
    definitions = rules / 'rule_decks/layers_definitions.lvs'
    definitions_text = definitions.read_text()
    formula = 'topmetal2 = topmetal2_drw.join(topmetal2_filler).not(topmetal2_slit)'
    assert formula in definitions_text
    snippets = []
    for file in sorted(rules.rglob('*.lvs')):
        lines = file.read_text().splitlines()
        selected = [(i + 1, line) for i, line in enumerate(lines) if any(
            word in line for word in ('topmetal2 =', 'topmetal2_drw =', 'topmetal2_filler =', 'topmetal2_slit =',
                                     '.simplify', '.purge', 'purge_nets', 'topmetal2_con'))]
        if selected:
            snippets.append(dict(file=str(file.relative_to(PDK)), sha256=sha(file), selected_lines=selected))
    db = pya.LayoutVsSchematic(); db.read(str(a.database))
    matches = []
    for index in db.layer_indexes():
        value = db.layer_by_index(index)
        if isinstance(value, pya.Region) and value.bbox() == actual_drawing.bbox() and (value ^ actual_drawing).is_empty():
            missing, extra = full - value, value - full
            matches.append(dict(index=index, name=db.layer_name(index), drawn_XOR_area_dbu2=0,
                                missing_area_um2=missing.area() * 1e-6, missing_polygons=missing.count(),
                                missing_exactly_native_filler=(missing ^ filler).is_empty(),
                                extra_area_um2=extra.area() * 1e-6, extra_empty=extra.is_empty()))
    result = dict(status='running material coverage audit', GDS_sha256=sha(gds), database_sha256=sha(a.database),
                  script_sha256=sha(Path(__file__)), exact_drawn_matches=matches, pinned_rule_snippets=snippets,
                  native_filler_polygons=filler.count(), native_filler_area_um2=filler.area() * 1e-6,
                  filler_drawn_overlap_area_um2=(filler & drawn).area() * 1e-6,
                  full_native_TM2_area_um2=full.area() * 1e-6,
                  caveat='Saved connected-conductor material is not a complete floating-fill PEX domain.')
    assert len(matches) == 1
    assert matches[0]['missing_exactly_native_filler'] and matches[0]['extra_empty']
    assert (filler & drawn).is_empty()
    # Geometric disconnection, not just zero positive-area overlap: touching
    # edges would also couple the fill to the real electrode component.
    assert (filler.interacting(drawn)).is_empty()
    result.update(status='passed exact drawn TM2 coverage; current floating fill count separately recorded',
                  fill_disconnected_from_drawn='passed exact interaction-empty',
                  complete_floating_fill_material_coverage='failed', full_PEX='not run', source_geometry_changes='not applicable')
    assert filler.count() > 0 and filler.area() > 0 # Current held GDS, not old-parent count.
    (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
