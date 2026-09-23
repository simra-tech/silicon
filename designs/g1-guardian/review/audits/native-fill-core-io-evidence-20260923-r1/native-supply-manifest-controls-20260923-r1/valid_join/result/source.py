#!/usr/bin/env python3
"""Merge hash-bound supply overlays, checking every actual native contact.

The reviewed JSON contract names the parent, frozen evidence predicates,
overlay net seeds (or one declared net), and all native terminal probes.
This integration gate never substitutes for new-context stock DRC/LVS/PEX.
"""
import argparse
import collections
import faulthandler
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region, text_records, sha
from audit_placed_decap_domains import identity
from flat_metal_connectivity import flat_physical
from build_native_decap_pdn import METALS, CUTS, point


def bound_file(record):
    path = Path(record['path'])
    assert path.is_file() and sha(path) == record['sha256'], str(path)
    return path


def predicates(record):
    path = bound_file(record)
    obj = json.loads(path.read_text())
    for assertion in record.get('assertions', []):
        value = obj
        for key in assertion['keys']:
            value = value[key]
        assert value == assertion['equals'], (str(path), assertion, value)
    return obj


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    contract = json.loads(a.contract.read_text())
    assert contract['schema'] == 'native-supply-integration-v1'
    source = bound_file(contract['parent'])
    meta = predicates(contract['parent_metadata'])
    assert meta['GDS_sha256'] == sha(source) and meta['status'].startswith('passed')
    assert meta['native_instances_retained'] == 4904 and meta['decap_pin_pairs_held'] == 9324
    probes = contract['native_probes']
    assert set(probes) == {'VDD', 'VSS', 'VDDA', 'IOVDD', 'IOVSS'}
    assert all('root' in group for group in probes.values())
    assert len({r['name'] for r in contract['overlays']}) == len(contract['overlays'])
    numbers = METALS + tuple(c[0] for c in CUTS)
    overlays = []
    for row in contract['overlays']:
        gds = bound_file(row['gds'])
        assert row['evidence'], 'Frozen geometry and stock evidence are required'
        for evidence in row['evidence']:
            assert evidence.get('assertions'), 'Evidence must have explicit acceptance predicates'
            predicates(evidence)
        ol = pya.Layout(); ol.read(str(gds)); ot = ol.top_cell()
        assert ol.dbu == .001 and not text_records(ol, ot)
        assert bool(row.get('single_net')) != bool(row.get('seeds'))
        overlays.append((row, ol, ot))
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'contract.json').write_bytes(a.contract.read_bytes())
    result = dict(status='running', source_GDS_sha256=sha(source),
                  contract_sha256=sha(a.contract), script_sha256=sha(Path(__file__)))
    faulthandler.dump_traceback_later(60, repeat=True)
    try:
        ly = pya.Layout(); ly.read(str(source)); top = ly.top_cell()
        assert ly.dbu == .001
        net, ml, held = flat_physical(ly, top)
        before = {n: {name: identity(net, ml[q['layer']], q['xy'])
                      for name, q in group.items()} for n, group in probes.items()}
        allowed = {n: set(group.values()) for n, group in before.items()}
        assert all(None not in ids for ids in allowed.values())
        assert all(not (allowed[n] & allowed[m]) for n in allowed for m in allowed if n != m)
        routes = {n: {l: pya.Region() for l in numbers} for n in probes}
        for row, ol, ot in overlays:
            mapping = {}
            if row.get('seeds'):
                on, om, oh = flat_physical(ol, ot)
                for n, seeds in row['seeds'].items():
                    assert n in routes
                    for q in seeds:
                        key = identity(on, om[q['layer']], q['xy'])
                        assert key is not None and mapping.get(key, n) == n
                        mapping[key] = n
            else:
                assert row['single_net'] in routes
            for info in ol.layer_infos():
                polys = region(ol, ot, info)
                if polys.is_empty():
                    continue
                assert info.datatype == 0 and info.layer in numbers
                l = info.layer
                probe = l if l in METALS else next(lo for cut, lo, hi in CUTS if cut == l)
                for poly in polys.each():
                    n = row.get('single_net')
                    if n is None:
                        key = identity(on, om[probe], point(poly))
                        assert key in mapping, (row['name'], l, key)
                        n = mapping[key]
                    routes[n][l].insert(poly)
        native = {l: region(ly, top, pya.LayerInfo(l, 0)) for l in numbers}
        errors = []; counts = collections.Counter()
        def inspect(n, l, polys, reason):
            for poly in polys.each():
                xy = point(poly); actual = identity(net, ml[l], xy); counts[reason] += 1
                if actual not in allowed[n]:
                    errors.append(dict(net=n, layer=l, xy=xy, actual=actual, reason=reason))
        for n, added in routes.items():
            for l in METALS:
                inspect(n, l, native[l].interacting(added[l]), 'new metal touches native metal')
                for other in routes:
                    if n != other:
                        assert added[l].interacting(routes[other][l]).is_empty(), (n, other, l)
            for cut, lo, hi in CUTS:
                for l, opposite in ((lo, hi), (hi, lo)):
                    inspect(n, opposite, native[opposite].interacting(native[cut].interacting(added[l])),
                            'new metal touches old cut')
                    inspect(n, l, native[l].interacting(added[cut]), 'new cut touches native metal')
                    assert (added[cut] - (native[l] + added[l])).is_empty(), (n, cut, l)
                    for other in routes:
                        if n != other:
                            assert added[cut].interacting(routes[other][l]).is_empty(), (n, other, cut, l)
        (a.output/'contact_gate.json').write_text(json.dumps(dict(
            status='failed' if errors else 'passed', errors=errors, counts=dict(counts),
            source_probes=before), indent=2)+'\n')
        assert not errors, errors[:12]
        old = {str(i): region(ly, top, i) for i in ly.layer_infos()}
        texts = text_records(ly, top)
        instances = sorted((i.cell.name, str(i.trans)) for i in top.each_inst())
        assert len(instances) == 4904
        for layers in routes.values():
            for l, polys in layers.items():
                top.shapes(ly.layer(l, 0)).insert(polys)
        output = a.output/'power_connected_native.gds'; ly.write(str(output))
        saved = pya.Layout(); saved.read(str(output)); st = saved.top_cell()
        assert text_records(saved, st) == texts
        assert sorted((i.cell.name, str(i.trans)) for i in st.each_inst()) == instances
        assert set(old) <= {str(i) for i in saved.layer_infos()}
        for info in saved.layer_infos():
            expected = old.get(str(info), pya.Region())
            if info.datatype == 0 and info.layer in numbers:
                for layers in routes.values():
                    expected += layers[info.layer]
            assert (region(saved, st, info) ^ expected).is_empty(), str(info)
        nn, nm, nh = flat_physical(saved, st)
        after = {n: {name: identity(nn, nm[q['layer']], q['xy'])
                     for name, q in group.items()} for n, group in probes.items()}
        assert all(None not in group.values() and len(set(group.values())) == 1 for group in after.values())
        assert len({next(iter(group.values())) for group in after.values()}) == 5
        result.update(status='passed manifest-bound native supply integration', GDS_sha256=sha(output),
                      source_geometry_text_instances_roundtrip='passed', no_foreign_contact='passed',
                      saved_flat_actual_connectivity='passed', before=before, after=after,
                      native_instances_retained=4904, decap_pin_pairs_held=9324,
                      not_run=['new-context main/maximal/antenna/density', 'final signal routing',
                               'device-aware fullchip LVS/PEX', 'current IR EM and electrical adoption'])
    except Exception as exc:
        result.update(status='failed native supply integration', error=repr(exc))
        raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
        faulthandler.cancel_dump_traceback_later()


if __name__ == '__main__':
    main()
