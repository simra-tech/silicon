# P1_COMPARATOR — clocked CML latch

HBT CML latch with a CMOS output buffer and a 10-bit offset trim DAC. Samples
the amplified noise and produces a rail-to-rail digital bit.

## The block was rebuilt, and the table below predates the rebuild

Everything in *Measured* was taken on a hand-written netlist that did not
correspond to the schematic — 27 device lines against a 6-device drawing with 24
unnamed nets, with ideal resistors and an ideal current source. That netlist has
been replaced by a schematic-derived one: **42 instances**, all PDK devices, all
nets named, exported by xschem and audited for shorts, undriven outputs, orphan
nets and floating bases.

Rebuilding it cost the block its function for a while. On the rebuilt netlist the
comparator at first did not respond to its input at all; then it resolved
correctly with the clock *held still* but toggled at the clock rate on one input
polarity once actually clocked. Both are now fixed, and the numbers below in
*Measured* have **not** been re-taken on the rebuilt block. Treat this section as
the current state of the block and that one as history.

## Clocked at 5 GS/s, and it holds on both polarities

`run/clocked-both-polarities/` — two runs of one deck, differing only in which
input source is higher.

| | end of latch phase (900 ps) | end of track phase (1000 ps) | over two full periods |
| --- | --- | --- | --- |
| **+10 mV** → `PBIT_RAW` | 1.20001 V | 1.19999 V | 1.19992 … 1.20008 V |
| **+10 mV** → `PBIT_OUT` | −0.9 µV | +0.4 µV | −13.8 … +7.7 µV |
| **−10 mV** → `PBIT_RAW` | −13.0 µV | +6.9 µV | −57 … +84 µV |
| **−10 mV** → `PBIT_OUT` | 1.20000 V | 1.20000 V | 1.19998 … 1.20002 V |

Three things are in that table at once. The outputs are **complementary** and they
**exchange when the input flips**, so the block is deciding rather than stuck.
Each output is the **same at both clock phases** to within 20 µV, so there is no
phase-dependent offset left. And nothing moves more than 0.16 mV across two
periods, so there is no toggling.

The flip is the part that carries the weight. A comparator whose output is welded
to one rail also reports zero toggling on the polarity that was failing; only
running the other polarity separates a fix from a clamp.

## The output no longer overshoots its own rail

It used to reach **1.286 V on a 1.2 V supply** — 86 mV of overshoot into the gate
oxide of whatever follows. Two `cap_cmim` capacitors, 5 × 5 µm, went onto the CML
load nodes `cml_out_p` / `cml_out_n`; at this process's typical 1.5 fF/µm² area
density plus 40 aF/µm of perimeter that is **38.3 fF** each.

The highest voltage now reached on either output node, anywhere in a 400 ps window
spanning two complete clock periods, is **1.20008 V**. 0.08 mV above the rail,
against 86 mV before.

## What changed in the circuit

| | before | after |
| --- | --- | --- |
| emitter-follower → CMOS gate divider | 10 kΩ / 5 kΩ, ratio 0.333 | 5.79 kΩ / 3.84 kΩ (`rppd` 22 µm / 14.5 µm at w = 1 µm), ratio **0.399** |
| CML load node damping | none | 2 × 38.3 fF `cap_cmim` |

The divider ratio sets where the CML swing lands relative to the CMOS inverter
trip point, measured at 0.600 V on this 1.2 V supply. Raising it from 0.333 to
0.399 moves the quiescent gate voltage up, and that is what stopped the two clock
phases resolving to opposite sides of the trip point.

Both resistor values include the `rppd` model's contact end resistance, which adds
70 Ω·µm/w on top of Rspec·l/w — see `../noise-generator/layout/rppd-end-resistance/`.

## Still open on this block

| | |
| --- | --- |
| Clock kickback | The clock injects a differential disturbance into the input pair on every edge. Peak during the edge is 94.9 mV; by the sampling instant it has decayed to **0.63 mV**, which is what sets the error. That is ≈0.80% of bit probability against a 1% budget. It recurs identically on every edge, so the trim DAC — which resolves 39 µV, 15× finer — **cannot remove it**. The fix has to be edge rate, clocked-pair sizing, or a dummy switch. |
| Input-referred noise | A figure of 247.69 µV_rms exists but has no committed deck or log, so it is not published here. |
| Bit statistics from a real bitstream | Not run. |

## Measured on the superseded netlist

| Quantity | Value | How |
| --- | --- | --- |
| Sampling rate | **5.00 GS/s** | 8 rising edges over 1600 ps, transient |
| Decisions correct | **8 / 8** | every clock edge checked, not sampled |
| Digital output | 0 → 1.2 V rail to rail | `v(pbit_raw)` |
| Smallest resolved input | 3.02 mV | at a sampling edge |
| Untrimmed offset σ | 6.46 mV | 200-sample mismatch Monte Carlo |
| Trimmed residual, worst of 200 | 38.8 µV | same run |

## Trim is for accuracy, not survival

This is a correction to an earlier claim of ours. Offset does **not** stop the
comparator working:

| V_OS | P(bit = 1) at 36.4 mV noise | |
| --- | --- | --- |
| 6.46 mV (1σ) | 0.570 | skewed |
| 20.4 mV (worst of 200) | **0.712** | skewed |
| ~85 mV (≈13σ) | >0.99 | genuinely stuck |

No die in the distribution is close to stuck. Untrimmed parts are working p-bits
with a bias that varies from roughly 0.34 to 0.71 die to die — useless for a
machine that tunes probabilities, but not a functional failure. **The trim buys
probability accuracy and die-to-die uniformity, not yield.**

We previously described untrimmable dies as "stuck, outputting a constant". That
was wrong, and it is corrected here rather than quietly dropped.

## Not run

| Check | State |
| --- | --- |
| P(bit=1) counted from transient bits | **Not run.** The distribution above is **analytically derived** from the Monte Carlo V_OS distribution through the Gaussian CDF Φ(V_OS/σ_noise). It assumes Gaussian noise and no comparator non-ideality other than offset. |
| Bit autocorrelation, NIST / SP800-90B | **Not run.** No long transient bitstream exists. |
| Metastability, aperture window | **Not run.** |
| Layout, extraction, silicon | **Not done.** |

`run/tb_stuck_die_demo.spice` forces a −20.4 mV offset and reduces the input to
10 mV to make sticking visible. That is a demonstration of the mechanism at
reduced signal, **not** a prediction about this design at its real 36.4 mV.
