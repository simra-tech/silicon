#!/usr/bin/env python3
"""Check only the new DVBE overlay against the held complete b417 parent."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import pya

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'coordinated_supply_followup_20260923'))
from check_full_context_flat import sha, dump, region, METALS, CUTS, graph, flatten_conductors, PAIRS, hierarchy_control


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0)) == {48}
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    parent = bulk/'bgr-supply-context-candidate-20260923-r1/supply_context_native.gds'
    local = bulk/'bgr-dvbe-cuts-candidate-20260923-r1/bank.gds'
    prior = bulk/'bgr-supply-candidate-20260923-r1/bank.gds'
    overlay = bulk/'bgr-dvbe-cuts-candidate-20260923-r1/redundant_cuts_overlay.gds'
    preparation = local.with_name('preparation.json')
    routes = bulk/'bgr-assembly-20260922-r5/routing.json'
    assert sha(parent) == 'b417a132626fd1d0f4cc8162c49449868f33096a8069bc7b90408864a0b0e5de'
    assert sha(local) == 'dfcd9e5a5c309c6f490c09aa25b71f3a4294c1acabc4cfc723010f53a283555a'
    assert sha(prior) == 'e3ecfc6208fcae71c6b2f4223b7db3900677acfe30987b50ba6365c720297feb'
    prep = json.loads(preparation.read_text())
    assert prep['status'] == 'passed preparation' and prep['gds_sha256'] == sha(local)
    assert prep['overlay_sha256'] == sha(overlay)
    paths = [parent, local, prior, overlay, preparation, routes, Path(__file__).resolve(),
             HERE.parent/'coordinated_supply_followup_20260923/check_full_context_flat.py']
    inputs = {str(p): sha(p) for p in paths}
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    start = time.monotonic()
    result = dict(status='running', inputs=inputs)
    dump(a.output/'analysis.json', result)
    try:
        result['controls'] = hierarchy_control()
        ly = pya.Layout()
        ly.read(str(parent))
        top = ly.top_cell()
        fl, ft, counts = flatten_conductors(ly, top)
        pg, ps = graph(fl, ft, True)
        cl = pya.Layout()
        cl.read(str(local))
        ct = cl.top_cell()
        cf, cft, local_counts = flatten_conductors(cl, ct)
        cg, cs = graph(cf, cft)
        old = pya.Layout()
        old.read(str(prior))
        old_top = old.top_cell()
        ol = pya.Layout()
        ol.read(str(overlay))
        ot = ol.top_cell()
        transform = pya.ICplxTrans(1, 0, False, 331000, 732000)
        bindings, local_bindings = {}, {}
        probes = json.loads(routes.read_text())['source_probes']
        for probe in probes:
            layer = PAIRS[probe['layer']][0]
            point = pya.Point(*probe['point'])
            pn = pg.probe_net(ps[(layer, 0)], transform*point)
            cn = cg.probe_net(cs[(layer, 0)], point)
            assert pn and cn
            bindings.setdefault(probe['net'], set()).add(pn.cluster_id)
            local_bindings.setdefault(probe['net'], set()).add(cn.cluster_id)
        for bound in (bindings, local_bindings):
            assert len(bound) == 55 and all(len(v) == 1 for v in bound.values())
            assert len({next(iter(v)) for v in bound.values()}) == 55
        probe = next(p for p in probes if p['net'] == 'dvbe')
        pn = pg.probe_net(ps[(PAIRS[probe['layer']][0], 0)], transform*pya.Point(*probe['point']))
        rows = []
        for layer in METALS+tuple(CUTS):
            original = region(old_top, old.layer(layer, 0))
            actual = region(ct, cl.layer(layer, 0))
            requested = region(ot, ol.layer(layer, 0))
            assert (actual ^ (original+requested)).is_empty()
            delta = actual-original
            if delta.is_empty():
                continue
            added = delta.transformed(transform)
            material = region(top, ly.layer(layer, 0))
            owned = pg.shapes_of_net(pn, ps[(layer, 0)], True)
            if layer in METALS:
                material += region(top, ly.layer(layer, 22))
                owned += pg.shapes_of_net(pn, ps[(layer, 22)], True)
            foreign = material-owned
            overlap = added & foreign
            proximity = added.sized(250) & foreign if layer in METALS else pya.Region()
            captures = {}
            if layer in METALS:
                for cut, ends in CUTS.items():
                    if layer in ends:
                        fc = region(top, ly.layer(cut, 0))-pg.shapes_of_net(pn, ps[(cut, 0)], True)
                        captures[str(cut)] = [str(p.bbox()) for p in (added & fc).each()]
            else:
                for end in CUTS[layer]:
                    fm = region(top, ly.layer(end, 0))-pg.shapes_of_net(pn, ps[(end, 0)], True)
                    fm += region(top, ly.layer(end, 22))-pg.shapes_of_net(pn, ps[(end, 22)], True)
                    captures[str(end)] = [str(p.bbox()) for p in (added & fm).each()]
            rows.append(dict(net='dvbe', layer=layer, added_area_um2=added.area()*1e-6,
                passed=overlap.is_empty() and proximity.is_empty() and not any(captures.values()),
                foreign_overlap=[str(p.bbox()) for p in overlap.each()],
                foreign_proximity=[str(p.bbox()) for p in proximity.each()], foreign_capture=captures))
        assert rows and all(sha(Path(p)) == h for p, h in inputs.items())
        result.update(status='passed held-parent source-owned clearance' if all(r['passed'] for r in rows) else 'failed held-parent clearance',
            checks=rows, source_probe_count=len(probes), all55_source_nets_distinct=True,
            exact_local_parent_plus_overlay_XOR=True, exact_flat_counts=counts, local_counts=local_counts,
            final_digital_reroute_context='not run; parent has previous digital geometry',
            fullchip_LVS='not run', candidate_integration='not run', adoption='not run')
        assert all(r['passed'] for r in rows), rows
    except Exception as exc:
        result.update(status='failed parent-context gate', error=repr(exc))
        raise
    finally:
        result['wall_s'] = time.monotonic()-start
        dump(a.output/'analysis.json', result)
        print(json.dumps({k: v for k, v in result.items() if k not in ('inputs', 'exact_flat_counts', 'local_counts')}, indent=2))


if __name__ == '__main__':
    main()
