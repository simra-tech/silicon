# P1_COMPARATOR — clocked CML latch

HBT CML latch with a CMOS output buffer and a 10-bit offset trim DAC. Samples
the amplified noise and produces a rail-to-rail digital bit.

## Measured

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
