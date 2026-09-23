#!/usr/bin/env python3
"""Map raw tap polygons through real contacts to native source-port labels."""
import argparse
import collections
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import pya

METALS = (8,10,30,50,67,126,134)
CUTS = {19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134),6:(8,300)}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def polygon(row):
    rings = [[pya.Point(*p) for p in ring] for ring in row['hull_and_holes']]
    p = pya.Polygon(rings[0])
    for hole in rings[1:]:
        p.insert_hole(hole)
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    dimensions = bulk/'io-tap-physical-dimensions-20260923-r2/analysis.json'
    data = json.loads(dimensions.read_text())
    assert data['status'] == 'passed raw source-cell geometry inventory; source mapping pending'
    assert all(sha(Path(p)) == h for p,h in data['inputs'].items())
    gds = Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds')
    inputs = {str(p):sha(p) for p in (dimensions,gds,Path(__file__).resolve())}
    ly = pya.Layout(); ly.read(str(gds)); assert ly.dbu == .001
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running native ownership', inputs=inputs, cells=[], source_parameter_changes='not run')
    failures = []
    try:
        for row in data['cells']:
            cell = ly.cell(row['cell']); assert cell is not None
            flat = pya.Layout(); flat.dbu = ly.dbu; top = flat.create_cell('physical_tap_ownership')
            for layer in METALS+tuple(CUTS):
                reg = pya.Region(cell.begin_shapes_rec(ly.layer(layer,0))).merged()
                if layer in METALS:
                    reg += pya.Region(cell.begin_shapes_rec(ly.layer(layer,22)))
                    reg -= pya.Region(cell.begin_shapes_rec(ly.layer(layer,24)))
                top.shapes(flat.layer(layer,0)).insert(reg)
            own = []
            for kind, geometry in row['dimensions'].items():
                for index, poly in enumerate(geometry['polygons']):
                    shape = polygon(poly)
                    top.shapes(flat.layer(300,0)).insert(shape)
                    own.append((kind,index,poly,shape))
            ltn = pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,top,[]))
            layers = {k:ltn.make_layer(flat.layer(k,0),'L%d'%k) for k in METALS+(300,)+tuple(CUTS)}
            for layer in layers.values():
                ltn.connect(layer)
            for cut,ends in CUTS.items():
                for end in ends:
                    ltn.connect(layers[cut],layers[end])
            ltn.extract_netlist()
            targets = {r['terminals'][0] for r in row['source_taps']}
            bindings = collections.defaultdict(set); labels = []
            for layer in METALS:
                for shape in cell.shapes(ly.layer(layer,25)).each():
                    if not shape.is_text() or shape.text.string not in targets:
                        continue
                    text = shape.text; n = ltn.probe_net(layers[layer],pya.Point(text.x,text.y))
                    labels.append(dict(name=text.string,layer=layer,point=[text.x,text.y],cluster=n.cluster_id if n else None))
                    if n:
                        bindings[text.string].add(n.cluster_id)
            mapping = collections.defaultdict(list); polygon_rows = []
            contacts = pya.Region(cell.begin_shapes_rec(ly.layer(6,0))).merged()
            for kind,index,poly,shape in own:
                cuts = contacts & pya.Region(shape)
                nets = set()
                for cut in cuts.each():
                    point = cut.bbox().center()
                    n = ltn.probe_net(layers[6],point)
                    if n:
                        nets.add(n.cluster_id)
                matches = [name for name,clusters in bindings.items() if nets and nets <= clusters]
                passed = len(matches) == 1 and len(nets) == 1
                polygon_rows.append(dict(model=kind,index=index,contacts=cuts.count(),clusters=sorted(nets),source_port_matches=matches,passed=passed))
                if passed:
                    mapping[(kind,matches[0])].append(poly)
                else:
                    failures.append(dict(cell=row['cell'],polygon=index,model=kind,detail=polygon_rows[-1]))
            source_rows = []
            for tap in row['source_taps']:
                polys = mapping.get((tap['model'],tap['terminals'][0]),[])
                area = sum((Decimal(p['area_um2']) for p in polys),Decimal(0))
                perimeter = sum((Decimal(p['perimeter_um']) for p in polys),Decimal(0))
                source_rows.append(dict(source=tap,owned_polygon_count=len(polys),area_um2=str(area),perimeter_um=str(perimeter),
                    polygons=polys,original_electrical=next(r for r in row['original_electrical'] if r['instance'] == tap['instance']),
                    electrical_formula_applicability='not yet selected'))
                if not polys:
                    failures.append(dict(cell=row['cell'],source=tap['instance'],detail='no uniquely owned polygon'))
            result['cells'].append(dict(cell=row['cell'],labels=labels,port_clusters={n:sorted(v) for n,v in bindings.items()},
                polygon_mapping=polygon_rows,taps=source_rows))
        assert all(sha(Path(p)) == h for p,h in inputs.items())
        result.update(status='passed per-tap local native ownership' if not failures else 'failed one or more native ownership mappings',
            failures=failures,source_taps=sum(len(r['taps']) for r in result['cells']),
            forced_net_joins='not applicable; labels only probed, never connected',
            fullchip_instance_context='not run',independent_negative_controls='not run',electrical_R='not run',strict_LVS='not run')
    except Exception as exc:
        result.update(status='failed ownership harness',error=repr(exc))
        raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    raise SystemExit(0 if not failures else 1)


if __name__ == '__main__':
    main()
