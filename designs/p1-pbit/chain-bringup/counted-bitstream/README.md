# P(bit=1) counted from a real bitstream — 0.472 ± 0.022

The first counted bit probability in this project. Every distribution published
before this one was **derived** — the Monte Carlo offset distribution pushed through
a Gaussian CDF, assuming Gaussian noise and no non-ideality but offset. This one is
ones and zeros out of a transient.

```
N = 500   ones = 236   zeros = 263   ambiguous = 1
P(bit=1) = 0.4720 +/- 0.0223 (1 sigma)
95% interval: 0.4282 .. 0.5158
```

**The interval contains 0.5.** At this sample size the bit is indistinguishable from
a fair coin, which is what an untrimmed p-bit with small residual offset should give.

Measured on the full chain — `p1_noise_amp` into `p1_comparator`, both exported from
their schematics, all PDK devices — with a seeded band-limited noise source at
σ = 3.0818 mV and a 5 GS/s clock.

## Why every earlier attempt counted zero

Three separate runs before this one reported **0 ones** — 0/190, 0/474. They were not
wrong about what they measured. They measured inside the settling transient.

The interstage coupling network is ~2 pF into ~50 kΩ: a time constant near **100 ns**.
While it charges, the amplifier's differential output carries a decaying offset that
reaches **+32 mV** at 2–20 ns — comparable to the noise itself — and that pins the
comparator. The offset is gone by 150 ns (see
[`../rectified-offset/`](../rectified-offset/), which retracts our own reading of it as
a circuit property).

This run samples from **200 ns onward**. Over 200 … 300 ns:

| | |
| --- | --- |
| amplifier output differential, RMS | **29.24 mV** |
| amplifier output differential, mean | **+0.477 mV** — consistent with zero |
| `PBIT_OUT` range | **−0.046 … 1.269 V** — full rail, both directions |
| `PBIT_OUT` time average | 0.5554 V, a 46.3% duty cycle |

The mean of +0.48 mV against 29 mV of noise is a bias contribution of
0.3989 × 0.48/29.2 = **0.7%**, which is inside the 1% budget on its own and is also
within the statistical resolution of this measurement.

## How the bit is sampled

The decision is taken at the track-to-latch transition, on multiples of 200 ps. The
regenerated bit is read **100 ps later**, in the middle of the following latch phase
where it is flat — reading at the transition itself catches the edge. `count_bits.py`
does this against the transient dump; one sample per clock period, no interpolation.

One sample of 500 fell between the thresholds (0.3 … 0.9 V) and is counted as
ambiguous rather than assigned. That is the honest treatment of a metastable
decision, and at 1 in 500 it does not move the result.

## What this does and does not establish

**Does:** the chain works end to end on PDK devices with real amplified thermal
noise; the comparator resolves a noise-driven input at 5 GS/s; the counted
probability is consistent with the predicted ~0.5.

**Does not:**

| | |
| --- | --- |
| Verify the 1% bias budget | **No.** N = 500 gives ±2.2% at 1σ. Resolving 1% needs N ≈ 2,500 for the standard error alone, and more to bound it. |
| Say anything about whiteness | **No.** No autocorrelation, no run-length test, nothing from SP800-90B. A biased-but-correlated stream would pass this check. |
| Cover process, voltage, temperature | **No.** One realisation, typical corner, 27 °C, nominal supplies. |
| Include parasitics | **No.** Schematic values throughout. |
| Establish the trim works | **No.** `TRIM_P` / `TRIM_N` are held at 1.440 V; no trim code was exercised. |

Also logged: `PBIT_OUT` reaches **1.269 V** on a 1.2 V supply — 69 mV of overshoot.
The comparator's own page reports 0.08 mV, measured with ideal sources through 120 Ω
standing in for the amplifier. Driven by the real amplifier it is **69 mV**, which is
the same lesson as
[`../../comparator/run/kickback-clocked-vs-frozen/`](../../comparator/run/kickback-clocked-vs-frozen/):
a number measured against a stand-in belongs to the stand-in.

## Reproducing

```
ngspice -b bitcount.cir          # writes bits.dat, ~150k rows
python3 count_bits.py bits.dat
```

`$PDK_ROOT` is the IHP SG13G2 PDK root. The noise source is 50,000 samples at 10 ps
from a seeded Gaussian generator, linearly interpolated — see
[`../noise-convergence/`](../noise-convergence/) for why a held-step source will not
integrate. The run is 300 ns at a 5 ps maximum timestep; the first 200 ns are
simulated and discarded, which is not waste but the price of the coupling constant.
