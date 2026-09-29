#!/usr/bin/env python3
"""Timeline of a 3.3 V dropout run (item 4) from its full waves file: python3 analyze_drop.py <waves_*.txt> [--json OUT]

Reports, from the waves the runner writes (v(gate), tripped, trip_d, cmp_hard, vref, vdda, icmp, vth_hard, load current):
GATE and the latch state before, during and after the dip; the first rise of `tripped` and of `trip_d`; the time
GATE falls below 1 V; VREF at the end of the dip and when it is back within 1 % of its pre-dip value; the interval
in which icmp > vth_hard (hard comparator input overdriven) after the rail returns.
"""
import json
import sys


def load(path):
    with open(path) as f:
        head = f.readline().split()
        cols = {k: i for i, k in enumerate(head)}
        rows = [list(map(float, l.split())) for l in f if l.strip()]
    return cols, rows


def main():
    path = sys.argv[1]
    cols, rows = load(path)
    c = lambda name: cols[name]
    t = [r[0] for r in rows]
    g = [r[c('v(gate)')] for r in rows]
    tr = [r[c('v(xchip.i_core_tripped)')] for r in rows]
    td = [r[c('v(xchip.i_core_trip_d)')] for r in rows]
    vr = [r[c('v(xchip.i_core_vref)')] for r in rows]
    va = [r[c('v(vdda)')] for r in rows]
    ic = [r[c('v(xchip.xi_core_u_trip.icmp)')] for r in rows]
    vh = [r[c('v(xchip.xi_core_u_trip.vth_hard)')] for r in rows]
    il = [r[c('i(vim)')] for r in rows]
    en = [r[c('v(xchip.en_i)')] for r in rows]

    def first(pred, t0=0.0):
        for i, ti in enumerate(t):
            if ti >= t0 and pred(i):
                return ti
        return None

    def at(v, ts):
        for i, ti in enumerate(t):
            if ti >= ts:
                return v[i]
        return v[-1]

    def rng(v, a, b):
        s = [v[i] for i, ti in enumerate(t) if a <= ti <= b]
        return (min(s), max(s)) if s else (None, None)

    dip0 = first(lambda i: va[i] < 3.25, 1e-6)
    dip1 = first(lambda i: va[i] > 3.25, (dip0 or 0) + 0.5e-6) if dip0 else None
    vref0 = at(vr, dip0 - 0.1e-6) if dip0 else None
    out = dict(
        waves=path.rsplit('/', 1)[-1], t_end_us=t[-1] * 1e6,
        dip_start_us=dip0 and dip0 * 1e6, rail_back_us=dip1 and dip1 * 1e6,
        vdda_min=min(va), vref_before=vref0,
        vref_min=min(vr), vref_at_rail_back=dip1 and at(vr, dip1),
        vref_back_1pct_us=(lambda x: x and x * 1e6)(first(lambda i: abs(vr[i] - vref0) < 0.01 * vref0, dip1)) if dip1 else None,
        gate_before=dip0 and at(g, dip0 - 0.1e-6),
        gate_range_during_dip=dip0 and dip1 and rng(g, dip0, dip1),
        gate_at_rail_back=dip1 and at(g, dip1),
        gate_max_after_rail_back=dip1 and rng(g, dip1, t[-1])[1],
        t_gate_above_3V_after_back_us=(lambda x: x and x * 1e6)(first(lambda i: g[i] > 3.0, dip1)) if dip1 else None,
        t_tripped_rise_us=(lambda x: x and x * 1e6)(first(lambda i: tr[i] > 0.6, 1e-6)),
        t_trip_d_rise_us=(lambda x: x and x * 1e6)(first(lambda i: td[i] > 0.6, 1e-6)),
        t_gate_below_1V_after_back_us=(lambda x: x and x * 1e6)(first(lambda i: g[i] < 1.0, dip1)) if dip1 else None,
        t_icmp_over_vth_hard_after_back_us=(lambda x: x and x * 1e6)(first(lambda i: ic[i] > vh[i], dip1)) if dip1 else None,
        load_A_end=il[-1], en_i_min=min(en), tripped_end=tr[-1], gate_end=g[-1])
    txt = json.dumps(out, indent=1)
    print(txt)
    if '--json' in sys.argv:
        with open(sys.argv[sys.argv.index('--json') + 1], 'w') as f:
            f.write(txt + '\n')


if __name__ == '__main__':
    main()
