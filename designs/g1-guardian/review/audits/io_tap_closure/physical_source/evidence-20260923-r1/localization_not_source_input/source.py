#!/usr/bin/env python3
"""Localize independent raw-dimension disagreements; never generate parameters."""
import argparse
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import pya


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    database = bulk/'full-io-marker-lvs-original-20260923-r1/reports/io_marker_native.lvsdb'
    assert sha(database) == '3ed5cd2b78b3d4f4ed724730fcba2388148340d6442249e143c17a9f7ac99f04'
    raw = bulk/'io-tap-physical-dimensions-20260923-r2/analysis.json'
    ownership = bulk/'io-tap-physical-ownership-20260923-r1/analysis.json'
    geometries = {r['cell'].lower():r for r in json.loads(raw.read_text())['cells']}
    owned = {r['cell'].lower():r for r in json.loads(ownership.read_text())['cells']}
    inputs = {str(p):sha(p) for p in (database,raw,ownership,Path(__file__).resolve())}
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running saved-local discrepancy localization', inputs=inputs, circuits=[])
    try:
        db = pya.LayoutVsSchematic(); db.read(str(database))
        for cell in db.netlist().each_circuit():
            devices = []
            for dev in cell.each_device():
                klass = dev.device_class()
                if klass.name.lower() not in ('ptap1','ntap1'):
                    continue
                devices.append(dict(id=dev.id(),name=dev.expanded_name(),model=klass.name,
                    parameters={p.name:dev.parameter(p.name) for p in klass.parameter_definitions()},
                    terminals={t.name:dev.net_for_terminal(t.name).name for t in klass.terminal_definitions()}))
            if not devices:
                continue
            matches = [name for name in geometries if cell.name.lower().endswith(name)]
            row = dict(circuit=cell.name,devices=devices,source_cell_matches=matches)
            if len(matches) == 1:
                name, = matches
                row['independent_raw'] = geometries[name]
                row['independent_ownership'] = owned[name]
                row['deltas'] = []
                for kind in ('ptap1','ntap1'):
                    polygons = geometries[name]['dimensions'][kind]['polygons']
                    area = sum((Decimal(p['area_um2']) for p in polygons),Decimal(0))
                    perimeter = sum((Decimal(p['perimeter_um']) for p in polygons),Decimal(0))
                    observed = [d for d in devices if d['model'].lower() == kind]
                    extracted_a = sum((Decimal(str(d['parameters']['A'])) for d in observed),Decimal(0))
                    extracted_p = sum((Decimal(str(d['parameters']['P'])) for d in observed),Decimal(0))
                    row['deltas'].append(dict(model=kind,independent_A_um2=str(area),independent_P_um=str(perimeter),
                        saved_A_um2=str(extracted_a),saved_P_um=str(extracted_p),
                        area_delta_um2=str(area-extracted_a),perimeter_delta_um=str(perimeter-extracted_p)))
            result['circuits'].append(row)
        assert result['circuits']
        assert all(sha(Path(p)) == h for p,h in inputs.items())
        result.update(status='passed read-only localization; disagreements not normalized',
            source_generation='not applicable',new_extraction='not run',new_source_validation='not run',
            saved_parent_scope='Original ae62 marker parent; geometry applicability checked separately against current native.')
    except Exception as exc:
        result.update(status='failed localization harness',error=repr(exc));raise
    finally:
        (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    main()
