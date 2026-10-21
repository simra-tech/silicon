#!/usr/bin/env python3
"""T2 2026-10-21 (first-conversion fix test): write sim/r5/r1_adc_timing_r5_<base>_pre<W>.inc from an existing
revision-5 timing include. The encoder track signals trkX0 get one hold pulse (track low) of width W after t = 0,
then the original timing (track high, first sampling edge at T0). This is the r1_ctrl-side start-up sequence under
test: after ADC enable, one hold phase charges the bootstrap capacitor of the in0 sampling switch, then >= 250 ns
track before the first sampling edge. The netlist is not changed.
Pulse: falling edge at 106 ns (3.18 T, off the clk30 grid), rising edge W later, 2 ns edges (as the frame timing).
Implementation: trkX0 = trkX0_orig * (1 - pre) (B source); trkX0_orig is the unchanged PULSE / PWL line.
usage: gen_timing_pre5.py <base inc> <W in ns> [<W> ...]"""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
base = sys.argv[1]
src = open(os.path.join(HERE, base)).read().splitlines()
for w in sys.argv[2:]:
    W = float(w) * 1e-9
    out = ["* %s with a start-up hold pulse on trka0/trkb0: %.1f ns from 106 ns (gen_timing_pre5.py, T2 2026-10-21)" % (base, W * 1e9)]
    for l in src:
        f = l.split()
        if f and f[0] in ("Vtrka0", "Vtrkb0"):
            ch = f[0][4]
            vdd = [x for x in src if x.startswith("Vclk30")][0].split("(")[1].split()[1]
            out.append(l.replace("Vtrk%s0 trk%s0 " % (ch, ch), "Vtrk%s0o trk%s0o " % (ch, ch), 1))
            out.append("Vpre%s pre%s 0 PWL(0 0 106n 0 108n 1 %.4gn 1 %.4gn 0)" % (ch, ch, 108 + W * 1e9, 110 + W * 1e9))
            out.append("Btrk%s0 trk%s0 0 V=v(trk%s0o)*(1-v(pre%s))" % (ch, ch, ch, ch))
            continue
        out.append(l)
    fn = base.replace(".inc", "_pre%d.inc" % int(round(W * 1e9)))
    open(os.path.join(HERE, fn), "w").write("\n".join(out) + "\n")
    print("wrote", fn)
