#!/usr/bin/env python3
"""Prepare an unadopted physical-unit selective PTAT-loop replication hypothesis."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOS = {34, 35, 36, 37, 38, 39, 41, 45, 47, 48, 50, 52, 54}
HBT = {56, 62, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76}
RES = {16, 23, 24, 25, 26, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--units', type=int, choices=[4, 8, 16], default=16)
    args = parser.parse_args()
    source = HERE.parent / 'postlayout/g1_bgr_pex.spice'
    original = source.read_text()
    expected_hash = '72417e072003d2ce28a108c47ef6ac86927ce6c6f89f3a614f360165a31c9d77'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected_hash
    selected = {'XM'+str(i) for i in MOS} | {'XQ'+str(i) for i in HBT} | {'XR'+str(i) for i in RES}
    lines, additions, mapping, found = [], [], [], set()
    for line in original.splitlines():
        fields = line.split()
        if fields and fields[0] in selected:
            instance = fields[0]
            found.add(instance)
            for unit in range(2, args.units+1):
                name = instance+'_u'+str(unit)
                additions.append(line.replace(instance, name, 1))
                mapping.append({'original': instance, 'new': name})
        if line.lower().startswith('.ends'):
            lines.extend(additions)
        lines.append(line)
    assert found == selected and len(additions) == 40*(args.units-1)
    candidate = '\n'.join(lines)+'\n'
    name = 'bgr_selective_loop'+str(args.units)
    output = HERE / 'candidates' / name
    output.mkdir(exist_ok=False)
    (output/'baseline_pex.spice').write_text(original)
    (output/(name+'.spice')).write_text(candidate)
    manifest = {
        'status': 'prepared; unadopted simulation-only candidate; all checks not run',
        'units': args.units, 'source_sha256': expected_hash,
        'candidate_sha256': hashlib.sha256(candidate.encode()).hexdigest(),
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'replicated_original_instances': sorted(selected), 'added_units': mapping,
        'unchanged_branches': ['startup XM27–33', 'detector XM42/XM49 and XR1–15',
                               'IPTAT XM40/XM46/XM53', 'VREF XM43/XM44/XM51/XQ60 and XR17–22'],
        'hypothesis': 'Replicate only the PTAT and bias-loop current-carrying MOS, HBT and full-length parallel resistor units. Loop current is intended to scale with unit count while original per-unit current density, voltage drops and exported bias voltages remain unchanged. Output and detector mirror branches retain original geometry/current. All of these are hypotheses until nominal qualification.',
        'model_policy': 'Separate original legal Nx=1 HBT and MOS/R units, not artificial random scaling or model edits. Equal seed across different netlists is not a paired physical sample. Spatial mismatch correlation is unknown.',
        'parasitics': 'Baseline extracted wiring capacitance retained plus native added-device capacitances. New placement/wiring/contact/fill extraction is not run.',
        'gates': ['nominal TC/VREF/IPTAT/bias/current and per-unit HBT density',
                  'model-terminal validity', 'local physical footprint feasibility',
                  'all-parameter mismatch qualification before sample expansion',
                  'startup/load/stability/rail/process tests', 'candidate layout DRC/LVS/new PEX'],
    }
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'candidate': name, 'added_units': len(additions), 'sha256': manifest['candidate_sha256']}))


if __name__ == '__main__':
    main()
