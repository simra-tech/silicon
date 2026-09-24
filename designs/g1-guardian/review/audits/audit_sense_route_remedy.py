#!/usr/bin/env python3
"""Independent GDS-difference and physical-connectivity diagnostics, not stock LVS."""
import argparse
import hashlib
import json
from pathlib import Path
import pya

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('candidate', type=Path)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--parity-reference', type=Path,
                    help='Compare all nontext polygons against a saved diagnostic candidate')
a = parser.parse_args()
assert not a.output.exists()
root = Path(__file__).resolve().parents[4]
source = root / 'build/scratch/pad-outward-dummy-clean-20260921/g1_chip_top.gds'
ly = pya.Layout()
ly.read(str(a.candidate))
old = pya.Layout()
old.read(str(source))
top = ly.cell('g1_chip_top')
oldtop = old.cell('g1_chip_top')
assert ly.dbu == old.dbu
dbu = ly.dbu
expected_layers = {(30, 0), (49, 0), (50, 0), (30, 22), (50, 22)}
keys = {(q.layer, q.datatype) for layout in (ly, old) for q in layout.layer_infos()}
diffs = []
for key in sorted(keys):
    before = pya.Region(oldtop.begin_shapes_rec(old.layer(*key))).merged()
    after = pya.Region(top.begin_shapes_rec(ly.layer(*key))).merged()
    xor = before ^ after
    if not xor.is_empty():
        diffs.append({'layer': list(key), 'area_um2': xor.area() * dbu ** 2,
                      'bbox_um': str(xor.bbox().to_dtype(dbu))})
assert {tuple(r['layer']) for r in diffs} == expected_layers, diffs
network = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, top, []))
metal_numbers = [8, 10, 30, 50, 67, 126, 134]
metals = {}
for number in metal_numbers:
    metals[number] = network.make_layer(ly.layer(number, 0), f'M{number}')
    network.connect(metals[number])
for cut, lower, upper in zip([19, 29, 49, 66, 125, 133], metal_numbers, metal_numbers[1:]):
    via = network.make_layer(ly.layer(cut, 0), f'V{cut}')
    network.connect(via)
    network.connect(via, metals[lower])
    network.connect(via, metals[upper])
network.extract_netlist()
points = [('P_pad', 30, 1029.12, 493.5), ('P_macro', 30, 982, 465),
          ('P_wire', 50, 1024.5, 478), ('N_pad', 30, 1029.12, 605.22),
          ('N_macro', 30, 982, 459), ('N_wire', 50, 1021, 478),
          ('VDD_ring', 50, 1033, 478), ('supply_1', 126, 997, 478),
          ('supply_2', 126, 1017, 478), ('supply_3', 126, 982.7, 478)]
probes = {}
for name, layer, x, y in points:
    net = network.probe_net(metals[layer], pya.DPoint(x, y).to_itype(dbu))
    probes[name] = None if net is None else {'circuit': net.circuit().name,
                                           'cluster_id': net.cluster_id}
assert all(probes.values()), probes
assert probes['P_pad'] == probes['P_macro'] == probes['P_wire'], probes
assert probes['N_pad'] == probes['N_macro'] == probes['N_wire'], probes
assert probes['P_pad'] != probes['N_pad'], probes
assert all(probes[name] not in (probes['P_pad'], probes['N_pad'])
           for name in ('VDD_ring', 'supply_1', 'supply_2', 'supply_3')), probes
result = {'status': 'passed', 'klayout_version': pya.__version__,
          'candidate_sha256': hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
          'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'nontext_geometry_deltas': diffs, 'probes': probes,
          'scope': 'Whole-layout nontext polygon XOR confined to five intended layers. Physical conductor probes with no labels or virtual net joining; not transistor LVS or exhaustive electrical connectivity proof.',
          'stock_DRC': 'not run', 'pinned_tool_parity': 'not run'}
if a.parity_reference:
    reference = pya.Layout()
    reference.read(str(a.parity_reference))
    reference_top = reference.cell('g1_chip_top')
    assert reference.dbu == dbu
    reference_keys = {(q.layer, q.datatype) for q in reference.layer_infos()} | keys
    parity_differences = []
    for key in sorted(reference_keys):
        expected = pya.Region(reference_top.begin_shapes_rec(reference.layer(*key))).merged()
        actual = pya.Region(top.begin_shapes_rec(ly.layer(*key))).merged()
        difference = actual ^ expected
        if not difference.is_empty():
            parity_differences.append({'layer': list(key), 'area_um2': difference.area() * dbu ** 2})
    result['pinned_tool_parity'] = {
        'status': 'failed' if parity_differences else 'passed',
        'scope': 'Whole-layout nontext polygon XOR; not simulator or extraction parity',
        'reference_sha256': hashlib.sha256(a.parity_reference.read_bytes()).hexdigest(),
        'differences': parity_differences}
    if parity_differences:
        result['status'] = 'failed'
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
if a.parity_reference:
    assert not parity_differences, 'Candidate geometry differs between tool runtimes'
