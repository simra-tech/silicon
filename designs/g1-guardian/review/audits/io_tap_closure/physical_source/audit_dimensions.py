#!/usr/bin/env python3
"""Raw-polygon inventory before any project-local tap source mutation."""
import argparse
import collections
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import pya

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from audit_pinned_taps import records, number
PDK = Path('/foss/pdks/ihp-sg13g2')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def polygon_record(poly):
    rings = [list(poly.each_point_hull())]+[list(poly.each_point_hole(i)) for i in range(poly.holes())]
    areas, perimeters = [], []
    for points in rings:
        assert len(points) >= 4
        pairs = list(zip(points, points[1:]+points[:1]))
        assert all(p.x == q.x or p.y == q.y for p,q in pairs)
        areas.append(abs(sum(p.x*q.y-q.x*p.y for p,q in pairs)))
        perimeters.append(sum(abs(p.x-q.x)+abs(p.y-q.y) for p,q in pairs))
    assert areas[0]-sum(areas[1:]) == 2*poly.area()
    assert sum(perimeters) == poly.perimeter()
    shape = 'rectangle' if poly.is_box() else 'other Manhattan shape'
    if len(rings) == 2 and len(rings[0]) == len(rings[1]) == 4:
        shape = 'rectangular ring; width uniformity not yet established'
    return dict(area_dbu2=poly.area(), perimeter_dbu=poly.perimeter(),
                area_um2=str(Decimal(poly.area())/Decimal(1000000)),
                perimeter_um=str(Decimal(poly.perimeter())/Decimal(1000)),
                classification=shape, hull_and_holes=[[[p.x,p.y] for p in ring] for ring in rings],
                bbox_dbu=str(poly.bbox()), independent_shoelace_and_edge_lengths='passed')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    assert (PDK/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    gds = PDK/'libs.ref/sg13g2_io/gds/sg13g2_io.gds'
    cdl = PDK/'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl'
    spi = PDK/'libs.ref/sg13g2_io/spice/sg13g2_io.spi'
    assert sha(gds) == '4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825'
    assert sha(cdl) == '7a30e902099e8a8f85e0ae853167904df3793357a793a7b4dc82237b72b3eec4'
    assert sha(spi) == '1d53ab7df431b717ef5aff43e1117c0224681d5cc84886da37a319280ee958d6'
    rules = PDK/'libs.tech/klayout/tech/lvs/rule_decks'
    paths = [gds, cdl, spi, Path(__file__).resolve(), HERE.parent/'audit_pinned_taps.py']
    paths += [rules/n for n in ('layers_definitions.lvs','general_derivations.lvs','tap_derivations.lvs','tap_connections.lvs')]
    paths += [PDK/'libs.tech/xschem/sg13g2_pr'/n for n in ('ptap1.sym','ptap1_ring.sym','ntap1.sym')]
    inputs = {str(p):sha(p) for p in paths}
    layers = {m[1]:(int(m[2]),int(m[3])) for m in re.finditer(r'(?m)^(\w+)\s*=\s*get_polygons\((\d+),\s*(\d+)\)', paths[5].read_text())}
    source = records(cdl.read_text())
    assert len(source) == 63
    bycell = collections.defaultdict(list)
    for row in source:
        bycell[row['cell']].append(row)
    spice = {(r['cell'],r['instance']):r for r in records(spi.read_text())}
    ly = pya.Layout(); ly.read(str(gds)); assert ly.dbu == .001
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running raw geometry inventory', inputs=inputs, cells=[])
    cache = {}

    def derive(cell):
        if cell.cell_index() in cache:
            return cache[cell.cell_index()]
        def region(name):
            return pya.Region(cell.begin_shapes_rec(ly.layer(*layers[name]))).merged()
        active = region('activ_drw')+region('activ_filler')
        nw, psd = region('nwell_drw'), region('psd_drw')
        gap = region('digisub_drw')-region('digisub_drw').sized(-1)
        pwell = pya.Region(cell.bbox())-region('pwell_block')-nw-gap
        marker_regions = {'ptap1':region('substrate_drw') & pwell, 'ntap1':nw}
        labels = {'ptap1':[], 'ntap1':[]}
        it = cell.begin_shapes_rec(ly.layer(63,0))
        while not it.at_end():
            shape = it.shape()
            if shape.is_text():
                text = shape.text.transformed(it.trans())
                key = {'sub!':'ptap1','well':'ntap1'}.get(text.string.lower())
                if key:
                    labels[key].append(pya.Point(text.x,text.y))
            it.next()
        selected = {}
        for kind, region in marker_regions.items():
            selected[kind] = pya.Region()
            for poly in region.each():
                if any(poly.inside(point) for point in labels[kind]):
                    selected[kind].insert(poly)
        excluded = pya.Region()
        for name in ('gatpoly_drw','gatpoly_filler','nsd_drw','trans_drw','emwind_drw','emwihv_drw',
                     'salblock_drw','polyres_drw','extblock_drw','res_drw','activ_mask','recog_diode','ind_drw','ind_pin'):
            excluded += region_by_name(cell, name)
        derived = {'ptap1':((active & psd) & selected['ptap1'])-nw-excluded,
                   'ntap1':((active-psd-region_by_name(cell,'nsd_block')) & selected['ntap1'])-pwell-psd-excluded}
        value = {k:v.merged() for k,v in derived.items()}
        cache[cell.cell_index()] = value
        return value

    def region_by_name(cell, name):
        return pya.Region(cell.begin_shapes_rec(ly.layer(*layers[name]))).merged()

    try:
        for name, rows in sorted(bycell.items()):
            cell = ly.cell(name); assert cell is not None
            total = derive(cell)
            inherited = {k:pya.Region() for k in total}
            for inst in cell.each_inst():
                child = derive(inst.cell)
                for transform in inst.cell_inst.each_cplx_trans():
                    for kind, reg in child.items():
                        inherited[kind] += reg.transformed(transform)
            dimensions = {}
            for kind, reg in total.items():
                own = (reg-inherited[kind]).merged()
                polygons = [polygon_record(p) for p in own.each()]
                dimensions[kind] = dict(total_area_dbu2=reg.area(), inherited_area_dbu2=(reg & inherited[kind]).area(),
                    local_area_dbu2=own.area(), local_perimeter_dbu=own.perimeter(), polygons=polygons,
                    inherited_outside_parent_area_dbu2=(inherited[kind]-reg).area())
            result['cells'].append(dict(cell=name, source_taps=rows,
                original_electrical=[spice[(name,r['instance'])] for r in rows], dimensions=dimensions,
                source_geometry_bijection='not run; no source parameter replacement from aggregate inventory'))
        assert all(sha(Path(p)) == h for p,h in inputs.items())
        result.update(status='passed raw source-cell geometry inventory; source mapping pending',
            source_taps=63, native_cells=len(bycell), source_replacement='not run',
            electrical_R_derivation='not run; rectangle/ring perimeter convention remains separate',
            fullchip_instanced_geometry='not run', native_LVS='not run', model_rule_changes='not applicable')
    except Exception as exc:
        result.update(status='failed raw geometry inventory', error=repr(exc))
        raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
