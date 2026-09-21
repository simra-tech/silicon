#!/usr/bin/env python3
"""Ideal-resistor sensitivity from audited GDS positions; not PDK simulation.

R_i = R_unit [1 + gx (x_i-x0) + gy (y_i-y0)]. Identical nominal
units, ideal OTAs, no contact/route R, self-heating, mismatch or gradients
in active devices. Values are deliberately specified perturbations, not
predictions of a physical gradient distribution.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--geometry', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    geometry = json.loads(args.geometry.read_text())
    units = geometry['sense_resistors']['units']
    origin = geometry['sense_resistors']['groups']['R2N']['centroid_um']
    rows = []
    for axis in (0, 1):
        for ppm_per_um in (-10, -1, 0, 1, 10):
            totals = {}
            for r in units:
                scale = 1 + ppm_per_um * 1e-6 * (r['center_um'][axis] - origin[axis])
                assert scale > 0
                totals[r['group']] = totals.get(r['group'], 0) + scale
            kn, kp = totals['R2N'] / totals['R1N'], totals['R2P'] / totals['R1P']
            alpha = (1 + kn) / (1 + kp)
            nominal_fraction = 51 / 53
            ped_fraction = totals['RD2'] / (totals['RD1'] + totals['RD2'])
            for vref in (1.0, 1.04):
                for vcm in (-0.1, 0.0, 0.3):
                    for differential in (0.0, 0.05):
                        vp, vn = vcm + differential / 2, vcm - differential / 2
                        out = alpha * (kp * vp + vref * ped_fraction) - kn * vn
                        ideal = 20 * differential + vref * nominal_fraction
                        rows.append({'axis': 'xy'[axis], 'gradient_ppm_per_um': ppm_per_um,
                                     'vref_V': vref, 'common_mode_V': vcm, 'differential_V': differential,
                                     'R2N_R1N': kn, 'R2P_R1P': kp, 'pedestal_fraction': ped_fraction,
                                     'output_V': out, 'output_error_V': out - ideal,
                                     'input_referred_error_uV': (out - ideal) / 20 * 1e6})
    with args.output.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    meta = {'method': __doc__, 'geometry': str(args.geometry),
            'geometry_sha256': hashlib.sha256(args.geometry.read_bytes()).hexdigest(),
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'command': f'python3 designs/g1-guardian/review/audits/gradient_sensitivity.py --geometry {args.geometry} --output {args.output}',
            'rows': len(rows), 'origin_um': origin,
            'zero_gradient_max_abs_error_uV': max(abs(r['input_referred_error_uV']) for r in rows if r['gradient_ppm_per_um'] == 0),
            'not_run': ['PDK circuit gradient simulation', 'Active-device thermal/gradient simulation',
                        'Physical distribution or yield inference', 'Frozen-calibration drift simulation']}
    args.output.with_suffix('.json').write_text(json.dumps(meta, indent=2) + '\n')
    print(json.dumps(meta, indent=2))


if __name__ == '__main__': main()
