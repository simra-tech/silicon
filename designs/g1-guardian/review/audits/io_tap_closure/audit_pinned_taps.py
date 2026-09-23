#!/usr/bin/env python3
"""Read-only pinned IO tap reference/shape applicability audit; no LVS rewrite."""
import argparse
import collections
import datetime
from decimal import Decimal, getcontext
import hashlib
import json
import os
from pathlib import Path
import re
import pya

getcontext().prec = 50
HERE = Path(__file__).resolve().parent
AUDITS = HERE.parent
PDK = Path('/foss/pdks/ihp-sg13g2')
SCALE = {'': Decimal(1), 'm': Decimal('1e-3'), 'u': Decimal('1e-6'),
         'n': Decimal('1e-9'), 'p': Decimal('1e-12'), 'f': Decimal('1e-15'), 'k': Decimal('1e3')}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def number(token):
    match = re.fullmatch(r'([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?)([a-z]?)', token, re.I)
    assert match is not None, token
    return Decimal(match[1]) * SCALE[match[2].lower()]


def records(text):
    rows, cell = [], None
    for lineno, line in enumerate(text.splitlines(), 1):
        match = re.match(r'^\.subckt\s+(\S+)', line, re.I)
        if match:
            cell = match[1]
        if re.match(r'^\.ends', line, re.I):
            cell = None
        if re.match(r'^\s*[xR]\S+\s+\S+\s+\S+\s+[pn]tap1\s', line, re.I):
            fields = line.split()
            params = {m[0].upper(): m[1] for m in re.findall(r'(\w+)=(\S+)', line)}
            rows.append(dict(cell=cell, source_line=lineno, instance=fields[0], model=fields[3],
                             terminals=fields[1:3], parameters=params, source=line))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    a = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1
    gate = json.loads(a.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    assert (PDK / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    assert pya.__version__ == '0.30.9'
    cdl = PDK / 'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl'
    spice = PDK / 'libs.ref/sg13g2_io/spice/sg13g2_io.spice'
    gds = PDK / 'libs.ref/sg13g2_io/gds/sg13g2_io.gds'
    assert sha(cdl) == '7a30e902099e8a8f85e0ae853167904df3793357a793a7b4dc82237b72b3eec4'
    assert sha(spice) == '1d53ab7df431b717ef5aff43e1117c0224681d5cc84886da37a319280ee958d6'
    assert sha(gds) == '4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825'
    a.output.mkdir(exist_ok=False)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    sr = {(r['cell'], r['instance']): r for r in records(spice.read_text())}
    rows = records(cdl.read_text())
    for row in rows:
        A = number(row['parameters']['A']) * Decimal('1e12')
        p_key = 'P' if 'P' in row['parameters'] else 'PERIM'
        P = number(row['parameters'][p_key]) * Decimal('1e6')
        delta = P * P - 16 * A
        electrical = sr[(row['cell'], row['instance'])]
        assert row['terminals'] == electrical['terminals'] and row['model'] == electrical['model']
        R = number(electrical['parameters']['R'])
        predicted = Decimal(980) / (A + P)
        row.update(perimeter_parameter_key=p_key, A_um2=str(A), P_um=str(P), P_squared_minus_16A_um2=str(delta),
                   manhattan_necessary_bound='failed exact reference values' if delta < 0 else 'passed necessary bound only',
                   equivalent_square_P_um=str(4 * A.sqrt()),
                   P_relative_to_square=str(P / (4 * A.sqrt())),
                   literal_CbTapCalc_R_ohm=str(predicted), stock_SPICE_R_ohm=str(R),
                   literal_formula_relative_R_difference=str((predicted - R) / R),
                   spice_source=electrical['source'], spice_source_line=electrical['source_line'])
    bycell = collections.defaultdict(list)
    for row in rows:
        bycell[row['cell']].append(row)
    # Read native raw LevelUp geometry as independent corroboration of the
    # already saved stock extraction; do not build a new comparison reference.
    layout = pya.Layout()
    layout.read(str(gds))
    cell = layout.cell('sg13g2_LevelUpInv')
    def region(n):
        return pya.Region(cell.begin_shapes_rec(layout.layer(n, 0))).merged()
    tap = (region(1) & region(14)) - region(31) - region(5) - region(28) - region(111) - region(128)
    polygons = []
    for poly in tap.each():
        points = list(poly.each_point_hull())
        orthogonal = all(p.x == q.x or p.y == q.y for p, q in zip(points, points[1:] + points[:1]))
        polygons.append(dict(area_dbu2=poly.area(), perimeter_dbu=poly.perimeter(),
                             bbox_dbu=[poly.bbox().left, poly.bbox().bottom, poly.bbox().right, poly.bbox().top],
                             orthogonal_hull=orthogonal, holes=poly.holes(), is_box=poly.is_box()))
    level = bycell['sg13g2_LevelUpInv']
    assert len(level) == 1
    assert level[0]['manhattan_necessary_bound'] == 'failed exact reference values'
    assert polygons and all(p['orthogonal_hull'] and p['holes'] == 0 for p in polygons)
    level_geo = dict(polygons=polygons, dbu_um=layout.dbu, area_um2=tap.area() * layout.dbu**2,
                     perimeter_um=sum(p['perimeter_dbu'] for p in polygons) * layout.dbu)
    saved = AUDITS / 'io-tap-binding-lvs-levelup-20260922-r1/tap_warning_analysis.json'
    saved_rows = json.loads(saved.read_text())['rows']
    normalized = next(r for r in saved_rows if r['variant'] == 'normalized')
    assert normalized['tap_pair_status'] == 'MatchWithWarning'
    assert normalized['layout_tap']['parameters'] == {'A': level_geo['area_um2'], 'P': level_geo['perimeter_um']}
    code_paths = [
        'libs.tech/klayout/tech/lvs/rule_decks/custom_devices.lvs',
        'libs.tech/klayout/tech/lvs/rule_decks/custom_combiner.lvs',
        'libs.tech/klayout/tech/lvs/rule_decks/custom_reader.lvs',
        'libs.tech/klayout/tech/lvs/rule_decks/tap_derivations.lvs',
        'libs.tech/klayout/tech/lvs/rule_decks/tap_extraction.lvs',
        'libs.tech/klayout/tech/lvs/rule_decks/tap_connections.lvs',
        'libs.tech/klayout/tech/lvs/README.md',
        'libs.tech/xschem/sg13g2_pr/ptap1.sym',
        'libs.tech/xschem/sg13g2_pr/ptap1_ring.sym',
        'libs.tech/ngspice/models/resistors_mod.lib',
        'libs.tech/klayout/python/sg13g2_pycell_lib/ihp/utility_functions.py',
        'libs.ref/sg13g2_io/doc/README.md']
    evidence = []
    for relative in code_paths:
        p = PDK / relative
        lines = p.read_text().splitlines()
        hits = [i for i, line in enumerate(lines) if re.search(r'CustomTap|TapDeviceCombiner|ptap1|ntap1|CbTapCalc|disable_tap|DISABLE_TAP|equal_parameters|PERIM|^lvs_format=|^format=|generated|CDL|18.06.2026', line, re.I)]
        selected = set(j for i in hits for j in range(max(0, i - 2), min(len(lines), i + 12)))
        evidence.append(dict(path=relative, sha256=sha(p), selected_lines=[dict(line=i + 1, text=lines[i]) for i in sorted(selected)]))
    summary = dict(status='passed read-only reference applicability audit; strict IO LVS remains failed',
                   pdk_commit=(PDK / 'COMMIT').read_text().strip(), klayout=pya.__version__,
                   checks=dict(pinned_IO_views='passed', source_SPICE_CDL_terminal_model_pairing='passed',
                               exact_decimal_all_tap_inventory='passed', LevelUp_native_Manhattan_shape='passed',
                               LevelUp_saved_stock_extract_parameter_parity='passed',
                               LevelUp_source_Manhattan_bound='failed', strict_native_IO_LVS='failed prior bound run',
                               new_LVS='not run', source_geometry_deck_model_changes='not run', stochastic_seed='not applicable'),
                   tap_records=len(rows), tap_cells=len(bycell),
                   exact_Manhattan_bound_failures=sum(r['manhattan_necessary_bound'].startswith('failed') for r in rows),
                   unitless_P_rows=[r['cell'] + ':' + r['instance'] for r in rows if re.fullmatch(r'[-+0-9.eE]+', r['parameters'][r['perimeter_parameter_key']])],
                   levelup_native=level_geo, rows=rows,
                   limitations=['P^2 >= 16A applies to orthogonal regions, not arbitrary curved/non-Manhattan shapes.',
                                'Failure of this necessary bound is separate from small decimal rounding and the much larger existing native perimeter mismatch.',
                                'No extraction-derived replacement schematic or electrical interpretation is authorized by this audit.'],
                   inputs={str(p.relative_to(PDK)): sha(p) for p in (cdl, spice, gds)},
                   saved_evidence={str(saved.relative_to(AUDITS)): sha(saved)}, worker_sha256=sha(Path(__file__)))
    (a.output / 'pinned_code_evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    (a.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('rows', 'inputs', 'saved_evidence')}, indent=2))


if __name__ == '__main__':
    main()
