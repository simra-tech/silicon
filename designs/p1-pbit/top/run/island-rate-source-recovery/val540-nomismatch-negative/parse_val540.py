#!/usr/bin/env python3
"""Parse the val540 ngspice log echo markers into per-code tables.

The deck emits:
  OFFSET <code> <base_mV>
  ANCHORLO <code> <vv_mV> <out>
  ANCHORHI <code> <vv_mV> <out>
  BAND    <code> <vv_mV> <out>

where out = v(pbit_raw_core)[last] (raw comparator output, ~0 = LOW, ~1.2 = HIGH).
"""
import sys, re, collections

def parse(path):
    codes = collections.OrderedDict()
    pat = re.compile(r'^(OFFSET|ANCHORLO|ANCHORHI|BAND)\s+(\d+)\s+(-?[\d.Ee+-]+)\s*(-?[\d.Ee+-]+)?\s*$')
    with open(path, 'r', errors='replace') as f:
        for line in f:
            m = pat.match(line.strip())
            if not m:
                continue
            kind, code, a = m.group(1), m.group(2), float(m.group(3))
            b = float(m.group(4)) if m.group(4) else None
            code = int(code)
            c = codes.setdefault(code, {'offset': None, 'anchorlo': None, 'anchorhi': None, 'band': []})
            if kind == 'OFFSET':
                c['offset'] = a
            elif kind == 'ANCHORLO':
                c['anchorlo'] = (a, b)
            elif kind == 'ANCHORHI':
                c['anchorhi'] = (a, b)
            elif kind == 'BAND':
                c['band'].append((a, b))
    return codes

def island_extent(band, thresh=0.6):
    """Return list of (start_vv, end_vv, width_mV, npts) contiguous LOW (out<thresh) runs."""
    runs = []
    cur = None
    for vv, out in band:
        low = out is not None and out < thresh
        if low:
            if cur is None:
                cur = [vv, vv, 0]
            cur[1] = vv
            cur[2] += 1
        else:
            if cur is not None:
                runs.append((cur[0], cur[1], cur[1]-cur[0], cur[2]))
                cur = None
    if cur is not None:
        runs.append((cur[0], cur[1], cur[1]-cur[0], cur[2]))
    return runs

def main():
    path = sys.argv[1]
    codes = parse(path)
    for code in sorted(codes):
        c = codes[code]
        print(f'--- code {code} ---')
        print(f'  OFFSET(base) = {c["offset"]}')
        print(f'  ANCHORLO vv={c["anchorlo"][0]} out={c["anchorlo"][1]:.6g}' if c['anchorlo'] else '  ANCHORLO = None')
        print(f'  ANCHORHI vv={c["anchorhi"][0]} out={c["anchorhi"][1]:.6g}' if c['anchorhi'] else '  ANCHORHI = None')
        runs = island_extent(c['band'])
        # classify each band point
        lows = [(vv, out) for vv, out in c['band'] if out is not None and out < 0.6]
        highs = [(vv, out) for vv, out in c['band'] if out is not None and out >= 0.6]
        print(f'  BAND: {len(c["band"])} pts, LOW(<0.6)={len(lows)}, HIGH(>=0.6)={len(highs)}')
        for r in runs:
            print(f'  LOW-run: start={r[0]:.4f} end={r[1]:.4f} width={r[2]:.4f} mV ({r[3]} pts)')
        print(f'  BAND points:')
        for vv, out in c['band']:
            print(f'    {vv:+.4f} mV  {out:.6g}  {"LOW" if out is not None and out < 0.6 else "HIGH"}')

if __name__ == '__main__':
    main()
