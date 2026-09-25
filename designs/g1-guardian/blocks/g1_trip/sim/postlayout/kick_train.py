#!/usr/bin/env python3
"""Sample a tb_trip_kick_train.cir run at the strobe edges.

  python3 kick_train.py <run.log> [<run.log> ...]     (the .dat written by wrdata sits next to the .log)

For each run: DC values (op before the transient, clock low), then at every strobe edge of the
comparator under test (soft: cmp_clk rising, t = 20n + k*200n; hard: cmp_clk falling = cmp_clk_n
rising, t = 120n + k*200n; k = 0..20 or as many as the run holds, the value just before the edge) the errors
dvth = vth(t) - vth_DC and dicmp = icmp(t) - icmp_DC, and the effective threshold shift of that
comparator referred to icmp, shift = dvth - dicmp (positive: the path trips later). Referred to the
shunt: icmp = ISENSE/2 and ISENSE = 1 V + 20 Vshunt, so shift_shunt = shift/10. 1 LSB = VREF/530.
Worst = max |.| over k >= 1 (strobes after the first); steady state = mean over the last 5 strobes.
The node errors during a decision are dominated by the deciding comparator's own kick and are not an
input-referred quantity; the effective threshold is bracketed instead by the decisions at several
underdrives (run_kick_train.sh argument 8). The decision of each strobe is the comparator output 50 ns after the edge (> VDD/2 = high).
"""
import re
import sys
import numpy as np

LSB = 1.04 / 530


def one(log):
    txt = open(log).read()
    m = re.search(r'DC vth_soft= *([-0-9.e+]+) +vth_hard= *([-0-9.e+]+) +icmp= *([-0-9.e+]+)', txt)
    dc = dict(zip(('vth_soft', 'vth_hard', 'icmp'), map(float, m.groups())))
    d = np.loadtxt(log[:-4] + '.dat')
    t = d[:, 0]
    col = dict(vth_soft=d[:, 1], vth_hard=d[:, 3], icmp=d[:, 5], clk=d[:, 7], cmp_soft=d[:, 9], cmp_hard=d[:, 11])
    cond = 'soft' if log.endswith('_soft.log') else 'hard'
    ud = float(re.search(r'_ud([-0-9.]+)_', log).group(1)) if '_ud' in log else 1.0
    vdd = float(re.search(r'_([0-9.]+)V_', log).group(1))
    t0 = 20e-9 if cond == 'soft' else 120e-9
    te = np.array([t0 + k * 200e-9 for k in range(21) if t0 + k * 200e-9 + 50e-9 < t[-1]])
    vth = np.interp(te, t, col['vth_' + cond]) - dc['vth_' + cond]
    ic = np.interp(te, t, col['icmp']) - dc['icmp']
    sh = vth - ic
    q = np.interp(te + 50e-9, t, col['cmp_' + cond]) > vdd / 2
    # the other comparator's threshold node at the same edges (it also receives this comparator's kick)
    other = 'hard' if cond == 'soft' else 'soft'
    vo = np.interp(te, t, col['vth_' + other]) - dc['vth_' + other]
    r = {}
    for name, v in [('dvth_' + cond, vth), ('dicmp', ic), ('shift', sh), ('dvth_' + other, vo)]:
        w = v[1:][np.argmax(abs(v[1:]))]
        r[name] = (w * 1e3, v[-5:].mean() * 1e3)
    return cond, dc, r, int(q.sum()), te, vth, ic, ud


def main():
    for log in sys.argv[1:]:
        cond, dc, r, nhigh, te, vth, ic, ud = one(log)
        name = log.split('/')[-1][:-4]
        print('== %s  (DC vth_%s=%.5f V, icmp=%.5f V = DC threshold - %g LSB; %d strobes, %d decided high)'
              % (name, cond, dc['vth_' + cond], dc['icmp'], ud, len(te), nhigh))
        for k, (w, s) in r.items():
            extra = ''
            if k.startswith('shift'):
                extra = '  | shunt-referred worst %+.3f mV, steady %+.3f mV' % (w / 10, s / 10)
            print('  %-13s worst %+8.3f mV (%+6.2f LSB)  steady %+8.3f mV (%+6.2f LSB)%s'
                  % (k, w, w / 1e3 / LSB, s, s / 1e3 / LSB, extra))
        print('  per-strobe dvth/dicmp mV: ' + ' '.join('%.1f/%.1f' % (a * 1e3, b * 1e3) for a, b in zip(vth, ic)))


if __name__ == '__main__':
    main()
