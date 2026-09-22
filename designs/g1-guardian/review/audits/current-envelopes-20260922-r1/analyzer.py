#!/usr/bin/env python3
"""Read-only current envelopes from a complete, accepted compact analog fixture."""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
from check_campaign import read_wave


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def integrate_linear_current(times, values):
    if len(times) < 2 or len(times) != len(values) or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('strictly increasing samples required')
    if not all(math.isfinite(x) for x in times + values):
        raise ValueError('nonfinite input')
    span = times[-1] - times[0]
    charge = sum((tb-ta)*(a+b)/2 for ta,tb,a,b in zip(times,times[1:],values,values[1:]))
    square = sum((tb-ta)*(a*a+a*b+b*b)/3 for ta,tb,a,b in zip(times,times[1:],values,values[1:]))
    return dict(mean_A=charge/span, rms_A=math.sqrt(max(0, square/span)),
                sampled_abs_peak_A=max(map(abs, values)), sampled_min_A=min(values),
                sampled_max_A=max(values), charge_C=charge, duration_s=span)


def window_values(times, values, start, end):
    if not times[0] <= start < end <= times[-1]:
        raise ValueError('no window extrapolation allowed')
    def at(t):
        i = bisect.bisect_left(times, t)
        if times[i] == t:
            return values[i]
        return values[i-1] + (values[i]-values[i-1])*(t-times[i-1])/(times[i]-times[i-1])
    interior = [i for i,t in enumerate(times) if start < t < end]
    return [start] + [times[i] for i in interior] + [end], [at(start)] + [values[i] for i in interior] + [at(end)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        ap.error('preserve prior evidence')
    manifest = json.loads((args.run/'run.json').read_text())
    acceptance = json.loads((args.run/'electrical_acceptance.json').read_text())
    wave = args.run/'observations.tsv'
    if (acceptance['status'] != 'passed' or sha(wave) != acceptance['waveform_sha256']
            or manifest['source_deck_sha256'] != '506df5bf09fa11eff7dfc1cc80b5e62ee02b757b25cc0ca4b2771b6226a54a29'):
        ap.error('requires the pinned complete accepted compact c_mid fixture')
    cols, rows = read_wave(wave)
    times = [r[0] for r in rows]
    if abs(times[-1]-28e-6) > 1e-12:
        ap.error('complete28us endpoint required')
    branches = [('BGR','VDDA','i(vm_bgr)'),('SENSE','VDDA','i(vm_sense)'),
                ('TRIP','VDDA','i(vm_tripa)'),('TRIP','VDD','i(vm_tripd)'),
                ('GATE_core','VDDA','i(vm_gatea)'),('GATE_core','VDD','i(vm_gated)')]
    windows = {'complete':(0,28e-6),'armed':(14e-6,15.9e-6),
               'fault_transition':(16e-6,18e-6),'tripped':(20e-6,28e-6)}
    records = []
    for macro,rail,probe in branches:
        values = [r[cols.index(probe)] for r in rows]
        record = dict(macro=macro, rail=rail, probe=probe, windows={})
        for name,(start,end) in windows.items():
            t,v = window_values(times,values,start,end)
            record['windows'][name] = integrate_linear_current(t,v)
        records.append(record)
    args.output.mkdir()
    shutil.copyfile(__file__, args.output/'analyzer.py')
    report = dict(status='passed current extraction; implementation margin not run',
                  run=args.run.name, waveform_sha256=sha(wave), manifest_sha256=sha(args.run/'run.json'),
                  acceptance_sha256=sha(args.run/'electrical_acceptance.json'),
                  checker_sha256=sha(Path(__file__)), runtime_image=manifest['image_id'],
                  pdk_commit=manifest['pdk_commit'], included_sources=manifest['included_sha256'],
                  temperature_C=27, branches=records,
                  method='Exact integral of linear-interpolated saved current for mean/RMS; interpolate window boundaries only. Absolute peak is sampled, not a proven continuous maximum.',
                  limitations=['Nominal compact28us fixture only, not worst-case PVT/mismatch/activity or startup sequence.',
                               'Core-feed total does not establish distribution among multiple accesses, internal stacks, or shared returns.',
                               'Ideal oscillator and RTL outputs omit real switching power; fitted IO pads are not included as real-pad evidence.',
                               'No applicable pulse/lifetime/125C EM rule or current-sharing model inferred. No implementation margin pass.'])
    (args.output/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(records, indent=2))


if __name__ == '__main__':
    main()
