#!/usr/bin/env python3
"""Preserve every native contact footprint without choosing a terminal injection."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('ledger', 'contacts', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    ledger = json.loads(args.ledger.read_text()); native = json.loads(args.contacts.read_text())
    assert native['status'] == 'passed read-only native contact enumeration; model attachment not qualified'
    assert native['ledger_sha256'] == sha(args.ledger)
    assert native['source_sha256'] == ledger['source_sha256']
    assert native['GDS_sha256'] == ledger['GDS_sha256'] == '8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7'
    devices = {d['device']: d for d in ledger['devices']}
    footprints = {}; slots = collections.defaultdict(list)
    for index, row in enumerate(native['rows']):
        for contact in row['contacts']:
            box = tuple(contact['bbox_dbu']); assert len(box) == 4
            assert box[2]-box[0] == box[3]-box[1] == 160
            assert contact['external_metal_layer'] == 8 and contact['contact_layer'] == 6
            identity = 'cont_'+hashlib.sha256((','.join(str(x) for x in box)).encode()).hexdigest()[:20]
            owners = []
            for name, adjacent_gates in row['owners'].items():
                terminal = 'G' if row['kind'] == 'gate_poly_component' else row['owner_roles'][name]
                assert devices[name]['terminal_nets'][terminal] == row['source_net']
                owners.append(dict(device=name, terminal=terminal, adjacent_gate_count=adjacent_gates))
                slots[(name, terminal)].append(identity)
            assert identity not in footprints, 'A physical contact was enumerated twice'
            footprints[identity] = dict(id=identity, bbox_dbu=list(box), contact_layer=[6, 0],
                                       covered_metal_layer=[8, 0], source_net=row['source_net'],
                                       owners=owners, native_record_index=index,
                                       selected_point=None, current_weights=None,
                                       equipotential_footprint_assumption=False)
    assert len(footprints) == 19384 and len(slots) == 174
    out_slots = []
    for slot in ledger['slots']:
        key = (slot['device'], slot['terminal']); ids = sorted(slots.get(key, []))
        assert len(ids) == len(set(ids))
        out_slots.append(dict(device=key[0], terminal=key[1], source_net=slot['source_net'],
                              footprint_ids=ids,
                              geometry_enumeration='passed' if ids else 'not run in this contact inventory',
                              source_model_attachment='not qualified', selected_point=None, weights=None))
    assert len(out_slots) == 541 and sum(bool(s['footprint_ids']) for s in out_slots) == 174
    shared = [f for f in footprints.values() if len(f['owners']) > 1]
    assert len(shared) == 816 and all(len(f['owners']) == 2 for f in shared)
    result = dict(status='prepared exact native contact footprints; no injection/mesh/model selected',
                  source_sha256=ledger['source_sha256'], GDS_sha256=ledger['GDS_sha256'],
                  ledger_sha256=sha(args.ledger), contacts_sha256=sha(args.contacts),
                  script_sha256=sha(Path(__file__)), physical_contact_count=len(footprints),
                  shared_contact_count=len(shared), covered_source_slots=174, total_source_slots=541,
                  source_slots=out_slots, footprints=sorted(footprints.values(), key=lambda f: f['id']),
                  planned_geometry_only_domain='M1 through TopMetal2 and Via1 through TopVia2, unchanged physical polygons; no Cont/Poly/Active/resistor/MIM/substrate material assignment',
                  next_controls=['Generalized per-cut area for Via1-4/TopVia1/TopVia2; no hardcoded .19um top-via assumption',
                                 'Positive resistance edges after exact zero-edge contraction',
                                 'Every footprint remains a distributed contact area, not an asserted equipotential PolygonPort',
                                 'No geometric point probe becomes a compact-model current injection without a separately reviewed boundary',
                                 'Do not compose the mesh with source devices or infer current loading from this catalogue'],
                  not_run=['367 remaining slot contact assignments', 'Metal R extraction',
                           'Contact-area PDE/port-boundary qualification', 'Current allocation',
                           'Full11512/wave zeroR parity', 'Intrinsic applicability', 'Electrical adoption'])
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('source_slots', 'footprints')}, indent=2))


if __name__ == '__main__': main()
