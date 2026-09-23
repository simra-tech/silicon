#!/usr/bin/env python3
"""Read-only staged conductor audit; not a replacement for the stock antenna deck."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import pya

METALS = (8, 10, 30, 50, 67, 126, 134)
CUTS = (19, 29, 49, 66, 125, 133)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2) + '\n')


def region(layout, cell, layer, purpose=0):
    return pya.Region(cell.begin_shapes_rec(layout.layer(layer, purpose))).merged()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gds', type=Path, required=True)
    ap.add_argument('--top', required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--native', action='store_true')
    ap.add_argument('--stages', default='0,1,2,3,4,5,6')
    a = ap.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running', GDS_sha256=sha(a.gds), script_sha256=sha(Path(__file__)))
    start = time.monotonic()
    try:
        assert pya.__version__ == '0.30.9' and len(os.sched_getaffinity(0)) == 1
        ly = pya.Layout(); ly.read(str(a.gds)); top = ly.cell(a.top)
        assert top is not None and ly.dbu == .001
        native = a.native
        if native:
            assert sha(a.gds) == '4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825'
            transforms = [('native_IOPadIn', pya.Trans())]
        else:
            assert sha(a.gds) == '393b485183dc7d7624365a2119590ed1babdf945ce298f848a0b1c228da736c7'
            transforms = [('pad12_en', pya.Trans(pya.Trans.R90, 1273000, 915000)),
                          ('pad14_sclk', pya.Trans(pya.Trans.M0, 467000, 1273000)),
                          ('pad15_sdi', pya.Trans(pya.Trans.M0, 579000, 1273000))]
            instances = [(i.cell.name, str(i.trans)) for i in top.each_inst()]
            for name, tr in transforms:
                found = [(cell, t) for cell, t in instances if t == str(tr) and cell.endswith('sg13g2_IOPadIn')]
                assert len(found) == 1, (name, found)
        raw = {n: region(ly, top, n) for n in set(METALS + CUTS + (1, 5, 6, 14))}
        active = raw[1]; poly = raw[5]
        raw['gate'] = (poly & active).merged()
        raw['field'] = (poly - active).merged()
        nsdblock = region(ly, top, 7, 21)
        raw['diode'] = (((active - poly) - (raw[14] | nsdblock)) | ((active - poly) & raw[14])).merged()
        # Explicit native antenna devices as in the pinned deck; these are
        # derived from recognition layers, recorded separately below.
        gate_local = pya.Box(41540, 166270, 41990, 170920)
        gate_proof = []
        for name, tr in transforms:
            box = tr * gate_local
            got = raw['gate'] & pya.Region(box)
            assert got.area() == gate_local.area() and (got ^ pya.Region(box)).is_empty()
            gate_proof.append(dict(instance=name, transform=str(tr), bbox_dbu=[box.left, box.bottom, box.right, box.top], gate_area_um2=got.area()*1e-6))
        result.update(native_gate_geometry=gate_proof, stages=[])
        dump(a.output / 'summary.json', result)
        for stage in [int(v) for v in a.stages.split(',')]:
            flat = pya.Layout(); flat.dbu = ly.dbu
            cell = flat.create_cell('antenna_stage')
            keys = ['gate', 'field', 'diode', 6] + list(METALS[:stage+1]) + list(CUTS[:stage])
            for index, key in enumerate(keys):
                cell.shapes(flat.layer(index+1, 0)).insert(raw[key])
            l2n = pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat, cell, []))
            layers = {key: l2n.make_layer(flat.layer(index+1, 0), str(key)) for index, key in enumerate(keys)}
            for layer in layers.values(): l2n.connect(layer)
            for lo, hi in [('gate','field'), ('gate',6), ('field',6), ('diode',6), (6,8)]:
                l2n.connect(layers[lo], layers[hi])
            for index, cut in enumerate(CUTS[:stage]):
                l2n.connect(layers[METALS[index]], layers[cut])
                l2n.connect(layers[cut], layers[METALS[index+1]])
            l2n.extract_netlist()
            observations = []
            for name, tr in transforms:
                point = tr * gate_local.center()
                net = l2n.probe_net(layers['gate'], point)
                assert net is not None
                areas = {}
                for key in ['gate', 'diode'] + list(METALS[:stage+1]):
                    area = l2n.shapes_of_net(net, layers[key], True).area()*1e-6
                    areas[str(key)] = area
                # Native annotations are observation points only: never graph joins.
                label_probes = []
                for metal, point in [(30,(41120,171000)), (50,(41365,150595)), (67,(41365,151030)), (126,(41190,152255))]:
                    if metal not in layers: continue
                    p = tr * pya.Point(*point)
                    other = l2n.probe_net(layers[metal], p)
                    label_probes.append(dict(layer=metal, pin='vdd', point_dbu=[p.x,p.y], same_net=other is not None and other.cluster_id == net.cluster_id))
                observations.append(dict(instance=name, cluster_id=net.cluster_id, areas_um2=areas,
                                         current_metal_gate_ratio=areas[str(METALS[stage])]/areas['gate'], vdd_annotation_probes=label_probes))
            entry = dict(stage=stage, metal=METALS[stage], observations=observations, elapsed_seconds=time.monotonic()-start)
            result['stages'].append(entry); dump(a.output/'summary.json', result)
            print(json.dumps(entry), flush=True)
        result.update(status='passed read-only staged connectivity observations', elapsed_seconds=time.monotonic()-start,
                      checks=dict(stock_rerun='not run', geometry_changes='not run', electrical_qualification='not run', seed='not applicable'),
                      scope='Gate/field/ordinary active-derived diode/cont/seven drawn metals/six cuts. No name-based joins. Dedicated antenna recognition devices not yet included; no stock-equivalence claim.')
        dump(a.output / 'summary.json', result)
    except BaseException as exc:
        result.update(status='failed', exception=repr(exc), traceback=traceback.format_exc(), elapsed_seconds=time.monotonic()-start)
        dump(a.output / 'failure.json', result); dump(a.output / 'summary.json', result)
        raise


if __name__ == '__main__':
    main()
