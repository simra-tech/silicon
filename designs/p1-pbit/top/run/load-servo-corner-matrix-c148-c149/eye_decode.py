#!/usr/bin/env python3
"""Offset-swept bit-error decode for pbit output raws — the standard of record since 2026-08-07.

Reports, per raw: the widest contiguous zero-error span of sampling offsets (the eye), all
zero-error spans, the minimum error count over the whole sweep, and the rig reference decode
(comparator differential, 0 V slice) which must be 0/64 or the run is void.

Never report an error count taken at a single sampling phase: a phase-quantized decoder turns
corner-dependent chain latency into phantom bit errors (see harness finding H-722 — the C148
27 C "failures"). Sweep bounds must cover at least latency_seconds/bit_period + 1 bits; a
minimum sitting at the sweep edge means the sweep is too short, not that the eye is closed.

Usage: eye_decode.py <file.raw> <bit_period_seconds> [n_bits=64] [settle_seconds=10e-9]
"""
import array
import sys

TX64 = '1111111000000100000110000101000111100100010110011101010011111010'


def load_raw(path):
    """ngspice binary raw -> (npoints, nvars, {name: index}, flat float64 array).
    Column extraction is a stride slice: a[idx[name]::nv]. Verify npoints against the
    expected point count from the deck's stop time and step before trusting any number
    (H-717: ngspice exits 0 after an aborted tran and .measure still returns values)."""
    f = open(path, 'rb')
    header = b''
    while True:
        line = f.readline()
        header += line
        if line.strip() == b'Binary:':
            break
    text = header.decode('latin1')
    nv = int([l for l in text.splitlines() if 'No. Variables' in l][0].split(':')[1])
    npt = int([l for l in text.splitlines() if 'No. Points' in l][0].split(':')[1])
    names = []
    in_vars = False
    for l in text.splitlines():
        if l.startswith('Variables:'):
            in_vars = True
            continue
        if in_vars and l.strip() and not l.startswith('Binary'):
            parts = l.split()
            if len(parts) >= 2 and parts[0].isdigit():
                names.append(parts[1])
    data = array.array('d')
    data.frombytes(f.read()[:nv * npt * 8])
    f.close()
    return npt, nv, {n: i for i, n in enumerate(names)}, data


def sample(t, y, tq):
    lo, hi = 0, len(t) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if t[mid] <= tq:
            lo = mid
        else:
            hi = mid
    frac = (tq - t[lo]) / (t[hi] - t[lo]) if t[hi] != t[lo] else 0.0
    return y[lo] + frac * (y[hi] - y[lo])


def errors_at_offset(t, y, threshold, offset_bits, bp, tx, settle):
    bits = ''.join('1' if sample(t, y, settle + (offset_bits + k) * bp) >= threshold else '0'
                   for k in range(len(tx)))
    return sum(1 for a, b in zip(bits, tx) if a != b)


def eye_spans(t, y, threshold, bp, tx, settle, step=0.05):
    """All contiguous zero-error offset spans within the simulated window."""
    max_offset = (t[-1] - settle) / bp - len(tx)
    offsets, counts = [], []
    x = step
    while x < max_offset - 1e-9:
        offsets.append(round(x, 4))
        counts.append(errors_at_offset(t, y, threshold, x, bp, tx, settle))
        x += step
    spans = []
    for x, e in zip(offsets, counts):
        if e == 0:
            if spans and abs(x - spans[-1][1] - step) < 1e-9:
                spans[-1][1] = x
            else:
                spans.append([x, x])
    widest = max(((b - a) for a, b in spans), default=-step) + step
    return spans, widest if spans else 0.0, min(counts), offsets[counts.index(min(counts))]


def main():
    path = sys.argv[1]
    bp = float(sys.argv[2])
    tx = TX64 if len(sys.argv) < 4 else TX64  # extend here for the 127-bit period
    settle = float(sys.argv[4]) if len(sys.argv) > 4 else 10e-9
    npt, nv, idx, a = load_raw(path)
    t = a[idx['time']::nv]
    out = a[idx['v(pbit_out)']::nv]
    cp = a[idx['v(xcomp.c_p)']::nv]
    cn = a[idx['v(xcomp.c_n)']::nv]
    dif = array.array('d', (x - y for x, y in zip(cp, cn)))
    rig_spans, rig_w, rig_min, _ = eye_spans(t, dif, 0.0, bp, tx, settle)
    spans, w, mn, mnx = eye_spans(t, out, 0.6, bp, tx, settle)
    print('points=%d  rig: min_errors=%d widest_zero=%.0f ps' % (npt, rig_min, rig_w * bp * 1e12))
    if rig_min != 0:
        print('RIG NONZERO — RUN IS VOID')
        return
    print('out: widest_zero=%.0f ps  min_errors=%d at offset %.2f  spans=%s' % (
        w * bp * 1e12, mn, mnx, [('%.2f-%.2f' % (a2, b2)) for a2, b2 in spans]))


if __name__ == '__main__':
    main()
